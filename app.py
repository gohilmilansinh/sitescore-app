import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from scorer import score_site
from report import generate_report
import time
import io

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
    ["Single Site", "Compare 3 Sites"],
    horizontal=True,
    label_visibility="collapsed"
)

# ── Session state ─────────────────────────────────────────
if "result"   not in st.session_state: st.session_state.result   = None
if "compared" not in st.session_state: st.session_state.compared = None

# ════════════════════════════════════════════════════════════
# SINGLE SITE MODE
# ════════════════════════════════════════════════════════════
if mode == "Single Site":

    col_input, col_type = st.columns([3, 1])
    with col_input:
        address = st.text_input(
            "Address",
            placeholder="e.g. CG Road, Ahmedabad, Gujarat",
            label_visibility="collapsed",
            key="single_address"
        )
    with col_type:
        brand_type = st.selectbox(
            "Type", ["restaurant","pharmacy","supermarket","bank","school"],
            label_visibility="collapsed", key="single_type"
        )

    if st.button("Score This Site", type="primary", use_container_width=True):
        if address.strip():
            with st.spinner("Analysing location — takes 20–30 seconds..."):
                result = score_site(address.strip(), brand_type)
            if result:
                st.session_state.result = result
            else:
                st.error("Could not geocode. Try adding 'Ahmedabad, Gujarat'.")

    if st.session_state.result:
        result       = st.session_state.result
        scores       = result["scores"]
        total        = result["total_score"]
        verdict      = result["verdict"]
        lat, lng     = result["lat"], result["lng"]
        vc           = "#1D9E75" if verdict=="Strong" else \
                       "#BA7517" if verdict=="Moderate" else "#C0392B"

        st.markdown("---")
        col_score, col_radar = st.columns([1, 2])

        with col_score:
            st.markdown(f"""
            <div class='score-box'>
              <div style='font-size:72px;font-weight:700;
                          color:{vc};line-height:1'>{total}</div>
              <div style='font-size:13px;color:#9ecfc0;
                          margin-top:4px'>out of 100</div>
              <hr style='border-color:#1a4a3a;margin:14px 0'>
              <div style='color:{vc};font-size:18px;font-weight:700'>
                {verdict.upper()} SITE</div>
              <div style='color:#9ecfc0;font-size:11px;margin-top:8px'>
                {result["address"][:55]}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>",
                        unsafe_allow_html=True)

            for label, key in [("Demand","demand"),("Footfall","footfall"),
                                ("Competition","competition"),
                                ("Accessibility","accessibility"),
                                ("Catchment","catchment")]:
                s   = scores[key]
                col = "#1D9E75" if s>=65 else "#BA7517" if s>=45 else "#C0392B"
                st.markdown(f"""
                <div class='metric-card'>
                  <div class='metric-val' style='color:{col}'>{s}</div>
                  <div class='metric-lbl'>{label}</div>
                </div>""", unsafe_allow_html=True)

        with col_radar:
            cats = ["Demand","Footfall","Competition","Accessibility","Catchment"]
            vals = [scores["demand"], scores["footfall"], scores["competition"],
                    scores["accessibility"], scores["catchment"]]
            fig  = go.Figure(go.Scatterpolar(
                r=vals+[vals[0]], theta=cats+[cats[0]],
                fill="toself", fillcolor="rgba(29,158,117,0.15)",
                line=dict(color="#1D9E75", width=2),
                marker=dict(color="#1D9E75", size=7),
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor="#F0FAF6",
                    radialaxis=dict(visible=True, range=[0,100],
                                    tickfont=dict(size=9),
                                    gridcolor="#DDDDDD"),
                    angularaxis=dict(tickfont=dict(size=12, color="#333"))
                ),
                showlegend=False, height=400,
                margin=dict(l=40,r=40,t=40,b=40),
                paper_bgcolor="white"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Map
        st.markdown("### Location Map")
        m = folium.Map(location=[lat,lng], zoom_start=15,
                       tiles="CartoDB positron")
        folium.CircleMarker(
            location=[lat,lng], radius=14,
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
        st_folium(m, width="100%", height=420, returned_objects=[])

        # Risk flags
        st.markdown("### Risk Assessment")
        risks = []
        if scores["competition"]   < 30: risks.append("High competitor density within 500m — market may be saturated")
        if scores["demand"]        < 40: risks.append("Low residential population density — walk-in customer base limited")
        if scores["footfall"]      < 40: risks.append("Few anchor stores nearby — footfall dependent on destination visits")
        if scores["accessibility"] < 40: risks.append("Limited road connectivity — may reduce customer convenience")

        if risks:
            for r in risks:
                st.markdown(f"<div class='risk-box'>! {r}</div>",
                            unsafe_allow_html=True)
        else:
            st.markdown(
                "<div class='ok-box'>No significant risk flags at this location</div>",
                unsafe_allow_html=True)

        # PDF download
        st.markdown("---")
        if st.button("Generate PDF Report", use_container_width=True):
            with st.spinner("Generating PDF..."):
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

        st.caption("SiteScore Analytics · Ahmedabad · OpenStreetMap + Google Places API")


# ════════════════════════════════════════════════════════════
# COMPARE 3 SITES MODE
# ════════════════════════════════════════════════════════════
else:
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
                    if r:
                        results.append(r)
                    progress.progress((i+1)/len(addresses),
                                      text=f"Scored {i+1} of {len(addresses)}")
                    time.sleep(0.5)
            progress.empty()

            if results:
                results.sort(key=lambda x: x["total_score"], reverse=True)
                st.session_state.compared = results
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
        categories   = ["Demand","Footfall","Competition",
                        "Accessibility","Catchment"]
        score_keys   = ["demand","footfall","competition",
                        "accessibility","catchment"]
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

        # Detailed score table
        st.markdown("### Detailed Score Table")
        header_cols = st.columns([2.5,1,1,1,1,1,1.2])
        headers = ["Address","Demand","Footfall","Competition",
                   "Accessibility","Catchment","Total"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"**{h}**")
        st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

        for i, r in enumerate(results):
            row_cols = st.columns([2.5,1,1,1,1,1,1.2])
            vc = rank_colors[i] if i < 3 else "#888"
            row_cols[0].markdown(
                f"{rank_emoji[i]} {r['address'].split(',')[0]}")
            for j, key in enumerate(score_keys):
                s  = r["scores"][key]
                c  = "#1D9E75" if s>=65 else "#BA7517" if s>=45 else "#C0392B"
                row_cols[j+1].markdown(
                    f"<span style='color:{c};font-weight:600'>{s}</span>",
                    unsafe_allow_html=True)
            row_cols[6].markdown(
                f"<span style='color:{vc};font-weight:700;font-size:16px'>"
                f"{r['total_score']}</span>",
                unsafe_allow_html=True)

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
        if st.button("Download PDF for Best Site", use_container_width=True):
            with st.spinner("Generating PDF..."):
                path = f"/tmp/best_site_report.pdf"
                generate_report(best, path)
                with open(path, "rb") as f:
                    pdf_bytes = f.read()
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name="best_site_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.caption(
            "SiteScore Analytics · Ahmedabad · "
            "OpenStreetMap + Google Places API")