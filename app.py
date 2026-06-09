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
import os
import tempfile
import pandas as pd

st.set_page_config(
    page_title="SiteIQ — Retail Location Intelligence",
    page_icon="assets/sitelogo.png",
    layout="wide",
)

render_header()

# ── Mode selector ─────────────────────────────────────────
mode = st.radio(
    "Mode",
    ["Single Site", "Compare N Sites", "Batch Upload", "History"],
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
if "batch_results" not in st.session_state:
    st.session_state.batch_results = None

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

    try:
        GKEY = st.secrets.get("GOOGLE_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    except Exception:
        GKEY = os.environ.get("GOOGLE_API_KEY", "")

    if "address" in st.query_params:
        st.session_state.search_address = st.query_params["address"]

    current_address = st.session_state.get("search_address", "")

    # ── Type selector ─────────────────────────────────────
    brand_type = st.selectbox(
        "Select brand type",
        ["restaurant", "pharmacy", "supermarket", "bank", "school"],
        key="single_type_v2",
    )

    # ── Search + Map (always visible) ─────────────────────
    search_html = f"""
    <style>
      * {{ box-sizing:border-box;margin:0;padding:0 }}
      body {{ background:transparent;overflow:visible }}

      #pac-input {{
        width:100%;padding:12px 36px 12px 14px;
        font-size:14px;border:1px solid #1D9E75;
        border-radius:8px;background:#0d1f1a;
        color:white;outline:none;font-family:sans-serif;
        margin-bottom:8px;
      }}
      #pac-input::placeholder {{ color:#666; }}

      #input-wrap {{ position:relative;width:100%; }}

      #clear-btn {{
        position:absolute;right:10px;top:13px;
        background:none;border:none;color:#666;
        font-size:18px;cursor:pointer;line-height:1;
        display:none;
      }}

      #map-div {{
        width:100%;height:320px;border-radius:10px;
        border:1px solid #1a3a2a;
      }}

      #status {{
        font-size:11px;color:#1D9E75;font-family:sans-serif;
        min-height:14px;margin-top:6px;
      }}

      .pac-container {{
        z-index:2147483647 !important;
        position:absolute !important;
        background:#0d1f1a !important;
        border:1px solid #1D9E75 !important;
        border-radius:0 0 8px 8px !important;
        font-family:sans-serif !important;
        box-shadow:0 8px 24px rgba(0,0,0,0.8) !important;
        margin-top:-8px !important;
      }}
      .pac-item {{
        color:#ccc !important;background:#0d1f1a !important;
        padding:10px 14px !important;font-size:13px !important;
        cursor:pointer !important;
        border-top:1px solid #1a3a2a !important;
      }}
      .pac-item:hover {{ background:#1a4a3a !important; }}
      .pac-item-query {{ color:white !important;font-size:13px !important; }}
      .pac-matched {{ color:#1D9E75 !important;font-weight:600 !important; }}
      .pac-icon {{ display:none !important; }}
    </style>

    <div id='input-wrap'>
      <input id='pac-input' type='text'
        placeholder='Search any location in Gujarat...'
        value='{current_address}' autocomplete='off'/>
      <button id='clear-btn' onclick='clearInput()'>×</button>
    </div>

    <div id='map-div'></div>
    <div id='status'></div>

    <script>
      let map, marker, autocomplete, geocoder;
      const input  = document.getElementById('pac-input');
      const clrBtn = document.getElementById('clear-btn');
      const status = document.getElementById('status');

      input.addEventListener('input', function() {{
        clrBtn.style.display = this.value ? 'block' : 'none';
      }});
      if (input.value) clrBtn.style.display = 'block';

      // Expand iframe when suggestions appear
      const observer = new MutationObserver(function() {{
        const pac = document.querySelector('.pac-container');
        if (pac && pac.children.length > 0 &&
            pac.style.display !== 'none') {{
          const h = 370 + pac.offsetHeight + 10;
          window.frameElement.style.height = h + 'px';
        }} else {{
          window.frameElement.style.height = '370px';
        }}
      }});
      observer.observe(document.body, {{
        childList:true, subtree:true,
        attributes:true, attributeFilter:['style']
      }});

      function clearInput() {{
        input.value = '';
        clrBtn.style.display = 'none';
        status.textContent = '';
        if (marker) marker.setMap(null);
      }}

      function pushAddress(addr) {{
        const url = new URL(window.parent.location.href);
        url.searchParams.set('address', addr);
        window.parent.history.replaceState({{}}, '', url.toString());
      }}

      function initMap() {{
        geocoder = new google.maps.Geocoder();

        // Default center: Ahmedabad
        const defaultCenter = {{ lat:23.0225, lng:72.5714 }};

        map = new google.maps.Map(
          document.getElementById('map-div'), {{
            center: defaultCenter,
            zoom: 12,
            mapTypeControl:false,
            streetViewControl:false,
            fullscreenControl:false,
            zoomControl:true,
            styles:[
              {{elementType:'geometry',
                stylers:[{{color:'#0d1f1a'}}]}},
              {{elementType:'labels.text.fill',
                stylers:[{{color:'#9ecfc0'}}]}},
              {{elementType:'labels.text.stroke',
                stylers:[{{color:'#0a1a14'}}]}},
              {{featureType:'road',elementType:'geometry',
                stylers:[{{color:'#1a3a2a'}}]}},
              {{featureType:'road',elementType:'geometry.stroke',
                stylers:[{{color:'#0d2a1a'}}]}},
              {{featureType:'road.highway',elementType:'geometry',
                stylers:[{{color:'#1D9E75'}}]}},
              {{featureType:'water',elementType:'geometry',
                stylers:[{{color:'#0d1f2a'}}]}},
              {{featureType:'poi',elementType:'geometry',
                stylers:[{{color:'#0d2a1a'}}]}},
              {{featureType:'transit',elementType:'geometry',
                stylers:[{{color:'#0d2a1a'}}]}}
            ]
          }}
        );

        // If address already set, show it on map
        if ('{current_address}') {{
          geocoder.geocode(
            {{address: '{current_address}'}},
            function(results, s) {{
              if (s === 'OK' && results[0]) {{
                const loc = results[0].geometry.location;
                map.setCenter(loc);
                map.setZoom(15);
                placeMarker(loc, '{current_address}');
              }}
            }}
          );
        }}

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
          input.value = addr;
          clrBtn.style.display = 'block';
          status.textContent = '📍 ' + addr.substring(0,60);
          map.setCenter(place.geometry.location);
          map.setZoom(15);
          placeMarker(place.geometry.location, addr);
          pushAddress(addr);
        }});

        map.addListener('click', function(e) {{
          geocoder.geocode({{location:e.latLng}},
            function(results, s) {{
              const addr = (s==='OK' && results[0])
                ? results[0].formatted_address
                : e.latLng.lat().toFixed(6)+', '+
                  e.latLng.lng().toFixed(6)+', Gujarat, India';
              input.value = addr;
              clrBtn.style.display = 'block';
              status.textContent = '📍 '+addr.substring(0,60);
              placeMarker(e.latLng, addr);
              pushAddress(addr);
            }}
          );
        }});
      }}

      function placeMarker(position, addr) {{
        if (marker) marker.setMap(null);
        marker = new google.maps.Marker({{
          position:position, map:map, title:addr,
          animation: google.maps.Animation.DROP,
          icon:{{
            path:google.maps.SymbolPath.CIRCLE,
            scale:12,
            fillColor:'#1D9E75',
            fillOpacity:1,
            strokeColor:'#ffffff',
            strokeWeight:2.5
          }}
        }});
      }}
    </script>
    <script
      src="https://maps.googleapis.com/maps/api/js?key={GKEY}&libraries=places&callback=initMap"
      async defer></script>
    """

    components.html(search_html, height=370, scrolling=False)

    # ── Score button ──────────────────────────────────────
    if st.button("Score This Site", type="primary", use_container_width=True):
        # Re-read address from query params in case updated by map
        if "address" in st.query_params:
            st.session_state.search_address = st.query_params["address"]
        addr = st.session_state.get("search_address", "").strip()
        if addr:
            with st.spinner("Analysing location..."):
                result = score_site(addr, brand_type)
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
            st.warning(
                "Please search or click on the map to select " "a location first."
            )

    # ── Results ───────────────────────────────────────────
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
elif mode == "Compare N Sites":

    try:
        GKEY = st.secrets.get("GOOGLE_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    except Exception:
        GKEY = os.environ.get("GOOGLE_API_KEY", "")

    st.markdown("#### Compare Multiple Sites")

    # ── Number of sites selector ──────────────────────────
    num_sites = st.slider(
        "How many sites to compare?", min_value=2, max_value=6, value=3, step=1
    )

    brand_type_c = st.selectbox(
        "Brand type",
        ["restaurant", "pharmacy", "supermarket", "bank", "school"],
        key="compare_type",
    )

    # ── Initialize session state for addresses ────────────
    if "compare_addresses" not in st.session_state:
        st.session_state.compare_addresses = [""] * 6
    if len(st.session_state.compare_addresses) < 6:
        st.session_state.compare_addresses += [""] * (
            6 - len(st.session_state.compare_addresses)
        )

    # Read any address updates from query params
    for i in range(num_sites):
        key = f"caddr_{i}"
        if key in st.query_params:
            st.session_state.compare_addresses[i] = st.query_params[key]

    # ── Multi-site map + search boxes ─────────────────────
    # Build JS arrays for current addresses
    addr_js = (
        "["
        + ",".join(
            f'"{st.session_state.compare_addresses[i]}"' for i in range(num_sites)
        )
        + "]"
    )

    colors_js = '["#1D9E75","#BA7517","#C0392B",' '"#185FA5","#8B5CF6","#E67E22"]'

    compare_html = f"""
    <style>
      * {{ box-sizing:border-box;margin:0;padding:0 }}
      body {{ background:transparent;overflow:visible }}

      .sites-grid {{
        display:grid;
        grid-template-columns: repeat(auto-fit, minmax(260px,1fr));
        gap:10px;
        margin-bottom:10px;
      }}

      .site-input-wrap {{
        position:relative;
      }}

      .site-label {{
        font-size:11px;font-weight:600;
        font-family:sans-serif;margin-bottom:4px;
        letter-spacing:0.5px;
      }}

      .site-input {{
        width:100%;padding:10px 30px 10px 12px;
        font-size:13px;border-radius:8px;
        background:#0d1f1a;color:white;
        outline:none;font-family:sans-serif;
        border:2px solid #333;
      }}
      .site-input::placeholder {{ color:#555; }}
      .site-input:focus {{ border-color:#1D9E75; }}

      .clear-site-btn {{
        position:absolute;right:8px;bottom:10px;
        background:none;border:none;color:#555;
        font-size:16px;cursor:pointer;line-height:1;
        display:none;
      }}

      #compare-map {{
        width:100%;height:360px;border-radius:10px;
        border:1px solid #1a3a2a;margin-top:10px;
      }}

      #map-status {{
        font-size:11px;color:#9ecfc0;
        font-family:sans-serif;margin-top:6px;
        min-height:14px;
      }}

      .pac-container {{
        z-index:2147483647 !important;
        position:absolute !important;
        background:#0d1f1a !important;
        border:1px solid #1D9E75 !important;
        border-radius:0 0 8px 8px !important;
        font-family:sans-serif !important;
        box-shadow:0 8px 24px rgba(0,0,0,0.8) !important;
      }}
      .pac-item {{
        color:#ccc !important;background:#0d1f1a !important;
        padding:10px 14px !important;font-size:13px !important;
        cursor:pointer !important;
        border-top:1px solid #1a3a2a !important;
      }}
      .pac-item:hover {{ background:#1a4a3a !important; }}
      .pac-item-query {{ color:white !important; }}
      .pac-matched {{ color:#1D9E75 !important;font-weight:600 !important; }}
      .pac-icon {{ display:none !important; }}
    </style>

    <div class='sites-grid' id='sites-grid'></div>
    <div id='compare-map'></div>
    <div id='map-status'>
      Click any marker to edit · Click empty map area to add a pin
    </div>

    <script>
      const NUM_SITES  = {num_sites};
      const ADDRESSES  = {addr_js};
      const COLORS     = {colors_js};
      const LABELS     = ['A','B','C','D','E','F'];
      const GKEY       = '{GKEY}';

      let map, geocoder;
      let markers   = Array(NUM_SITES).fill(null);
      let autocomps = Array(NUM_SITES).fill(null);
      let inputs    = Array(NUM_SITES).fill(null);

      // Build input grid
      const grid = document.getElementById('sites-grid');
      for (let i = 0; i < NUM_SITES; i++) {{
        const wrap = document.createElement('div');
        wrap.className = 'site-input-wrap';
        wrap.innerHTML = `
          <div class="site-label"
            style="color:${{COLORS[i]}}">
            SITE ${{LABELS[i]}}
          </div>
          <input
            id="site-input-${{i}}"
            class="site-input"
            type="text"
            placeholder="Search location ${{i+1}}..."
            value="${{ADDRESSES[i]}}"
            autocomplete="off"
            style="border-color:${{ADDRESSES[i] ? COLORS[i] : '#333'}}"
          />
          <button
            class="clear-site-btn"
            id="clear-${{i}}"
            onclick="clearSite(${{i}})"
            style="display:${{ADDRESSES[i] ? 'block' : 'none'}}">
            ×
          </button>
        `;
        grid.appendChild(wrap);
        inputs[i] = document.getElementById(`site-input-${{i}}`);
        inputs[i].addEventListener('input', function() {{
          document.getElementById(`clear-${{i}}`).style.display =
            this.value ? 'block' : 'none';
          inputs[i].style.borderColor =
            this.value ? COLORS[i] : '#333';
        }});
      }}

      function clearSite(i) {{
        inputs[i].value = '';
        inputs[i].style.borderColor = '#333';
        document.getElementById(`clear-${{i}}`).style.display = 'none';
        if (markers[i]) {{ markers[i].setMap(null); markers[i] = null; }}
        pushAddress(i, '');
      }}

      function pushAddress(i, addr) {{
        const url = new URL(window.parent.location.href);
        url.searchParams.set(`caddr_${{i}}`, addr);
        window.parent.history.replaceState({{}}, '', url.toString());
      }}

      function placeMarker(i, position, addr) {{
        if (markers[i]) markers[i].setMap(null);
        markers[i] = new google.maps.Marker({{
          position: position,
          map: map,
          title: addr,
          animation: google.maps.Animation.DROP,
          label: {{
            text: LABELS[i],
            color: 'white',
            fontWeight: 'bold',
            fontSize: '13px'
          }},
          icon: {{
            path: google.maps.SymbolPath.CIRCLE,
            scale: 16,
            fillColor: COLORS[i],
            fillOpacity: 1,
            strokeColor: '#ffffff',
            strokeWeight: 2.5
          }}
        }});

        // Click marker to focus its input
        markers[i].addListener('click', function() {{
          inputs[i].focus();
          inputs[i].select();
        }});
      }}

      function geocodeAndPlace(i, addr) {{
        if (!addr.trim()) return;
        geocoder.geocode({{address: addr + ', Gujarat, India'}},
          function(results, s) {{
            if (s === 'OK' && results[0]) {{
              placeMarker(i, results[0].geometry.location, addr);
              // Fit map to all markers
              fitMapToMarkers();
            }}
          }}
        );
      }}

      function fitMapToMarkers() {{
        const bounds = new google.maps.LatLngBounds();
        let count = 0;
        markers.forEach(function(m) {{
          if (m) {{ bounds.extend(m.getPosition()); count++; }}
        }});
        if (count === 1) {{
          map.setCenter(bounds.getCenter());
          map.setZoom(14);
        }} else if (count > 1) {{
          map.fitBounds(bounds, {{padding: 60}});
        }}
      }}

      function initMap() {{
        geocoder = new google.maps.Geocoder();

        map = new google.maps.Map(
          document.getElementById('compare-map'), {{
            center: {{ lat:23.0225, lng:72.5714 }},
            zoom: 11,
            mapTypeControl:false,
            streetViewControl:false,
            fullscreenControl:false,
            styles:[
              {{elementType:'geometry',
                stylers:[{{color:'#0d1f1a'}}]}},
              {{elementType:'labels.text.fill',
                stylers:[{{color:'#9ecfc0'}}]}},
              {{elementType:'labels.text.stroke',
                stylers:[{{color:'#0a1a14'}}]}},
              {{featureType:'road',elementType:'geometry',
                stylers:[{{color:'#1a3a2a'}}]}},
              {{featureType:'road.highway',elementType:'geometry',
                stylers:[{{color:'#1D9E75'}}]}},
              {{featureType:'water',elementType:'geometry',
                stylers:[{{color:'#0d1f2a'}}]}},
              {{featureType:'poi',
                stylers:[{{visibility:'off'}}]}}
            ]
          }}
        );

        // Setup autocomplete for each input
        for (let i = 0; i < NUM_SITES; i++) {{
          autocomps[i] = new google.maps.places.Autocomplete(
            inputs[i], {{
              componentRestrictions: {{ country:'in' }},
              bounds: new google.maps.LatLngBounds(
                new google.maps.LatLng(20.1, 68.1),
                new google.maps.LatLng(24.7, 74.5)
              ),
              strictBounds: false,
              fields: ['formatted_address','geometry','name']
            }}
          );

          (function(idx) {{
            autocomps[idx].addListener('place_changed', function() {{
              const place = autocomps[idx].getPlace();
              if (!place.geometry) return;
              const addr = place.formatted_address || place.name;
              inputs[idx].value = addr;
              inputs[idx].style.borderColor = COLORS[idx];
              document.getElementById(`clear-${{idx}}`).style.display = 'block';
              placeMarker(idx, place.geometry.location, addr);
              pushAddress(idx, addr);
              fitMapToMarkers();
            }});
          }})(i);

          // Show existing addresses on map
          if (ADDRESSES[i]) {{
            geocodeAndPlace(i, ADDRESSES[i]);
          }}
        }}

        // Click on map to assign to next empty slot
        map.addListener('click', function(e) {{
          // Find first empty slot
          let emptyIdx = -1;
          for (let i = 0; i < NUM_SITES; i++) {{
            if (!inputs[i].value.trim()) {{
              emptyIdx = i; break;
            }}
          }}
          if (emptyIdx === -1) return; // all filled

          geocoder.geocode({{location: e.latLng}},
            function(results, s) {{
              const addr = (s==='OK' && results[0])
                ? results[0].formatted_address
                : e.latLng.lat().toFixed(6)+', '+
                  e.latLng.lng().toFixed(6)+', Gujarat, India';
              inputs[emptyIdx].value = addr;
              inputs[emptyIdx].style.borderColor = COLORS[emptyIdx];
              document.getElementById(
                `clear-${{emptyIdx}}`).style.display = 'block';
              placeMarker(emptyIdx, e.latLng, addr);
              pushAddress(emptyIdx, addr);
              document.getElementById('map-status').textContent =
                `Site ${{LABELS[emptyIdx]}} set to: ${{addr.substring(0,50)}}`;
            }}
          );
        }});
      }}
    </script>
    <script
      src="https://maps.googleapis.com/maps/api/js?key={GKEY}&libraries=places&callback=initMap"
      async defer></script>
    """

    components.html(compare_html, height=500, scrolling=False)

    # ── Compare button ────────────────────────────────────
    if st.button("Compare All Sites", type="primary", use_container_width=True):

        # Re-read addresses from query params
        for i in range(num_sites):
            key = f"caddr_{i}"
            if key in st.query_params:
                st.session_state.compare_addresses[i] = st.query_params[key]

        addresses = [
            st.session_state.compare_addresses[i].strip()
            for i in range(num_sites)
            if st.session_state.compare_addresses[i].strip()
        ]

        if len(addresses) < 2:
            st.warning("Please enter at least 2 addresses " "to compare.")
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
                    time.sleep(0.3)
            progress.empty()

            if results:
                results.sort(key=lambda x: x["total_score"], reverse=True)
                st.session_state.compared = results
                for r in results:
                    r["mode"] = "compare"
                    save_to_history(r)
            else:
                st.error("Could not score any of those addresses.")

    # ── Results (same as before) ──────────────────────────
    if st.session_state.compared:
        results = st.session_state.compared
        rank_colors = ["#1D9E75", "#BA7517", "#C0392B", "#185FA5", "#8B5CF6", "#E67E22"]
        rank_labels = ["BEST", "2ND", "3RD", "4TH", "5TH", "6TH"]
        rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]

        st.markdown("---")
        st.markdown("### Ranking")

        cols = st.columns(len(results))
        for i, (r, col) in enumerate(zip(results, cols)):
            vc = rank_colors[i] if i < len(rank_colors) else "#888"
            with col:
                st.markdown(
                    f"<div style='background:#111;border:2px solid {vc};"
                    f"border-radius:10px;padding:14px;text-align:center;"
                    f"margin-bottom:10px'>"
                    f"<div style='font-size:10px;font-weight:700;"
                    f"color:{vc};letter-spacing:1px'>"
                    f"{rank_emoji[i]} {rank_labels[i]} SITE</div>"
                    f"<div style='font-size:32px;font-weight:700;"
                    f"color:{vc};line-height:1.2'>{r['total_score']}</div>"
                    f"<div style='font-size:12px;color:{vc};"
                    f"font-weight:600'>{r['verdict'].upper()}</div>"
                    f"<div style='font-size:10px;color:#666;"
                    f"margin-top:4px'>{r['address'][:35]}...</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Bar chart
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

        fig = go.Figure()
        for i, r in enumerate(results):
            vals = [r["scores"].get(k, 0) for k in score_keys]
            name = r["address"].split(",")[0]
            fig.add_trace(
                go.Bar(
                    name=name,
                    x=categories,
                    y=vals,
                    marker_color=rank_colors[i] if i < len(rank_colors) else "#888",
                    text=[str(v) for v in vals],
                    textposition="outside",
                )
            )
        fig.update_layout(
            barmode="group",
            height=420,
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(range=[0, 115], gridcolor="#EEEEEE"),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Score table
        st.markdown("### Detailed Score Table")

        def score_color(s):
            return "#1D9E75" if s >= 65 else "#BA7517" if s >= 45 else "#C0392B"

        rows_html = ""
        for i, r in enumerate(results):
            vc = rank_colors[i] if i < len(rank_colors) else "#888"
            name = r["address"].split(",")[0]
            rows_html += (
                f"<tr>"
                f"<td style='padding:12px 14px;border-bottom:1px solid #222'>"
                f"<span style='font-size:14px'>{rank_emoji[i]}</span>"
                f"<span style='font-weight:600;color:white'> {name}</span>"
                f"</td>"
            )
            for k in score_keys:
                s = r["scores"].get(k, 0)
                rows_html += (
                    f"<td style='padding:12px 10px;text-align:center;"
                    f"border-bottom:1px solid #222;"
                    f"color:{score_color(s)};font-weight:600'>{s}</td>"
                )
            rows_html += (
                f"<td style='padding:12px 10px;text-align:center;"
                f"border-bottom:1px solid #222;color:{vc};"
                f"font-weight:700;font-size:16px'>"
                f"{r['total_score']}</td></tr>"
            )

        table_html = f"""<!DOCTYPE html><html><head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
          body{{margin:0;padding:0;background:transparent}}
          .wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;
                border-radius:10px;border:1px solid #333}}
          table{{width:100%;border-collapse:collapse;background:#111;
                font-size:13px;white-space:nowrap;font-family:sans-serif}}
          thead tr{{background:#0A2E26}}
          th{{padding:12px 10px;text-align:center;color:#9ecfc0;
              font-size:11px;letter-spacing:0.5px;font-weight:600}}
          th:first-child{{text-align:left;padding-left:14px}}
        </style></head><body>
        <div class="wrap"><table><thead><tr>
          <th>ADDRESS</th><th>DEMAND</th><th>FOOTFALL</th>
          <th>COMPETITION</th><th>ACCESS</th><th>CATCHMENT</th>
          <th>SPENDING</th><th>TOTAL</th>
        </tr></thead><tbody>{rows_html}</tbody></table></div>
        </body></html>"""

        components.html(table_html, height=40 + len(results) * 52)

        # Multi-site results map
        st.markdown("### All Sites on Map")
        center_lat = sum(r["lat"] for r in results) / len(results)
        center_lng = sum(r["lng"] for r in results) / len(results)
        m = folium.Map(
            location=[center_lat, center_lng], zoom_start=12, tiles="CartoDB positron"
        )
        for i, r in enumerate(results):
            color = (["green", "orange", "red", "blue", "purple", "darkred"])[i % 6]
            folium.CircleMarker(
                location=[r["lat"], r["lng"]],
                radius=16,
                color="#0A2E26",
                fill=True,
                fill_color=rank_colors[i % len(rank_colors)],
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
                color=rank_colors[i % len(rank_colors)],
                fill=True,
                fill_color=rank_colors[i % len(rank_colors)],
                fill_opacity=0.05,
                weight=1.5,
            ).add_to(m)
        st_folium(m, width="100%", height=460, returned_objects=[])

        # Recommendation
        best = results[0]
        st.markdown("### Recommendation")
        st.markdown(
            f"<div style='background:#0A2E26;border-radius:10px;"
            f"padding:20px 24px;color:white'>"
            f"<div style='font-size:11px;color:#9ecfc0;"
            f"letter-spacing:1px'>RECOMMENDED SITE</div>"
            f"<div style='font-size:22px;font-weight:700;"
            f"color:#1D9E75;margin-top:6px'>{best['address']}</div>"
            f"<div style='font-size:14px;color:#9ecfc0;margin-top:8px'>"
            f"Scored {best['total_score']}/100 — highest across all "
            f"{len(results)} candidate sites analysed.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # PDF for best site
        st.markdown("")
        with st.spinner("Preparing PDF..."):
            path = os.path.join(tempfile.gettempdir(),
                                "SiteIQ_best_site_report.pdf")
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
            "SiteScore Analytics · Gujarat · " "OpenStreetMap + Google Places API"
        )


# ════════════════════════════════════════════════════════════
# BATCH UPLOAD MODE
# ════════════════════════════════════════════════════════════
elif mode == "Batch Upload":
    from batch_scorer import (
        validate_csv, score_batch,
        results_to_dataframe
    )
    import io

    st.markdown("### Batch Site Scoring")
    st.markdown(
        "<div style='font-size:13px;color:#888;margin-bottom:16px'>"
        "Upload a CSV with multiple addresses. Score all at once. "
        "Export results to CSV or download PDF for the best site. "
        "Maximum 20 sites per batch.</div>",
        unsafe_allow_html=True,
    )

    # Download template
    template_csv = (
        "address,brand_type,monthly_rent,notes\n"
        "'Bopal, Ahmedabad, Gujarat',restaurant,80000,"
        "Near D-Mart\n"
        "'CG Road, Ahmedabad, Gujarat',restaurant,120000,"
        "Main commercial street\n"
        "'Prahlad Nagar, Ahmedabad', Gujarat,restaurant,"
        "95000,Corporate hub\n"
    )
    st.download_button(
        label="Download CSV Template",
        data=template_csv,
        file_name="siteiq_template.csv",
        mime="text/csv",
    )

    uploaded_file = st.file_uploader(
        "Upload your sites CSV",
        type=["csv"],
        help="CSV must have an 'address' column. "
             "Optional: brand_type, monthly_rent, notes",
    )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
            st.stop()

        is_valid, msg = validate_csv(df)
        if not is_valid:
            st.error(msg)
            st.stop()

        # Preview
        st.markdown(f"**{len(df)} sites ready to score**")
        st.dataframe(
            df[["address"] + [
                c for c in
                ["brand_type", "monthly_rent", "notes"]
                if c in df.columns
            ]],
            use_container_width=True,
            height=min(200, 50 + len(df) * 35),
        )

        if st.button(
            f"Score All {len(df)} Sites",
            type="primary",
            use_container_width=True,
        ):
            progress_bar = st.progress(
                0, text="Starting batch scoring...")
            status_text  = st.empty()
            results_container = st.empty()

            scored = []

            def update_progress(current, total, address):
                pct = current / total
                progress_bar.progress(
                    pct,
                    text=f"Scoring {current}/{total}: "
                         f"{address[:40]}..."
                )
                status_text.markdown(
                    f"<div style='font-size:12px;color:#888'>"
                    f"Scored {current} of {total} sites</div>",
                    unsafe_allow_html=True,
                )

            with st.spinner("Batch scoring in progress..."):
                scored = score_batch(df, update_progress)

            progress_bar.empty()
            status_text.empty()

            if scored:
                st.session_state.batch_results = scored
                st.success(
                    f"Scored {len(scored)} sites successfully."
                )
            else:
                st.error("No sites could be scored.")

    # Show batch results
    if "batch_results" in st.session_state and \
            st.session_state.batch_results:
        results = st.session_state.batch_results
        scored  = [r for r in results
                   if r.get("status") == "scored"]
        errors  = [r for r in results
                   if r.get("status") == "error"]

        st.markdown("---")
        st.markdown(
            f"### Results — {len(scored)} scored"
            + (f", {len(errors)} failed" if errors else "")
        )

        # Summary metrics
        if scored:
            avg_score = round(
                sum(r["total_score"] for r in scored) /
                len(scored), 1
            )
            strong   = sum(
                1 for r in scored
                if r["verdict"] == "Strong"
            )
            moderate = sum(
                1 for r in scored
                if r["verdict"] == "Moderate"
            )
            weak     = sum(
                1 for r in scored
                if r["verdict"] == "Weak"
            )

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Sites Scored",   len(scored))
            c2.metric("Average Score",  avg_score)
            c3.metric("Strong Sites",   strong)
            c4.metric("Moderate Sites", moderate)
            c5.metric("Weak Sites",     weak)

        # Results table
        rank_colors = [
            "#1D9E75", "#1D9E75", "#1D9E75",
            "#BA7517", "#BA7517",
            "#C0392B", "#C0392B",
        ]

        rows_html = ""
        for i, r in enumerate(scored):
            score = r["total_score"]
            col   = (
                "#1D9E75" if score >= 65
                else "#BA7517" if score >= 45
                else "#C0392B"
            )

            def sc(s):
                if s == "":
                    return "<td style='padding:8px;color:#555;" \
                           "text-align:center'>—</td>"
                v = float(s) if s else 0
                c = ("#1D9E75" if v >= 65
                     else "#BA7517" if v >= 45
                     else "#C0392B")
                return (
                    f"<td style='padding:8px;text-align:center;"
                    f"color:{c};font-weight:600'>{s}</td>"
                )

            has_roi = r.get("monthly_rent", 0) > 0
            roi_cells = ""
            if has_roi:
                roi_cells = (
                    f"<td style='padding:8px;text-align:center;"
                    f"color:#9ecfc0'>"
                    f"Rs.{r.get('monthly_rent',0):,.0f}</td>"
                    f"<td style='padding:8px;text-align:center;"
                    f"color:#1D9E75'>"
                    f"Rs.{r.get('monthly_profit',0):,.0f}</td>"
                    f"<td style='padding:8px;text-align:center;"
                    f"color:{col}'>"
                    f"{r.get('payback_months',0):.0f}mo</td>"
                )

            rows_html += (
                f"<tr style='border-bottom:1px solid #1a1a1a'>"
                f"<td style='padding:8px 12px;font-weight:700;"
                f"color:#9ecfc0'>#{i+1}</td>"
                f"<td style='padding:8px;color:white;"
                f"max-width:200px'>"
                f"{r['address'][:45]}</td>"
                f"<td style='padding:8px;text-align:center;"
                f"color:{col};font-weight:700;font-size:15px'>"
                f"{score}</td>"
                f"<td style='padding:8px;text-align:center;"
                f"color:{col};font-weight:600'>"
                f"{r['verdict']}</td>"
                + sc(r.get("demand", ""))
                + sc(r.get("footfall", ""))
                + sc(r.get("competition", ""))
                + sc(r.get("accessibility", ""))
                + sc(r.get("catchment", ""))
                + sc(r.get("spending_power", ""))
                + roi_cells
                + f"<td style='padding:8px;color:#555;"
                f"font-size:11px'>{r.get('notes','')}</td>"
                f"</tr>"
            )

        has_any_roi = any(
            r.get("monthly_rent", 0) > 0 for r in scored
        )
        roi_headers = ""
        if has_any_roi:
            roi_headers = (
                "<th>RENT</th>"
                "<th>PROFIT</th>"
                "<th>PAYBACK</th>"
            )

        table_html = f"""<!DOCTYPE html><html><head>
        <style>
          body{{margin:0;background:transparent;
               font-family:sans-serif;font-size:12px}}
          table{{width:100%;border-collapse:collapse}}
          thead tr{{background:#0A2E26}}
          th{{padding:10px 8px;color:#9ecfc0;font-size:10px;
              letter-spacing:.5px;text-align:center;
              font-weight:600;white-space:nowrap}}
          th:nth-child(2){{text-align:left}}
          .wrap{{overflow-x:auto;
                 -webkit-overflow-scrolling:touch;
                 border-radius:10px;
                 border:1px solid #333}}
        </style></head><body>
        <div class="wrap"><table>
          <thead><tr>
            <th>#</th>
            <th style='text-align:left'>ADDRESS</th>
            <th>SCORE</th><th>VERDICT</th>
            <th>DEMAND</th><th>FOOTFALL</th>
            <th>COMP</th><th>ACCESS</th>
            <th>CATCH</th><th>SPEND</th>
            {roi_headers}
            <th>NOTES</th>
          </tr></thead>
          <tbody style='background:#111;color:white'>
            {rows_html}
          </tbody>
        </table></div></body></html>"""

        components.html(
            table_html,
            height=60 + len(scored) * 48,
        )

        # Error rows
        if errors:
            st.markdown("**Failed addresses:**")
            for e in errors:
                st.markdown(
                    f"<div style='background:#1a0e0e;"
                    f"border-left:3px solid #C0392B;"
                    f"padding:8px 12px;border-radius:0 6px 6px 0;"
                    f"font-size:12px;color:#ccc;margin-bottom:4px'>"
                    f"! {e['address']} — "
                    f"{e.get('error_msg','Failed')}</div>",
                    unsafe_allow_html=True,
                )

        # Export CSV
        st.markdown("---")
        col_csv, col_pdf = st.columns(2)

        with col_csv:
            export_df  = results_to_dataframe(results)
            csv_buffer = io.StringIO()
            export_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Export Results to CSV",
                data=csv_buffer.getvalue(),
                file_name="siteiq_batch_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_pdf:
            if scored:
                best = scored[0]["full_result"]
                with st.spinner("Preparing PDF for best site..."):
                    path = os.path.join(
                        tempfile.gettempdir(),
                        "batch_best_report.pdf"
                    )
                    generate_report(best, path)
                    with open(path, "rb") as f:
                        pdf_bytes = f.read()
                st.download_button(
                    label=f"PDF Report — Best Site "
                          f"({scored[0]['address'][:25]}...)",
                    data=pdf_bytes,
                    file_name="siteiq_best_site_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        # Map of all scored sites
        if len(scored) >= 2:
            st.markdown("### All Sites on Map")
            center_lat = sum(
                r["full_result"]["lat"] for r in scored
            ) / len(scored)
            center_lng = sum(
                r["full_result"]["lng"] for r in scored
            ) / len(scored)
            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=11,
                tiles="CartoDB positron",
            )
            rank_cols = [
                "#1D9E75", "#1D9E75", "#BA7517",
                "#BA7517", "#C0392B", "#C0392B",
            ]
            for i, r in enumerate(scored[:10]):
                fr  = r["full_result"]
                col = rank_cols[min(i, len(rank_cols) - 1)]
                folium.CircleMarker(
                    location=[fr["lat"], fr["lng"]],
                    radius=14,
                    color="#0A2E26",
                    fill=True,
                    fill_color=col,
                    fill_opacity=0.9,
                    popup=folium.Popup(
                        f"<b>#{i+1} {r['address']}</b>"
                        f"<br>Score: {r['total_score']}/100"
                        f"<br>{r['verdict']}",
                        max_width=240,
                    ),
                ).add_to(m)
            st_folium(
                m, width="100%",
                height=420, returned_objects=[]
            )

        st.caption(
            "SiteIQ Analytics · Gujarat · "
            "OpenStreetMap + Google Places API"
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
