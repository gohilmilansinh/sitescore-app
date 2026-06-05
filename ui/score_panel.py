from __future__ import annotations

from typing import Any, Dict

import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from report import generate_report
from benchmarks import get_category_context


def render_score_breakdown(result: Dict[str, Any], brand_type: str) -> None:
    scores = result.get("scores", {})
    total = result["total_score"]
    verdict = result["verdict"]
    lat, lng = result["lat"], result["lng"]
    vc = (
        "#1D9E75"
        if verdict == "Strong"
        else "#BA7517"
        if verdict == "Moderate"
        else "#C0392B"
    )

    benchmark = get_category_context(total, brand_type)
    stats = benchmark["stats"]
    percentile = benchmark["percentile"]
    bar_color = (
        "#1D9E75"
        if percentile >= 65
        else "#BA7517"
        if percentile >= 40
        else "#C0392B"
    )

    st.markdown("---")

    st.markdown(
        f"""
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
          {result['address'][:60]}</div>
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
          <span>Avg {stats['average']}</span>
          <span>Top {stats['top_sites_avg']}</span>
        </div>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Score pills
    score_items = [
        ("Demand", scores["demand"]),
        ("Footfall", scores["footfall"]),
        ("Competition", scores["competition"]),
        ("Accessibility", scores["accessibility"]),
        ("Catchment", scores["catchment"]),
        ("Spending Power", scores["spending_power"]),
    ]
    pills = ""
    for label, s in score_items:
        col = "#1D9E75" if s >= 65 else "#BA7517" if s >= 45 else "#C0392B"
        pills += f"""
        <div style='flex:1;min-width:80px;background:#111;
                    border:1px solid #222;border-radius:8px;
                    padding:10px 8px;text-align:center'>
          <div style='font-size:20px;font-weight:700;color:{col}'>{s}</div>
          <div style='font-size:10px;color:#888;margin-top:2px'>{label}</div>
        </div>"""

    components.html(
        f"""
    <div style='display:flex;gap:8px;flex-wrap:wrap;
                font-family:sans-serif'>
      {pills}
    </div>
    """,
        height=80,
    )

    # Radar chart
    st.markdown("### Score Breakdown")
    col_left, col_chart, col_right = st.columns([1, 6, 1])
    with col_chart:
        cats = [
            "Demand",
            "Footfall",
            "Competition",
            "Accessibility",
            "Catchment",
            "Spending Power",
        ]
        vals = [
            scores["demand"],
            scores["footfall"],
            scores["competition"],
            scores["accessibility"],
            scores["catchment"],
            scores["spending_power"],
        ]
        fig = go.Figure(
            go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(29,158,117,0.15)",
                line=dict(color="#1D9E75", width=2),
                marker=dict(color="#1D9E75", size=7),
            )
        )
        fig.update_layout(
            polar=dict(
                bgcolor="#0d1f1a",
                radialaxis=dict(visible=True, range=[0, 100]),
                angularaxis=dict(tickfont=dict(size=12, color="#ccc")),
            ),
            showlegend=False,
            height=380,
            margin=dict(l=60, r=60, t=40, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Map
    st.markdown("### Location Map")
    col_left, col_map, col_right = st.columns([1, 10, 1])
    with col_map:
        m = folium.Map(location=[lat, lng], zoom_start=15, tiles="CartoDB positron")
        folium.CircleMarker(
            location=[lat, lng],
            radius=14,
            color="#0A2E26",
            fill=True,
            fill_color=vc,
            fill_opacity=0.9,
            popup=folium.Popup(f"<b>{result['address']}</b><br>Score: {total}/100", max_width=220),
        ).add_to(m)
        folium.Circle(location=[lat, lng], radius=500, color="#1D9E75", fill=True, fill_color="#1D9E75", fill_opacity=0.05).add_to(m)
        folium.Circle(location=[lat, lng], radius=1000, color="#BA7517", fill=False).add_to(m)
        st_folium(m, width="100%", height=400, returned_objects=[])

    # Explainability & competitors
    st.markdown("### Analysis Details")
    col_risk, col_explain = st.columns(2)
    with col_risk:
        st.markdown("**Risk Assessment**")
        risks = []
        if scores["competition"] < 30:
            risks.append("High competitor density within 500m")
        if scores["demand"] < 40:
            risks.append("Low residential population density")
        if scores["footfall"] < 40:
            risks.append("Few anchor stores within 500m")
        if scores["accessibility"] < 40:
            risks.append("Limited road connectivity")
        if risks:
            for r in risks:
                st.markdown(f"<div style='background:#1a0e0e;border-left:3px solid #C0392B;padding:8px 12px;border-radius:0 6px 6px 0;font-size:12px;color:#ccc;margin-bottom:6px'>! {r}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#0d1f1a;border-left:3px solid #1D9E75;padding:8px 12px;border-radius:0 6px 6px 0;font-size:12px;color:#9ecfc0'>No significant risk flags at this location</div>", unsafe_allow_html=True)

    with col_explain:
        st.markdown("**What we found**")
        raw = result.get("raw", {})

        def mini_row(label, value, note):
            st.markdown(f"<div style='border-bottom:1px solid #1a1a1a;padding:7px 0;margin-bottom:2px'><div style='display:flex;justify-content:space-between'><span style='font-size:11px;color:#888'>{label}</span><span style='font-size:13px;font-weight:700;color:white'>{value}</span></div><div style='font-size:10px;color:#555;margin-top:1px'>{note}</div></div>", unsafe_allow_html=True)

        method = raw.get("demand_method", "osm_buildings")
        if method == "census_2011":
            mini_row("Est. population within 1km", f"{raw.get('demand_population',0):,}", f"Census 2011 ward data · {raw.get('demand_households',0):,} households")
            wards = raw.get("demand_wards", [])
            if wards:
                ward_names = " · ".join(w["name"] for w in wards[:3])
                mini_row("Contributing wards", str(len(wards)), ward_names)
        else:
            mini_row("Residential buildings within 1km", f"{raw.get('demand_buildings',0):,}", "OpenStreetMap buildings (Census data unavailable)")
            mini_row("Footfall anchors", str(sum(raw.get("footfall_anchors", {}).values()) if raw.get("footfall_anchors") else 0), "supermarkets, hospitals, schools within 500m")
            mini_row("Competitors found", str(raw.get("competitor_count", 0)), "weighted by review count + rating")
            mini_row("Road intersections", str(raw.get("intersections", 0)), "within 300m drive network")
            mini_row("Commercial places", str(raw.get("catchment_places", 0)), "shops, cafes within 1km")
            spending = raw.get("spending_data", {})
            avg_p = spending.get("avg_price_level")
            mini_row("Avg price level", f"{avg_p}/4.0" if avg_p else "N/A", f"{spending.get('sample_size',0)} places sampled")

    if result.get("competitor_details"):
        st.markdown("### Nearby Competitors")
        competitors = sorted(result["competitor_details"], key=lambda x: x["strength"], reverse=True)[:8]
        col_left, col_comp, col_right = st.columns([1, 10, 1])
        with col_comp:
            for comp in competitors:
                strength = comp["strength"]
                bar_color2 = ("#C0392B" if strength > 0.6 else "#BA7517" if strength > 0.3 else "#1D9E75")
                bar_w = int(strength * 100)
                stars = "★" * int(round(comp["rating"])) + "☆" * (5 - int(round(comp["rating"])))
                rev_label = (f"{comp['reviews']:,} reviews" if comp["reviews"] > 0 else "No reviews")
                comp_name = comp["name"]
                label_text = "Strong" if strength > 0.6 else "Moderate" if strength > 0.3 else "Weak"
                html = (
                    "<div style='background:#111;border:1px solid #222;border-radius:8px;padding:10px 14px;margin-bottom:6px'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px'>"
                    f"<span style='font-size:13px;font-weight:600;color:white'>{comp_name}</span>"
                    f"<span style='font-size:11px;color:#888'>{stars} &nbsp;{rev_label}</span></div>"
                    "<div style='display:flex;align-items:center;gap:10px'>"
                    f"<div style='flex:1;background:#333;border-radius:4px;height:6px'>"
                    f"<div style='width:{bar_w}%;background:{bar_color2};height:6px;border-radius:4px'></div></div>"
                    f"<span style='font-size:11px;color:{bar_color2};min-width:80px;text-align:right'>{label_text} competitor</span>"
                    "</div></div>"
                )
                st.markdown(html, unsafe_allow_html=True)

    # PDF
    st.markdown("---")
    with st.spinner("Preparing PDF report..."):
        path = f"/tmp/{result['address'][:20].replace(' ','_')}_report.pdf"
        generate_report(result, path)
        with open(path, "rb") as f:
            pdf_bytes = f.read()
    st.download_button(label="Download PDF Report", data=pdf_bytes, file_name="sitescore_report.pdf", mime="application/pdf", use_container_width=True)
    st.caption("SiteScore Analytics · Gujarat · " "OpenStreetMap + Google Places API")
