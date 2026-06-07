import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from services.scoring_service import score_site
from ui.header import render_header
from ui.score_panel import render_score_breakdown
from report import generate_report
import time
import streamlit.components.v1 as components
from persistence import load_history, save_to_history, clear_history
from benchmarks import get_category_context
import os

st.set_page_config(
    page_title="SiteScore — Retail Site Intelligence", page_icon="📍", layout="wide"
)

render_header()

# ── Mode selector ─────────────────────────────────────────
mode = st.radio(
    "Mode",
    ["Single Site", "Compare 3 Sites", "History"],
    horizontal=True,
    label_visibility="collapsed",
)

# ── Session state ─────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "compared" not in st.session_state:
    st.session_state.compared = None
if "search_address" not in st.session_state:
    st.session_state.search_address = ""

# Clear any stale error results from previous sessions
if st.session_state.result is not None:
    if (
        not isinstance(st.session_state.result, dict)
        or "scores" not in st.session_state.result
    ):
        st.session_state.result = None

if st.session_state.compared is not None:
    if not isinstance(st.session_state.compared, list):
        st.session_state.compared = None
    else:
        st.session_state.compared = [
            r
            for r in st.session_state.compared
            if isinstance(r, dict) and "scores" in r
        ]
        if not st.session_state.compared:
            st.session_state.compared = None

# ════════════════════════════════════════════════════════════
# SINGLE SITE MODE
# ════════════════════════════════════════════════════════════
if mode == "Single Site":

    GKEY = os.environ.get("GOOGLE_API_KEY", "")

    if "address" in st.query_params:
        st.session_state.search_address = st.query_params["address"]

    current_address = st.session_state.get("search_address", "")

    brand_type = st.selectbox(
        "Type",
        ["restaurant", "pharmacy", "supermarket", "bank", "school"],
        label_visibility="collapsed",
        key="single_type_v2",
    )

    search_html = f"""
    <style>
      * {{ box-sizing:border-box;margin:0;padding:0 }}
      body {{ background:transparent;overflow:visible }}
      .row {{ display:flex;gap:6px;align-items:center;position:relative;z-index:9999; }}
      #search-wrapper {{ flex:0 0 75%;position:relative; }}
      #pac-input {{
        width:100%;padding:10px 32px 10px 12px;font-size:13px;
        border:1px solid #1D9E75;border-radius:8px;background:#0d1f1a;
        color:white;outline:none;font-family:sans-serif;
      }}
      #pac-input::placeholder {{ color:#888; }}
      #clear-btn {{
        position:absolute;right:8px;top:50%;transform:translateY(-50%);
        background:none;border:none;color:#888;font-size:16px;
        cursor:pointer;display:none;line-height:1;
      }}
      #map-container {{
        margin-top:6px;height:260px;border-radius:8px;
        border:1px solid #333;display:none;position:relative;z-index:1;
      }}
      #map-div {{ height:100%;width:100%;border-radius:8px; }}
      #hint {{
        padding:6px;background:#0d1f1a;border-top:1px solid #333;
        font-size:10px;color:#9ecfc0;text-align:center;font-family:sans-serif;
      }}
      #status {{
        font-size:11px;color:#1D9E75;font-family:sans-serif;
        min-height:14px;margin-top:4px;
      }}
      .pac-container {{
        z-index:2147483647 !important;
        position:absolute !important;
        background:#0d1f1a !important;
        border:1px solid #1D9E75 !important;
        border-radius:6px !important;
        font-family:sans-serif !important;
        margin-top:2px !important;
        box-shadow:0 4px 20px rgba(0,0,0,0.6) !important;
      }}
      .pac-item {{
        color:#ccc !important;background:#0d1f1a !important;
        padding:8px 12px !important;font-size:13px !important;
        cursor:pointer !important;border-top:1px solid #1a3a2a !important;
      }}
      .pac-item:hover {{ background:#1a4a3a !important; }}
      .pac-item-query {{ color:white !important;font-size:13px !important; }}
      .pac-matched {{ color:#1D9E75 !important; }}
    </style>

    <div class='row'>
      <div id='search-wrapper'>
        <input id='pac-input' type='text'
          placeholder='Search location in Gujarat...'
          value='{current_address}' autocomplete='off'/>
        <button id='clear-btn' onclick='clearInput()'>×</button>
      </div>
      <button onclick='toggleMap()'
        style='flex:0 0 auto;background:#0A2E26;color:#9ecfc0;
               border:1px solid #1D9E75;padding:9px 10px;border-radius:8px;
               cursor:pointer;font-size:16px;line-height:1'
        title='Pick on map'>📍</button>
      <button onclick='scoreThisSite()'
        style='flex:0 0 auto;background:#E74C3C;color:white;border:none;
               padding:10px 14px;border-radius:8px;cursor:pointer;
               font-size:13px;font-weight:600;font-family:sans-serif;
               white-space:nowrap'>
        Score →
      </button>
    </div>

    <div id='map-container'>
      <div id='map-div'></div>
      <div id='hint'>Click map to select · Click 📍 to close</div>
    </div>

    <div id='status'></div>

    <script>
      let map, marker, autocomplete, geocoder;
      let mapVisible = false;
      const input  = document.getElementById('pac-input');
      const clrBtn = document.getElementById('clear-btn');
      const status = document.getElementById('status');

      input.addEventListener('input', function() {{
        clrBtn.style.display = this.value ? 'block' : 'none';
      }});
      if (input.value) clrBtn.style.display = 'block';

      // Expand iframe when suggestions appear so they aren't clipped
      const observer = new MutationObserver(function() {{
        const pac = document.querySelector('.pac-container');
        if (pac && pac.children.length > 0 &&
            pac.style.display !== 'none') {{
          window.frameElement.style.height =
            (52 + pac.offsetHeight + 10) + 'px';
        }} else if (!mapVisible) {{
          window.frameElement.style.height = '52px';
        }}
      }});
      observer.observe(document.body, {{
        childList: true, subtree: true,
        attributes: true, attributeFilter: ['style']
      }});

      // Also shrink back when input loses focus
      input.addEventListener('blur', function() {{
        setTimeout(function() {{
          if (!mapVisible) {{
            window.frameElement.style.height = '52px';
          }}
        }}, 200);
      }});

      function clearInput() {{
        input.value = '';
        clrBtn.style.display = 'none';
        status.textContent = '';
        if (marker) marker.setMap(null);
      }}

      function setAddress(addr) {{
        input.value = addr;
        clrBtn.style.display = 'block';
        status.textContent = '📍 ' + addr.substring(0,60) +
          (addr.length > 60 ? '...' : '');
        const url = new URL(window.parent.location.href);
        url.searchParams.set('address', addr);
        url.searchParams.delete('do_score');
        window.parent.history.replaceState({{}}, '', url);
        window.parent.postMessage({{ type:'streamlit:rerun' }}, '*');
      }}

      function scoreThisSite() {{
        const addr = input.value.trim();
        if (!addr) {{
          status.textContent = 'Please enter an address first.';
          status.style.color = '#E74C3C';
          return;
        }}
        status.textContent = 'Scoring...';
        const url = new URL(window.parent.location.href);
        url.searchParams.set('address', addr);
        url.searchParams.set('do_score', '1');
        window.parent.location.href = url.toString();
      }}

      function initMap() {{
        geocoder = new google.maps.Geocoder();
        autocomplete = new google.maps.places.Autocomplete(input, {{
          componentRestrictions: {{ country:'in' }},
          bounds: new google.maps.LatLngBounds(
            new google.maps.LatLng(20.1, 68.1),
            new google.maps.LatLng(24.7, 74.5)
          ),
          strictBounds: false,
          fields: ['formatted_address','geometry','name']
        }});
        autocomplete.addListener('place_changed', function() {{
          const place = autocomplete.getPlace();
          if (!place.geometry) return;
          const addr = place.formatted_address || place.name;
          setAddress(addr);
          if (map) {{
            map.setCenter(place.geometry.location);
            map.setZoom(16);
            placeMarker(place.geometry.location, addr);
          }}
        }});
        map = new google.maps.Map(document.getElementById('map-div'), {{
          center: {{ lat:23.0225, lng:72.5714 }},
          zoom: 12,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: false,
          styles: [
            {{ elementType:'geometry', stylers:[{{ color:'#1a2a1a' }}] }},
            {{ elementType:'labels.text.fill', stylers:[{{ color:'#9ecfc0' }}] }},
            {{ elementType:'labels.text.stroke', stylers:[{{ color:'#0d1f1a' }}] }},
            {{ featureType:'road', elementType:'geometry', stylers:[{{ color:'#2a4a2a' }}] }},
            {{ featureType:'water', elementType:'geometry', stylers:[{{ color:'#0d1f2a' }}] }}
          ]
        }});
        map.addListener('click', function(e) {{
          geocoder.geocode({{ location:e.latLng }}, function(results, s) {{
            const addr = (s === 'OK' && results[0])
              ? results[0].formatted_address
              : e.latLng.lat().toFixed(6) + ', ' +
                e.latLng.lng().toFixed(6) + ', Gujarat, India';
            placeMarker(e.latLng, addr);
            setAddress(addr);
          }});
        }});
      }}

      function placeMarker(position, addr) {{
        if (marker) marker.setMap(null);
        marker = new google.maps.Marker({{
          position: position, map: map, title: addr,
          icon: {{
            path: google.maps.SymbolPath.CIRCLE,
            scale: 10, fillColor: '#1D9E75', fillOpacity: 1,
            strokeColor: '#ffffff', strokeWeight: 2
          }}
        }});
      }}

      function toggleMap() {{
        const container = document.getElementById('map-container');
        mapVisible = !mapVisible;
        container.style.display = mapVisible ? 'block' : 'none';
        if (mapVisible) {{
          setTimeout(function() {{
            google.maps.event.trigger(map, 'resize');
          }}, 100);
          window.frameElement.style.height = '380px';
        }} else {{
          window.frameElement.style.height = '52px';
        }}
      }}
    </script>
    <script
      src="https://maps.googleapis.com/maps/api/js?key={GKEY}&libraries=places&callback=initMap"
      async defer></script>
    """

    components.html(search_html, height=52, scrolling=False)

    address = st.session_state.get("search_address", "")

    if address:
        st.markdown(
            f"<div style='font-size:12px;color:#1D9E75;margin-top:-8px;"
            f"margin-bottom:6px'>📍 {address}</div>",
            unsafe_allow_html=True,
        )

    # Only score when do_score param is set (Score button clicked)
    do_score = st.query_params.get("do_score") == "1"
    if do_score:
        try:
            st.query_params.pop("do_score")
        except Exception:
            pass
        if address.strip():
            with st.spinner("Analysing location — takes 20–30 seconds..."):
                result = score_site(address.strip(), brand_type)
            if not result:
                st.session_state.result = None
                st.error("Something went wrong. Please try again.")
            elif "error" in result:
                st.session_state.result = None
                st.error(result["error"])
            else:
                result["mode"] = "single"
                st.session_state.result = result
                save_to_history(result)
        else:
            st.warning("Please enter an address first.")

    if st.session_state.result and "error" not in st.session_state.result:
        result = st.session_state.result
        scores = result.get("scores", {})
        if not scores:
            st.error("Result data is incomplete. Please score again.")
            st.stop()
        render_score_breakdown(result, brand_type)


# ════════════════════════════════════════════════════════════
# COMPARE 3 SITES MODE
# ════════════════════════════════════════════════════════════
elif mode == "Compare 3 Sites":
    st.markdown("#### Enter 3 candidate sites to compare")

    col1, col2, col3 = st.columns(3)
    with col1:
        addr1 = st.text_input(
            "Site 1", placeholder="e.g. Bopal, Ahmedabad", key="addr1"
        )
    with col2:
        addr2 = st.text_input(
            "Site 2", placeholder="e.g. Prahlad Nagar, Ahmedabad", key="addr2"
        )
    with col3:
        addr3 = st.text_input(
            "Site 3", placeholder="e.g. Vastrapur, Ahmedabad", key="addr3"
        )

    brand_type_c = st.selectbox(
        "Brand type",
        ["restaurant", "pharmacy", "supermarket", "bank", "school"],
        key="compare_type",
    )

    if st.button("Compare All 3 Sites", type="primary", use_container_width=True):
        addresses = [a.strip() for a in [addr1, addr2, addr3] if a.strip()]
        if len(addresses) < 2:
            st.warning("Please enter at least 2 addresses.")
        else:
            results = []
            progress = st.progress(0, text="Scoring sites...")
            for i, addr in enumerate(addresses):
                with st.spinner(f"Scoring site {i+1} of {len(addresses)}..."):
                    r = score_site(addr, brand_type_c)
                    if r and "error" not in r:
                        results.append(r)
                    elif r and "error" in r:
                        st.warning(f"Skipped '{addr}': {r['error']}")
                    progress.progress(
                        (i + 1) / len(addresses),
                        text=f"Scored {i+1} of {len(addresses)}",
                    )
                    time.sleep(0.5)
            progress.empty()

            if results:
                results.sort(key=lambda x: x["total_score"], reverse=True)
                st.session_state.compared = results
                # Save each compared site to history
                for r in results:
                    r["mode"] = "compare"
                    save_to_history(r)
            else:
                st.error("Could not score any of those addresses.")

    if st.session_state.compared:
        results = st.session_state.compared
        rank_colors = ["#1D9E75", "#BA7517", "#C0392B"]
        rank_labels = ["BEST SITE", "2ND SITE", "3RD SITE"]
        rank_classes = ["rank-1", "rank-2", "rank-3"]
        rank_emoji = ["🥇", "🥈", "🥉"]

        st.markdown("---")
        st.markdown("### Ranking")

        # Podium cards
        cols = st.columns(len(results))
        for i, (r, col) in enumerate(zip(results, cols)):
            vc = rank_colors[i] if i < len(rank_colors) else "#888"
            with col:
                st.markdown(
                    f"""
                <div class='{rank_classes[i]}'>
                  <div class='rank-label' style='color:{vc}'>
                    {rank_emoji[i]} {rank_labels[i]}</div>
                  <div class='rank-score' style='color:{vc}'>
                    {r["total_score"]}</div>
                  <div style='font-size:13px;color:{vc};
                              font-weight:600;margin-top:2px'>
                    {r["verdict"].upper()} SITE</div>
                  <div class='rank-addr'>{r["address"][:45]}</div>
                </div>""",
                    unsafe_allow_html=True,
                )

        # Comparison bar chart
        st.markdown("### Score Breakdown Comparison")
        categories = [
            "Demand",
            "Footfall",
            "Competition",
            "Accessibility",
            "Catchment",
            "Spending Power",
        ]
        score_keys = [
            "demand",
            "footfall",
            "competition",
            "accessibility",
            "catchment",
            "spending_power",
        ]
        colors_list = ["#1D9E75", "#BA7517", "#C0392B", "#185FA5", "#8B5CF6"]

        fig = go.Figure()
        for i, r in enumerate(results):
            vals = [r["scores"][k] for k in score_keys]
            name = r["address"].split(",")[0]
            fig.add_trace(
                go.Bar(
                    name=name,
                    x=categories,
                    y=vals,
                    marker_color=rank_colors[i] if i < 3 else "#888",
                    text=[str(v) for v in vals],
                    textposition="outside",
                )
            )

        fig.update_layout(
            barmode="group",
            height=420,
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(range=[0, 115], gridcolor="#EEEEEE", title="Score (0-100)"),
            xaxis=dict(title=""),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Detailed score table — mobile friendly HTML table

        st.markdown("### Detailed Score Table")

        def score_color(s):
            return "#1D9E75" if s >= 65 else "#BA7517" if s >= 45 else "#C0392B"

        rows_html = ""
        for i, r in enumerate(results):
            vc = rank_colors[i] if i < 3 else "#888"
            name = r["address"].split(",")[0]
            rows_html += f"""
            <tr>
              <td style='padding:12px 14px;text-align:left;border-bottom:1px solid #222'>
                <span style='font-size:15px'>{rank_emoji[i]}</span>
                <span style='font-weight:600;color:white'> {name}</span>
              </td>
              <td style='padding:12px 10px;text-align:center;border-bottom:1px solid #222;
                        color:{score_color(r["scores"]["demand"])};font-weight:600'>
                {r["scores"]["demand"]}</td>
              <td style='padding:12px 10px;text-align:center;border-bottom:1px solid #222;
                        color:{score_color(r["scores"]["footfall"])};font-weight:600'>
                {r["scores"]["footfall"]}</td>
              <td style='padding:12px 10px;text-align:center;border-bottom:1px solid #222;
                        color:{score_color(r["scores"]["competition"])};font-weight:600'>
                {r["scores"]["competition"]}</td>
              <td style='padding:12px 10px;text-align:center;border-bottom:1px solid #222;
                        color:{score_color(r["scores"]["accessibility"])};font-weight:600'>
                {r["scores"]["accessibility"]}</td>
              <td style='padding:12px 10px;text-align:center;border-bottom:1px solid #222;
                        color:{score_color(r["scores"]["catchment"])};font-weight:600'>
                {r["scores"]["catchment"]}</td>
              <td style='padding:12px 10px;text-align:center;border-bottom:1px solid #222;
                        color:{vc};font-weight:700;font-size:17px'>
                {r["total_score"]}</td>
            </tr>"""

        table_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {{ margin:0; padding:0; background:transparent; }}
          .wrap {{ overflow-x:auto; -webkit-overflow-scrolling:touch;
                  border-radius:10px; border:1px solid #333; }}
          table {{ width:100%; border-collapse:collapse;
                  background:#111; font-size:13px;
                  white-space:nowrap; font-family:sans-serif; }}
          thead tr {{ background:#0A2E26; }}
          th {{ padding:12px 10px; text-align:center;
                color:#9ecfc0; font-size:11px; letter-spacing:0.5px;
                font-weight:600; }}
          th:first-child {{ text-align:left; padding-left:14px; }}
        </style>
        </head>
        <body>
          <div class="wrap">
            <table>
              <thead>
                <tr>
                  <th>ADDRESS</th>
                  <th>DEMAND</th>
                  <th>FOOTFALL</th>
                  <th>COMPETITION</th>
                  <th>ACCESS</th>
                  <th>CATCHMENT</th>
                  <th>TOTAL</th>
                </tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
          </div>
        </body>
        </html>
        """

        components.html(table_html, height=40 + len(results) * 56)

        # Multi-site map
        st.markdown("### All Sites on Map")
        center_lat = sum(r["lat"] for r in results) / len(results)
        center_lng = sum(r["lng"] for r in results) / len(results)
        m = folium.Map(
            location=[center_lat, center_lng], zoom_start=13, tiles="CartoDB positron"
        )

        map_colors = ["green", "orange", "red"]
        for i, r in enumerate(results):
            folium.CircleMarker(
                location=[r["lat"], r["lng"]],
                radius=16,
                color="#0A2E26",
                fill=True,
                fill_color=rank_colors[i],
                fill_opacity=0.9,
                popup=folium.Popup(
                    f"<b>#{i+1} {r['address']}</b>"
                    f"<br>Score: {r['total_score']}/100"
                    f"<br>{r['verdict']} Site",
                    max_width=240,
                ),
            ).add_to(m)
            folium.Circle(
                location=[r["lat"], r["lng"]],
                radius=500,
                color=rank_colors[i],
                fill=True,
                fill_color=rank_colors[i],
                fill_opacity=0.05,
                dash_array="6",
                weight=1.5,
            ).add_to(m)

        st_folium(m, width="100%", height=460, returned_objects=[])

        # Recommendation box
        best = results[0]
        st.markdown("### Recommendation")
        st.markdown(
            f"""
        <div style='background:#0A2E26;border-radius:10px;
                    padding:20px 24px;color:white'>
          <div style='font-size:11px;color:#9ecfc0;
                      letter-spacing:1px'>RECOMMENDED SITE</div>
          <div style='font-size:22px;font-weight:700;
                      color:#1D9E75;margin-top:6px'>
            {best["address"]}</div>
          <div style='font-size:14px;color:#9ecfc0;margin-top:8px'>
            Scored {best["total_score"]}/100 — highest across all
            {len(results)} candidate sites analysed.
            {"No risk flags detected." if
             best["scores"]["competition"] >= 30 and
             best["scores"]["demand"] >= 40
             else "Review risk flags before committing."}
          </div>
        </div>""",
            unsafe_allow_html=True,
        )

        # Export PDF for best site
        st.markdown("")
        with st.spinner("Preparing PDF report..."):
            path = "/tmp/best_site_report.pdf"
            generate_report(best, path)
            with open(path, "rb") as f:
                pdf_bytes = f.read()

        st.download_button(
            label="Download PDF Report for Best Site",
            data=pdf_bytes,
            file_name="best_site_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.caption(
            "SiteScore Analytics · Ahmedabad · " "OpenStreetMap + Google Places API"
        )

# ════════════════════════════════════════════════════════════
# HISTORY MODE
# ════════════════════════════════════════════════════════════
elif mode == "History":
    st.markdown("### Previously Scored Sites")

    history = load_history()

    if not history:
        st.markdown(
            """
        <div style='background:#111;border:1px solid #222;
                    border-radius:10px;padding:32px;text-align:center;
                    color:#888;margin-top:16px'>
          <div style='font-size:32px;margin-bottom:12px'>📋</div>
          <div style='font-size:14px'>No sites scored yet.</div>
          <div style='font-size:12px;margin-top:6px'>
            Switch to Single Site mode and score your first location.
          </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        # Summary stats
        avg_score = round(sum(h["total_score"] for h in history) / len(history), 1)
        strong = sum(1 for h in history if h["verdict"] == "Strong")
        moderate = sum(1 for h in history if h["verdict"] == "Moderate")
        weak = sum(1 for h in history if h["verdict"] == "Weak")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sites Scored", len(history))
        col2.metric("Average Score", avg_score)
        col3.metric("Strong Sites", strong)
        col4.metric("Weak Sites", weak)

        st.markdown("---")

        # Search/filter
        search = st.text_input(
            "Filter by address",
            placeholder="Type to filter...",
            label_visibility="collapsed",
        )

        filtered = (
            [h for h in history if search.lower() in h["address"].lower()]
            if search
            else history
        )

        if not filtered:
            st.warning("No results match your search.")
        else:
            for entry in filtered:
                vc = (
                    "#1D9E75"
                    if entry["verdict"] == "Strong"
                    else "#BA7517" if entry["verdict"] == "Moderate" else "#C0392B"
                )

                scores = entry["scores"]

                with st.expander(
                    f"{entry['verdict']} · {entry['total_score']}/100 · "
                    f"{entry['address'][:55]}"
                ):
                    col_info, col_scores = st.columns([2, 3])

                    with col_info:
                        mode_badge = (
                            "Single Site"
                            if entry.get("mode", "single") == "single"
                            else "Compare"
                        )
                        badge_color = (
                            "#185FA5" if mode_badge == "Single Site" else "#8B5CF6"
                        )

                        st.markdown(
                            f'<div style="display:inline-block;background:{badge_color};'
                            f"color:white;font-size:9px;font-weight:600;"
                            f"padding:3px 8px;border-radius:20px;"
                            f'margin-bottom:10px;letter-spacing:0.5px">'
                            f"{mode_badge.upper()}</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div style="margin-bottom:10px">'
                            f'<div style="font-size:11px;color:#888">SCORED ON</div>'
                            f"<div style=\"font-size:13px;color:white\">{entry['timestamp']}</div>"
                            f"</div>"
                            f'<div style="margin-bottom:10px">'
                            f'<div style="font-size:11px;color:#888">BRAND TYPE</div>'
                            f"<div style=\"font-size:13px;color:white;text-transform:capitalize\">{entry['brand_type']}</div>"
                            f"</div>"
                            f'<div style="margin-bottom:10px">'
                            f'<div style="font-size:11px;color:#888">LOCATION</div>'
                            f"<div style=\"font-size:12px;color:#9ecfc0\">{entry['lat']:.4f}N, {entry['lng']:.4f}E</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div style="background:#0A2E26;border-radius:8px;'
                            f'padding:14px;text-align:center">'
                            f"<div style=\"font-size:36px;font-weight:700;color:{vc}\">{entry['total_score']}</div>"
                            f'<div style="font-size:11px;color:#9ecfc0">out of 100</div>'
                            f'<div style="font-size:13px;font-weight:600;color:{vc};margin-top:4px">'
                            f"{entry['verdict'].upper()} SITE</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                    with col_scores:
                        st.markdown("**Score breakdown**")
                        for label, key in [
                            ("Demand", "demand"),
                            ("Footfall", "footfall"),
                            ("Competition", "competition"),
                            ("Accessibility", "accessibility"),
                            ("Catchment", "catchment"),
                            ("Spending Power", "spending_power"),
                        ]:
                            s = scores.get(key, 0)
                            col = (
                                "#1D9E75"
                                if s >= 65
                                else "#BA7517" if s >= 45 else "#C0392B"
                            )
                            bar = int(s)
                            st.markdown(
                                f'<div style="margin-bottom:8px">'
                                f'<div style="display:flex;justify-content:space-between;margin-bottom:3px">'
                                f'<span style="font-size:11px;color:#888">{label}</span>'
                                f'<span style="font-size:12px;font-weight:700;color:{col}">{s}</span>'
                                f"</div>"
                                f'<div style="background:#222;border-radius:3px;height:5px">'
                                f'<div style="width:{bar}%;background:{col};height:5px;border-radius:3px">'
                                f"</div></div></div>",
                                unsafe_allow_html=True,
                            )

                    # Re-score button
                    if st.button(
                        "Re-score this site", key=f"rescore_{entry['address'][:20]}"
                    ):
                        st.session_state.result = None
                        st.info(
                            f"Switch to Single Site mode and enter: "
                            f"{entry['address']}"
                        )

        st.markdown("---")
        if st.button("Clear All History", type="secondary"):
            clear_history()
            st.success("History cleared.")
            st.rerun()
