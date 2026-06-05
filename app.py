import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from scorer import score_site
from report import generate_report
import time
import io
import streamlit.components.v1 as components
from history import load_history, save_to_history, clear_history
from benchmarks import get_benchmark_stats, get_percentile, get_category_context
import os

st.set_page_config(
    page_title="SiteScore — Retail Site Intelligence",
    page_icon="📍",
    layout="wide"
)

st.markdown("""
<style>
  .site-header {
    background: #0A2E26; border-radius: 10px;
    padding: 20px 28px; margin-bottom: 24px;
  }
  .score-box {
    background: #0A2E26; border-radius: 12px;
    padding: 28px; text-align: center; color: white;
  }
  .metric-card {
    background: white; border-radius: 10px;
    padding: 16px; border: 1px solid #EEEEEE;
    text-align: center; margin-bottom: 10px;
  }
  .metric-val { font-size: 28px; font-weight: 700; }
  .metric-lbl { font-size: 11px; color: #888; margin-top: 2px; }
  .risk-box {
    background: #FFF8F0; border-left: 4px solid #BA7517;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    font-size: 13px; color: #555; margin-bottom: 8px;
  }
  .ok-box {
    background: #F0FAF6; border-left: 4px solid #1D9E75;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    font-size: 13px; color: #0A6E50; margin-bottom: 8px;
  }
  .rank-1 { background: #F0FAF6; border: 2px solid #1D9E75;
             border-radius: 10px; padding: 16px; margin-bottom: 10px; }
  .rank-2 { background: #FFFDF0; border: 2px solid #BA7517;
             border-radius: 10px; padding: 16px; margin-bottom: 10px; }
  .rank-3 { background: #FFF5F5; border: 2px solid #C0392B;
             border-radius: 10px; padding: 16px; margin-bottom: 10px; }
  .rank-label { font-size: 11px; font-weight: 700;
                letter-spacing: 1px; margin-bottom: 4px; }
  .rank-score { font-size: 36px; font-weight: 700; line-height: 1; }
  .rank-addr  { font-size: 11px; color: #666; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────
st.markdown("""
<div class='site-header'>
  <div style='color:#9ecfc0;font-size:11px;letter-spacing:2px'>
    RETAIL SITE INTELLIGENCE
  </div>
  <div style='color:white;font-size:24px;font-weight:700;margin-top:4px'>
    SiteScore
  </div>
  <div style='color:#9ecfc0;font-size:13px;margin-top:2px'>
    Score any retail location in Gujarat — instantly
  </div>
</div>
""", unsafe_allow_html=True)

# ── Mode selector ─────────────────────────────────────────
mode = st.radio(
    "Mode",
    ["Single Site", "Compare 3 Sites", "History"],
    horizontal=True,
    label_visibility="collapsed"
)

# ── Session state ─────────────────────────────────────────
if "result"   not in st.session_state: st.session_state.result   = None
if "compared" not in st.session_state: st.session_state.compared = None
if "search_address" not in st.session_state:
    st.session_state.search_address = ""

# Clear any stale error results from previous sessions
if st.session_state.result is not None:
    if not isinstance(st.session_state.result, dict) or \
       "scores" not in st.session_state.result:
        st.session_state.result = None

if st.session_state.compared is not None:
    if not isinstance(st.session_state.compared, list):
        st.session_state.compared = None
    else:
        st.session_state.compared = [
            r for r in st.session_state.compared
            if isinstance(r, dict) and "scores" in r
        ]
        if not st.session_state.compared:
            st.session_state.compared = None

# ════════════════════════════════════════════════════════════
# SINGLE SITE MODE
# ════════════════════════════════════════════════════════════
if mode == "Single Site":

    col_input, col_type = st.columns([3, 1])

    with col_type:
        brand_type = st.selectbox(
            "Type",
            ["restaurant","pharmacy","supermarket","bank","school"],
            label_visibility="collapsed",
            key="single_type"
        )

    with col_input:
        GKEY = os.environ.get("GOOGLE_API_KEY", "")

        # Read address from query params if set by the component
        if "address" in st.query_params:
            st.session_state.search_address = st.query_params["address"]

        current_address = st.session_state.get("search_address", "")

        search_html = f"""
        <style>
          * {{ box-sizing: border-box; margin: 0; padding: 0; }}
          body {{ background: transparent; }}

          #search-wrapper {{
            position: relative;
            width: 100%;
          }}

          #pac-input {{
            width: 100%;
            padding: 11px 40px 11px 14px;
            font-size: 14px;
            border: 1px solid #1D9E75;
            border-radius: 8px;
            background: #0d1f1a;
            color: white;
            outline: none;
            font-family: sans-serif;
          }}

          #pac-input::placeholder {{ color: #888; }}

          #clear-btn {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #888;
            font-size: 18px;
            cursor: pointer;
            display: none;
          }}

          #map-container {{
            margin-top: 8px;
            height: 260px;
            border-radius: 8px;
            border: 1px solid #333;
            display: none;
            position: relative;
          }}

          #map-div {{ height: 100%; width: 100%; border-radius: 8px; }}

          #map-toggle {{
            background: #0A2E26;
            color: #9ecfc0;
            border: 1px solid #1D9E75;
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 18px;
          }}

          #map-toggle:hover {{ background: #1a4a3a; }}

          #status {{
            margin-top: 6px;
            font-size: 11px;
            color: #1D9E75;
            font-family: sans-serif;
            min-height: 16px;
          }}
        </style>

        <div style='display:flex;gap:8px;align-items:center'>
          <div id='search-wrapper' style='flex:1;position:relative'>
            <input
              id='pac-input'
              type='text'
              placeholder='Search any location in Gujarat...'
              value='{current_address}'
              autocomplete='off'
            />
            <button id='clear-btn' onclick='clearInput()'>×</button>
          </div>
          <button id='map-toggle' onclick='toggleMap()'
            style='background:#0A2E26;color:#9ecfc0;
                   border:1px solid #1D9E75;padding:10px 12px;
                   border-radius:8px;cursor:pointer;font-size:18px;
                   white-space:nowrap;flex-shrink:0'>
            📍
          </button>
        </div>

        <div id='map-container'>
          <div id='map-div'></div>
          <div style='padding:8px;background:#0d1f1a;border-top:1px solid #333;
                      font-size:11px;color:#9ecfc0;text-align:center'>
            Click anywhere on map to select location · Click 📍 again to close
          </div>
        </div>

        <div id='status'></div>

        <script>
          let map, marker, autocomplete, mapVisible = false;
          const input = document.getElementById('pac-input');
          const clearBtn = document.getElementById('clear-btn');
          const status = document.getElementById('status');

          input.addEventListener('input', function() {{
            clearBtn.style.display = this.value ? 'block' : 'none';
          }});

          if (input.value) clearBtn.style.display = 'block';

          function clearInput() {{
            input.value = '';
            clearBtn.style.display = 'none';
            status.textContent = '';
            if (marker) marker.setMap(null);
          }}

          function setAddress(addr) {{
            input.value = addr;
            clearBtn.style.display = 'block';
            status.textContent = 'Ready — click Score This Site';

            // Send to Streamlit via query params
            const url = new URL(window.parent.location.href);
            url.searchParams.set('address', addr);
            window.parent.history.replaceState({{}}, '', url);

            // Trigger Streamlit rerun
            window.parent.postMessage({{
              type: 'streamlit:rerun'
            }}, '*');
          }}

          function initMap() {{
            // Autocomplete
            autocomplete = new google.maps.places.Autocomplete(input, {{
              componentRestrictions: {{ country: 'in' }},
              bounds: new google.maps.LatLngBounds(
                new google.maps.LatLng(20.1, 68.1),
                new google.maps.LatLng(24.7, 74.5)
              ),
              strictBounds: false,
              fields: ['formatted_address', 'geometry', 'name']
            }});

            autocomplete.addListener('place_changed', function() {{
              const place = autocomplete.getPlace();
              if (!place.geometry) return;

              const addr = place.formatted_address || place.name;
              setAddress(addr);

              // Pan map to selected place
              if (map) {{
                map.setCenter(place.geometry.location);
                map.setZoom(16);
                placeMarker(place.geometry.location,
                            place.geometry.location.lat(),
                            place.geometry.location.lng(),
                            addr);
              }}
            }});

            // Map
            map = new google.maps.Map(document.getElementById('map-div'), {{
              center: {{ lat: 23.0225, lng: 72.5714 }},
              zoom: 12,
              mapTypeControl: false,
              streetViewControl: false,
              fullscreenControl: false,
              styles: [
                {{ elementType: 'geometry',
                   stylers: [{{ color: '#1a2a1a' }}] }},
                {{ elementType: 'labels.text.fill',
                   stylers: [{{ color: '#9ecfc0' }}] }},
                {{ elementType: 'labels.text.stroke',
                   stylers: [{{ color: '#0d1f1a' }}] }},
                {{ featureType: 'road',
                   elementType: 'geometry',
                   stylers: [{{ color: '#2a4a2a' }}] }},
                {{ featureType: 'water',
                   elementType: 'geometry',
                   stylers: [{{ color: '#0d1f2a' }}] }}
              ]
            }});

            map.addListener('click', function(e) {{
              const lat = e.latLng.lat();
              const lng = e.latLng.lng();

              // Reverse geocode to get place name
              const geocoder = new google.maps.Geocoder();
              geocoder.geocode({{ location: e.latLng }}, function(results, s) {{
                let addr;
                if (s === 'OK' && results[0]) {{
                  addr = results[0].formatted_address;
                }} else {{
                  addr = lat.toFixed(6) + ', ' + lng.toFixed(6) +
                         ', Gujarat, India';
                }}
                placeMarker(e.latLng, lat, lng, addr);
                setAddress(addr);
              }});
            }});
          }}

          function placeMarker(position, lat, lng, addr) {{
            if (marker) marker.setMap(null);
            marker = new google.maps.Marker({{
              position: position,
              map: map,
              title: addr,
              icon: {{
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: '#1D9E75',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 2
              }}
            }});
          }}

          function toggleMap() {{
            const container = document.getElementById('map-container');
            const scoreRow  = document.getElementById('score-row');
            mapVisible = !mapVisible;
            container.style.display = mapVisible ? 'block' : 'none';
            if (mapVisible) {{
              setTimeout(function() {{
                google.maps.event.trigger(map, 'resize');
              }}, 100);
              window.frameElement.style.height = '400px';
            }} else {{
              window.frameElement.style.height = '52px';
            }}
          }}
        </script>

        <script
          src="https://maps.googleapis.com/maps/api/js?key={GKEY}&libraries=places&callback=initMap"
          async defer>
        </script>
        """

        components.html(search_html, height=52, scrolling=False)

    # Address comes from query params set by the component
    address = st.session_state.get("search_address", "")

    if address:
        st.markdown(
            f"<div style='font-size:12px;color:#1D9E75;margin-top:-8px;"
            f"margin-bottom:8px'>📍 {address}</div>",
            unsafe_allow_html=True
        )

    if st.button("Score This Site", type="primary", use_container_width=True):
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
        result   = st.session_state.result
        scores   = result.get("scores", {})
        if not scores:
            st.error("Result data is incomplete. Please score again.")
            st.stop()

        total    = result["total_score"]
        verdict  = result["verdict"]
        lat, lng = result["lat"], result["lng"]
        vc       = "#1D9E75" if verdict=="Strong" else \
                   "#BA7517" if verdict=="Moderate" else "#C0392B"

        benchmark  = get_category_context(total, brand_type)
        stats      = benchmark["stats"]
        percentile = benchmark["percentile"]
        bar_color  = "#1D9E75" if percentile >= 65 else \
                     "#BA7517" if percentile >= 40 else "#C0392B"

        st.markdown("---")

        # ── Row 1: Score summary bar ──────────────────────────
        st.markdown(f"""
        <div style='background:#0A2E26;border-radius:12px;
                    padding:20px 28px;margin-bottom:16px;
                    display:flex;align-items:center;
                    justify-content:space-between;flex-wrap:wrap;gap:16px'>
          <div>
            <div style='font-size:11px;color:#9ecfc0;
                        letter-spacing:1px;margin-bottom:4px'>SITE SCORE</div>
            <div style='font-size:52px;font-weight:700;
                        color:{vc};line-height:1'>{total}</div>
            <div style='font-size:12px;color:#9ecfc0;margin-top:2px'>
              out of 100</div>
          </div>
          <div style='text-align:center'>
            <div style='font-size:18px;font-weight:700;
                        color:{vc}'>{verdict.upper()} SITE</div>
            <div style='font-size:12px;color:#9ecfc0;margin-top:4px'>
              {result["address"][:60]}</div>
          </div>
          <div style='text-align:right;min-width:160px'>
            <div style='font-size:11px;color:#9ecfc0;margin-bottom:6px'>
              BETTER THAN {percentile}% OF SIMILAR SITES
            </div>
            <div style='background:#1a4a3a;border-radius:4px;height:8px'>
              <div style='width:{min(percentile,100)}%;
                          background:{bar_color};
                          height:8px;border-radius:4px'></div>
            </div>
            <div style='display:flex;justify-content:space-between;
                        font-size:10px;color:#9ecfc0;margin-top:4px'>
              <span>Avg {stats["average"]}</span>
              <span>Top {stats["top_sites_avg"]}</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Row 2: 6 score pills ──────────────────────────────
        score_items = [
            ("Demand",         scores["demand"]),
            ("Footfall",       scores["footfall"]),
            ("Competition",    scores["competition"]),
            ("Accessibility",  scores["accessibility"]),
            ("Catchment",      scores["catchment"]),
            ("Spending Power", scores["spending_power"]),
        ]
        pills = ""
        for label, s in score_items:
            col = "#1D9E75" if s>=65 else "#BA7517" if s>=45 else "#C0392B"
            pills += f"""
            <div style='flex:1;min-width:80px;background:#111;
                        border:1px solid #222;border-radius:8px;
                        padding:10px 8px;text-align:center'>
              <div style='font-size:20px;font-weight:700;color:{col}'>{s}</div>
              <div style='font-size:10px;color:#888;margin-top:2px'>{label}</div>
            </div>"""

        components.html(f"""
        <div style='display:flex;gap:8px;flex-wrap:wrap;
                    font-family:sans-serif'>
          {pills}
        </div>
        """, height=80)

        # ── Radar chart ───────────────────────────────────────
        st.markdown("### Score Breakdown")
        col_left, col_chart, col_right = st.columns([1, 6, 1])
        with col_chart:
            cats = ["Demand","Footfall","Competition",
                    "Accessibility","Catchment","Spending Power"]
            vals = [scores["demand"], scores["footfall"],
                    scores["competition"], scores["accessibility"],
                    scores["catchment"], scores["spending_power"]]
            fig = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill="toself", fillcolor="rgba(29,158,117,0.15)",
                line=dict(color="#1D9E75", width=2),
                marker=dict(color="#1D9E75", size=7),
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor="#0d1f1a",
                    radialaxis=dict(visible=True, range=[0,100],
                                    tickfont=dict(size=9, color="#888"),
                                    gridcolor="#2a2a2a"),
                    angularaxis=dict(tickfont=dict(size=12, color="#ccc"))
                ),
                showlegend=False, height=380,
                margin=dict(l=60, r=60, t=40, b=40),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── Map ───────────────────────────────────────────────
        st.markdown("### Location Map")
        col_left, col_map, col_right = st.columns([1, 10, 1])
        with col_map:
            m = folium.Map(location=[lat, lng], zoom_start=15,
                           tiles="CartoDB positron")
            folium.CircleMarker(
                location=[lat, lng], radius=14,
                color="#0A2E26", fill=True,
                fill_color=vc, fill_opacity=0.9,
                popup=folium.Popup(
                    f"<b>{result['address']}</b><br>Score: {total}/100",
                    max_width=220)
            ).add_to(m)
            folium.Circle(location=[lat,lng], radius=500,
                color="#1D9E75", fill=True, fill_color="#1D9E75",
                fill_opacity=0.05, dash_array="6", weight=1.5,
                tooltip="500m radius").add_to(m)
            folium.Circle(location=[lat,lng], radius=1000,
                color="#BA7517", fill=False,
                dash_array="4", weight=1,
                tooltip="1km radius").add_to(m)
            st_folium(m, width="100%", height=400, returned_objects=[])

        # ── Risk + explainability ─────────────────────────────
        st.markdown("### Analysis Details")
        col_risk, col_explain = st.columns(2)

        with col_risk:
            st.markdown("**Risk Assessment**")
            risks = []
            if scores["competition"]   < 30: risks.append("High competitor density within 500m")
            if scores["demand"]        < 40: risks.append("Low residential population density")
            if scores["footfall"]      < 40: risks.append("Few anchor stores within 500m")
            if scores["accessibility"] < 40: risks.append("Limited road connectivity")
            if risks:
                for r in risks:
                    st.markdown(f"""
                    <div style='background:#1a0e0e;border-left:3px solid #C0392B;
                                padding:8px 12px;border-radius:0 6px 6px 0;
                                font-size:12px;color:#ccc;margin-bottom:6px'>
                      ! {r}</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background:#0d1f1a;border-left:3px solid #1D9E75;
                            padding:8px 12px;border-radius:0 6px 6px 0;
                            font-size:12px;color:#9ecfc0'>
                  No significant risk flags at this location</div>""",
                unsafe_allow_html=True)

        with col_explain:
            st.markdown("**What we found**")
            raw = result.get("raw", {})

            def mini_row(label, value, note):
                st.markdown(f"""
                <div style='border-bottom:1px solid #1a1a1a;
                            padding:7px 0;margin-bottom:2px'>
                  <div style='display:flex;justify-content:space-between'>
                    <span style='font-size:11px;color:#888'>{label}</span>
                    <span style='font-size:13px;font-weight:700;
                                 color:white'>{value}</span>
                  </div>
                  <div style='font-size:10px;color:#555;
                              margin-top:1px'>{note}</div>
                </div>""", unsafe_allow_html=True)

            raw    = result.get("raw", {})
        method = raw.get("demand_method", "osm_buildings")

        if method == "census_2011":
            mini_row(
                "Est. population within 1km",
                f"{raw.get('demand_population',0):,}",
                f"Census 2011 ward data · "
                f"{raw.get('demand_households',0):,} households"
            )
            wards = raw.get("demand_wards", [])
            if wards:
                ward_names = " · ".join(
                    w["name"] for w in wards[:3])
                mini_row(
                    "Contributing wards",
                    str(len(wards)),
                    ward_names
                )
        else:
            mini_row(
                "Residential buildings within 1km",
                f"{raw.get('demand_buildings',0):,}",
                "OpenStreetMap buildings (Census data unavailable)"
            )
            mini_row("Footfall anchors",
                     str(sum(raw.get('footfall_anchors',{}).values())
                         if raw.get('footfall_anchors') else 0),
                     "supermarkets, hospitals, schools within 500m")
            mini_row("Competitors found",
                     str(raw.get('competitor_count', 0)),
                     "weighted by review count + rating")
            mini_row("Road intersections",
                     str(raw.get('intersections', 0)),
                     "within 300m drive network")
            mini_row("Commercial places",
                     str(raw.get('catchment_places', 0)),
                     "shops, cafes within 1km")
            spending = raw.get("spending_data", {})
            avg_p    = spending.get("avg_price_level")
            mini_row("Avg price level",
                     f"{avg_p}/4.0" if avg_p else "N/A",
                     f"{spending.get('sample_size',0)} places sampled")

        # ── Competitors ───────────────────────────────────────
        if result.get("competitor_details"):
            st.markdown("### Nearby Competitors")
            competitors = sorted(
                result["competitor_details"],
                key=lambda x: x["strength"], reverse=True)[:8]

            col_left, col_comp, col_right = st.columns([1, 10, 1])
            with col_comp:
                for comp in competitors:
                    strength   = comp["strength"]
                    bar_color2 = "#C0392B" if strength>0.6 else \
                                 "#BA7517" if strength>0.3 else "#1D9E75"
                    bar_w      = int(strength * 100)
                    stars      = "★"*int(round(comp["rating"])) + \
                                 "☆"*(5-int(round(comp["rating"])))
                    rev_label  = f"{comp['reviews']:,} reviews" \
                                 if comp["reviews"] > 0 else "No reviews"
                    st.markdown(f"""
                    <div style='background:#111;border:1px solid #222;
                                border-radius:8px;padding:10px 14px;
                                margin-bottom:6px'>
                      <div style='display:flex;justify-content:space-between;
                                  align-items:center;margin-bottom:6px'>
                        <span style='font-size:13px;font-weight:600;
                                     color:white'>{comp["name"]}</span>
                        <span style='font-size:11px;color:#888'>
                          {stars} &nbsp;{rev_label}</span>
                      </div>
                      <div style='display:flex;align-items:center;gap:10px'>
                        <div style='flex:1;background:#333;
                                    border-radius:4px;height:6px'>
                          <div style='width:{bar_w}%;background:{bar_color2};
                                      height:6px;border-radius:4px'></div>
                        </div>
                        <span style='font-size:11px;color:{bar_color2};
                                     min-width:80px;text-align:right'>
                          {"Strong" if strength>0.6 else
                           "Moderate" if strength>0.3 else "Weak"}
                          competitor</span>
                      </div>
                    </div>""", unsafe_allow_html=True)

        # ── PDF download ──────────────────────────────────────
        st.markdown("---")
        with st.spinner("Preparing PDF report..."):
            path = f"/tmp/{result['address'][:20].replace(' ','_')}_report.pdf"
            generate_report(result, path)
            with open(path, "rb") as f:
                pdf_bytes = f.read()
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name="sitescore_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.caption(
            "SiteScore Analytics · Gujarat · "
            "OpenStreetMap + Google Places API")


# ════════════════════════════════════════════════════════════
# COMPARE 3 SITES MODE
# ════════════════════════════════════════════════════════════
elif mode == "Compare 3 Sites":
    st.markdown("#### Enter 3 candidate sites to compare")

    col1, col2, col3 = st.columns(3)
    with col1:
        addr1 = st.text_input("Site 1", placeholder="e.g. Bopal, Ahmedabad",
                               key="addr1")
    with col2:
        addr2 = st.text_input("Site 2", placeholder="e.g. Prahlad Nagar, Ahmedabad",
                               key="addr2")
    with col3:
        addr3 = st.text_input("Site 3", placeholder="e.g. Vastrapur, Ahmedabad",
                               key="addr3")

    brand_type_c = st.selectbox(
        "Brand type",
        ["restaurant","pharmacy","supermarket","bank","school"],
        key="compare_type"
    )

    if st.button("Compare All 3 Sites", type="primary",
                 use_container_width=True):
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
                    progress.progress((i+1)/len(addresses),
                                      text=f"Scored {i+1} of {len(addresses)}")
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
        rank_colors  = ["#1D9E75", "#BA7517", "#C0392B"]
        rank_labels  = ["BEST SITE", "2ND SITE", "3RD SITE"]
        rank_classes = ["rank-1", "rank-2", "rank-3"]
        rank_emoji   = ["🥇", "🥈", "🥉"]

        st.markdown("---")
        st.markdown("### Ranking")

        # Podium cards
        cols = st.columns(len(results))
        for i, (r, col) in enumerate(zip(results, cols)):
            vc = rank_colors[i] if i < len(rank_colors) else "#888"
            with col:
                st.markdown(f"""
                <div class='{rank_classes[i]}'>
                  <div class='rank-label' style='color:{vc}'>
                    {rank_emoji[i]} {rank_labels[i]}</div>
                  <div class='rank-score' style='color:{vc}'>
                    {r["total_score"]}</div>
                  <div style='font-size:13px;color:{vc};
                              font-weight:600;margin-top:2px'>
                    {r["verdict"].upper()} SITE</div>
                  <div class='rank-addr'>{r["address"][:45]}</div>
                </div>""", unsafe_allow_html=True)

        # Comparison bar chart
        st.markdown("### Score Breakdown Comparison")
        categories = ["Demand","Footfall","Competition",
              "Accessibility","Catchment","Spending Power"]
        score_keys = ["demand","footfall","competition",
              "accessibility","catchment","spending_power"]
        colors_list  = ["#1D9E75","#BA7517","#C0392B",
                        "#185FA5","#8B5CF6"]

        fig = go.Figure()
        for i, r in enumerate(results):
            vals = [r["scores"][k] for k in score_keys]
            name = r["address"].split(",")[0]
            fig.add_trace(go.Bar(
                name=name,
                x=categories,
                y=vals,
                marker_color=rank_colors[i] if i < 3 else "#888",
                text=[str(v) for v in vals],
                textposition="outside",
            ))

        fig.update_layout(
            barmode="group",
            height=420,
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(range=[0,115], gridcolor="#EEEEEE",
                       title="Score (0-100)"),
            xaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom",
                        y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Detailed score table — mobile friendly HTML table

        st.markdown("### Detailed Score Table")

        def score_color(s):
            return "#1D9E75" if s >= 65 else "#BA7517" if s >= 45 else "#C0392B"

        rows_html = ""
        for i, r in enumerate(results):
            vc   = rank_colors[i] if i < 3 else "#888"
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
        m = folium.Map(location=[center_lat, center_lng],
                       zoom_start=13, tiles="CartoDB positron")

        map_colors = ["green","orange","red"]
        for i, r in enumerate(results):
            folium.CircleMarker(
                location=[r["lat"], r["lng"]],
                radius=16,
                color="#0A2E26", fill=True,
                fill_color=rank_colors[i],
                fill_opacity=0.9,
                popup=folium.Popup(
                    f"<b>#{i+1} {r['address']}</b>"
                    f"<br>Score: {r['total_score']}/100"
                    f"<br>{r['verdict']} Site",
                    max_width=240)
            ).add_to(m)
            folium.Circle(
                location=[r["lat"], r["lng"]], radius=500,
                color=rank_colors[i], fill=True,
                fill_color=rank_colors[i], fill_opacity=0.05,
                dash_array="6", weight=1.5
            ).add_to(m)

        st_folium(m, width="100%", height=460, returned_objects=[])

        # Recommendation box
        best = results[0]
        st.markdown("### Recommendation")
        st.markdown(f"""
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
        </div>""", unsafe_allow_html=True)

        # Export PDF for best site
        st.markdown("")
        with st.spinner("Preparing PDF report..."):
            path = f"/tmp/best_site_report.pdf"
            generate_report(best, path)
            with open(path, "rb") as f:
                pdf_bytes = f.read()

        st.download_button(
            label="Download PDF Report for Best Site",
            data=pdf_bytes,
            file_name="best_site_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.caption(
            "SiteScore Analytics · Ahmedabad · "
            "OpenStreetMap + Google Places API")
        
# ════════════════════════════════════════════════════════════
# HISTORY MODE
# ════════════════════════════════════════════════════════════
elif mode == "History":
    st.markdown("### Previously Scored Sites")

    history = load_history()

    if not history:
        st.markdown("""
        <div style='background:#111;border:1px solid #222;
                    border-radius:10px;padding:32px;text-align:center;
                    color:#888;margin-top:16px'>
          <div style='font-size:32px;margin-bottom:12px'>📋</div>
          <div style='font-size:14px'>No sites scored yet.</div>
          <div style='font-size:12px;margin-top:6px'>
            Switch to Single Site mode and score your first location.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary stats
        avg_score = round(
            sum(h["total_score"] for h in history) / len(history), 1)
        strong    = sum(1 for h in history if h["verdict"] == "Strong")
        moderate  = sum(1 for h in history if h["verdict"] == "Moderate")
        weak      = sum(1 for h in history if h["verdict"] == "Weak")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Sites Scored",   len(history))
        col2.metric("Average Score",  avg_score)
        col3.metric("Strong Sites",   strong)
        col4.metric("Weak Sites",     weak)

        st.markdown("---")

        # Search/filter
        search = st.text_input(
            "Filter by address",
            placeholder="Type to filter...",
            label_visibility="collapsed"
        )

        filtered = [
            h for h in history
            if search.lower() in h["address"].lower()
        ] if search else history

        if not filtered:
            st.warning("No results match your search.")
        else:
            for entry in filtered:
                vc = "#1D9E75" if entry["verdict"] == "Strong" else \
                     "#BA7517" if entry["verdict"] == "Moderate" else \
                     "#C0392B"

                scores = entry["scores"]

                with st.expander(
                    f"{entry['verdict']} · {entry['total_score']}/100 · "
                    f"{entry['address'][:55]}"
                ):
                    col_info, col_scores = st.columns([2, 3])

                    with col_info:
                        mode_badge  = "Single Site" if entry.get("mode","single") == "single" else "Compare"
                        badge_color = "#185FA5" if mode_badge == "Single Site" else "#8B5CF6"

                        st.markdown(
                            f"<div style=\"display:inline-block;background:{badge_color};"
                            f"color:white;font-size:9px;font-weight:600;"
                            f"padding:3px 8px;border-radius:20px;"
                            f"margin-bottom:10px;letter-spacing:0.5px\">"
                            f"{mode_badge.upper()}</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<div style=\"margin-bottom:10px\">"
                            f"<div style=\"font-size:11px;color:#888\">SCORED ON</div>"
                            f"<div style=\"font-size:13px;color:white\">{entry['timestamp']}</div>"
                            f"</div>"
                            f"<div style=\"margin-bottom:10px\">"
                            f"<div style=\"font-size:11px;color:#888\">BRAND TYPE</div>"
                            f"<div style=\"font-size:13px;color:white;text-transform:capitalize\">{entry['brand_type']}</div>"
                            f"</div>"
                            f"<div style=\"margin-bottom:10px\">"
                            f"<div style=\"font-size:11px;color:#888\">LOCATION</div>"
                            f"<div style=\"font-size:12px;color:#9ecfc0\">{entry['lat']:.4f}N, {entry['lng']:.4f}E</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<div style=\"background:#0A2E26;border-radius:8px;"
                            f"padding:14px;text-align:center\">"
                            f"<div style=\"font-size:36px;font-weight:700;color:{vc}\">{entry['total_score']}</div>"
                            f"<div style=\"font-size:11px;color:#9ecfc0\">out of 100</div>"
                            f"<div style=\"font-size:13px;font-weight:600;color:{vc};margin-top:4px\">"
                            f"{entry['verdict'].upper()} SITE</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                    with col_scores:
                        st.markdown("**Score breakdown**")
                        for label, key in [
                            ("Demand",        "demand"),
                            ("Footfall",      "footfall"),
                            ("Competition",   "competition"),
                            ("Accessibility", "accessibility"),
                            ("Catchment",     "catchment"),
                            ("Spending Power","spending_power"),
                        ]:
                            s   = scores.get(key, 0)
                            col = "#1D9E75" if s>=65 else "#BA7517" if s>=45 else "#C0392B"
                            bar = int(s)
                            st.markdown(
                                f"<div style=\"margin-bottom:8px\">"
                                f"<div style=\"display:flex;justify-content:space-between;margin-bottom:3px\">"
                                f"<span style=\"font-size:11px;color:#888\">{label}</span>"
                                f"<span style=\"font-size:12px;font-weight:700;color:{col}\">{s}</span>"
                                f"</div>"
                                f"<div style=\"background:#222;border-radius:3px;height:5px\">"
                                f"<div style=\"width:{bar}%;background:{col};height:5px;border-radius:3px\">"
                                f"</div></div></div>",
                                unsafe_allow_html=True
                            )

                    # Re-score button
                    if st.button(
                        f"Re-score this site",
                        key=f"rescore_{entry['address'][:20]}"
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