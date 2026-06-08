from __future__ import annotations

from typing import Any, Dict

import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from report import generate_report
from benchmarks import get_category_context
import os
from roi_calculator import calculate_roi
from score_explainer import explain_scores


def render_score_breakdown(result: Dict[str, Any], brand_type: str) -> None:
    scores = result.get("scores", {})
    total = result["total_score"]
    verdict = result["verdict"]
    lat, lng = result["lat"], result["lng"]
    vc = (
        "#1D9E75"
        if verdict == "Strong"
        else "#BA7517" if verdict == "Moderate" else "#C0392B"
    )

    benchmark = get_category_context(total, brand_type)
    stats = benchmark["stats"]
    percentile = benchmark["percentile"]
    bar_color = (
        "#1D9E75" if percentile >= 65 else "#BA7517" if percentile >= 40 else "#C0392B"
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
            popup=folium.Popup(
                f"<b>{result['address']}</b><br>Score: {total}/100", max_width=220
            ),
        ).add_to(m)
        folium.Circle(
            location=[lat, lng],
            radius=500,
            color="#1D9E75",
            fill=True,
            fill_color="#1D9E75",
            fill_opacity=0.05,
        ).add_to(m)
        folium.Circle(
            location=[lat, lng], radius=1000, color="#BA7517", fill=False
        ).add_to(m)
        st_folium(m, width="100%", height=400, returned_objects=[])

    # ── Score Explainability ──────────────────────────────
    st.markdown("### Why This Score?")

    explanation = explain_scores(
        scores=scores,
        brand_type=brand_type,
        total_score=total,
    )

    # Narrative summary
    if explanation["narrative"]:
        st.markdown(
            f"<div style='background:#111;border-left:3px solid #1D9E75;"
            f"padding:12px 16px;border-radius:0 8px 8px 0;"
            f"font-size:13px;color:#ccc;margin-bottom:16px'>"
            f"{explanation['narrative']}</div>",
            unsafe_allow_html=True,
        )

    # Contribution table
    contribs = explanation["contributions"]

    # Build HTML table
    rows_html = ""
    for c in contribs:
        score_col = (
            "#1D9E75" if c["score"] >= 65
            else "#BA7517" if c["score"] >= 45
            else "#C0392B"
        )
        delta_col = "#1D9E75" if c["delta"] >= 0 else "#C0392B"
        delta_str = (
            f"+{c['delta']}" if c["delta"] >= 0
            else str(c["delta"])
        )
        vs_avg_str = (
            f"+{c['vs_avg']}" if c["vs_avg"] >= 0
            else str(c["vs_avg"])
        )
        vs_avg_col = "#1D9E75" if c["vs_avg"] >= 0 else "#C0392B"

        # Bar showing score vs average
        bar_score_w = int(c["score"])
        bar_avg_w   = int(c["avg_score"])

        rows_html += f"""
        <tr>
          <td style='padding:10px 12px;color:white;
                     font-weight:500;min-width:130px'>
            {c['label']}
          </td>
          <td style='padding:10px 12px;text-align:center;
                     color:{score_col};font-weight:700;
                     font-size:15px'>
            {c['score']}
          </td>
          <td style='padding:10px 24px;min-width:160px'>
            <div style='position:relative;height:8px;
                        background:#222;border-radius:4px'>
              <div style='position:absolute;left:0;top:0;
                          width:{bar_avg_w}%;height:8px;
                          background:#333;border-radius:4px'></div>
              <div style='position:absolute;left:0;top:0;
                          width:{bar_score_w}%;height:8px;
                          background:{score_col};border-radius:4px;
                          opacity:0.85'></div>
              <div style='position:absolute;left:{bar_avg_w}%;
                          top:-3px;width:2px;height:14px;
                          background:#888'></div>
            </div>
            <div style='font-size:9px;color:#555;margin-top:3px'>
              avg {c['avg_score']}
            </div>
          </td>
          <td style='padding:10px 12px;text-align:center;
                     color:#888;font-size:12px'>
            {c['weight_pct']}%
          </td>
          <td style='padding:10px 12px;text-align:center;
                     color:{delta_col};font-weight:600'>
            {delta_str}
          </td>
          <td style='padding:10px 12px;text-align:center;
                     color:{vs_avg_col};font-size:12px'>
            {vs_avg_str} vs avg
          </td>
          <td style='padding:10px 12px;font-size:11px;
                     color:#666;max-width:180px'>
            {c['insight']}
          </td>
        </tr>"""

    explainer_html = f"""
    <!DOCTYPE html><html><head>
    <style>
      body{{margin:0;background:transparent;font-family:sans-serif}}
      table{{width:100%;border-collapse:collapse;font-size:13px}}
      thead tr{{background:#0A2E26}}
      th{{padding:10px 12px;color:#9ecfc0;font-size:10px;
          letter-spacing:.5px;text-align:center;font-weight:600}}
      th:first-child{{text-align:left}}
      tbody tr{{border-bottom:1px solid #1a1a1a}}
      tbody tr:hover{{background:#0d1f1a}}
    </style></head><body>
    <table>
      <thead><tr>
        <th style='text-align:left'>VARIABLE</th>
        <th>SCORE</th>
        <th style='text-align:left;padding-left:24px'>
          SCORE vs AVERAGE
        </th>
        <th>WEIGHT</th>
        <th>CONTRIBUTION</th>
        <th>VS AVG</th>
        <th style='text-align:left'>INSIGHT</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </body></html>"""

    components.html(
        explainer_html,
        height=60 + len(contribs) * 58
    )

    # Risk + boost highlights
    col_boost, col_drag = st.columns(2)

    with col_boost:
        if explanation["biggest_boost"]:
            b = explanation["biggest_boost"]
            st.markdown(
                f"<div style='background:#0d1f1a;border:1px solid #1D9E75;"
                f"border-radius:8px;padding:14px'>"
                f"<div style='font-size:10px;color:#9ecfc0;"
                f"letter-spacing:1px;margin-bottom:4px'>"
                f"BIGGEST STRENGTH</div>"
                f"<div style='font-size:16px;font-weight:700;"
                f"color:#1D9E75'>{b['label']}</div>"
                f"<div style='font-size:13px;color:#ccc;margin-top:4px'>"
                f"Score {b['score']} — "
                f"{abs(b['vs_avg']):.0f} pts above average</div>"
                f"<div style='font-size:11px;color:#888;margin-top:6px'>"
                f"{b['insight']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with col_drag:
        if explanation["biggest_drag"]:
            d = explanation["biggest_drag"]
            st.markdown(
                f"<div style='background:#1a0e0e;border:1px solid #C0392B;"
                f"border-radius:8px;padding:14px'>"
                f"<div style='font-size:10px;color:#e08080;"
                f"letter-spacing:1px;margin-bottom:4px'>"
                f"BIGGEST DRAG</div>"
                f"<div style='font-size:16px;font-weight:700;"
                f"color:#C0392B'>{d['label']}</div>"
                f"<div style='font-size:13px;color:#ccc;margin-top:4px'>"
                f"Score {d['score']} — "
                f"{abs(d['vs_avg']):.0f} pts below average</div>"
                f"<div style='font-size:11px;color:#888;margin-top:6px'>"
                f"{d['insight']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Risk assessment below
    st.markdown("### Risk Assessment")
    risks = []
    if scores.get("competition", 100)   < 30:
        risks.append("High competitor density within 500m — market may be saturated")
    if scores.get("demand", 100)        < 40:
        risks.append("Low residential population density — walk-in base limited")
    if scores.get("footfall", 100)      < 40:
        risks.append("Few anchor stores within 500m")
    if scores.get("accessibility", 100) < 40:
        risks.append("Limited road connectivity")

    if risks:
        for r in risks:
            st.markdown(
                f"<div style='background:#1a0e0e;border-left:3px solid "
                f"#C0392B;padding:8px 12px;border-radius:0 6px 6px 0;"
                f"font-size:12px;color:#ccc;margin-bottom:6px'>"
                f"! {r}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div style='background:#0d1f1a;border-left:3px solid #1D9E75;"
            "padding:8px 12px;border-radius:0 6px 6px 0;"
            "font-size:12px;color:#9ecfc0'>"
            "No significant risk flags at this location</div>",
            unsafe_allow_html=True,
        )

    # ── ROI Calculator ────────────────────────────────────
    st.markdown("### ROI Analysis")
    st.markdown(
        "<div style='font-size:12px;color:#888;margin-bottom:12px'>"
        "Enter monthly rent to calculate return on investment. "
        "Revenue estimates use Gujarat market benchmarks.</div>",
        unsafe_allow_html=True,
    )

    col_rent, col_setup = st.columns(2)
    with col_rent:
        monthly_rent = st.number_input(
            "Monthly Rent (Rs.)",
            min_value=0,
            max_value=2000000,
            value=0,
            step=5000,
            help="Enter the monthly rent quoted for this site",
            key=f"rent_{result['address'][:15]}",
        )
    with col_setup:
        setup_cost = st.number_input(
            "Setup / Fit-out Cost (Rs.)",
            min_value=0,
            max_value=10000000,
            value=0,
            step=50000,
            help="One-time setup cost — leave 0 to use category benchmark",
            key=f"setup_{result['address'][:15]}",
        )

    if monthly_rent > 0:
        roi = calculate_roi(
            total_score=result["total_score"],
            monthly_rent=monthly_rent,
            brand_type=result.get("brand_type", "restaurant"),
            setup_cost=setup_cost if setup_cost > 0 else None,
        )

        # ROI summary banner
        st.markdown(f"""
        <div style='background:#0A2E26;border-radius:12px;
                    padding:20px 24px;margin:12px 0'>
          <div style='display:flex;justify-content:space-between;
                      align-items:center;flex-wrap:wrap;gap:12px'>
            <div>
              <div style='font-size:10px;color:#9ecfc0;
                          letter-spacing:1px'>COMBINED SCORE</div>
              <div style='font-size:42px;font-weight:700;
                          color:{roi["verdict_color"]};line-height:1'>
                {roi["combined_score"]}</div>
              <div style='font-size:11px;color:#9ecfc0'>
                Location {roi["location_score"]} × 70% + 
                ROI {roi["roi_score"]} × 30%</div>
            </div>
            <div style='text-align:center'>
              <div style='font-size:16px;font-weight:700;
                          color:{roi["verdict_color"]}'>
                {roi["verdict"]}</div>
              <div style='font-size:11px;color:#9ecfc0;margin-top:4px'>
                {roi["recommendation"]}</div>
            </div>
            <div style='text-align:right'>
              <div style='font-size:10px;color:#9ecfc0'>RENT RATING</div>
              <div style='font-size:20px;font-weight:700;
                          color:{roi["rent_color"]}'>
                {roi["rent_label"]}</div>
              <div style='font-size:11px;color:#9ecfc0'>
                {roi["rent_pct_of_revenue"]}% of est. revenue</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        def fmt_inr(amount):
            if amount >= 100000:
                return f"Rs. {amount/100000:.1f}L"
            return f"Rs. {amount:,.0f}"

        col1.metric(
            "Est. Monthly Revenue",
            fmt_inr(roi["est_monthly_revenue"]),
            help="Based on site score and Gujarat category benchmarks"
        )
        col2.metric(
            "Monthly Profit",
            fmt_inr(roi["monthly_profit"]),
            delta=fmt_inr(roi["monthly_profit"]),
            delta_color="normal"
        )
        col3.metric(
            "Annual Profit",
            fmt_inr(roi["annual_profit"]),
        )
        col4.metric(
            "Payback Period",
            f"{roi['payback_months']:.0f} months"
            if roi["payback_months"] < 999
            else "Not viable",
            help="Months to recover total setup cost"
        )

        # Rent sensitivity table
        st.markdown("**Rent Sensitivity — what different rent levels mean**")

        rent_levels = [
            monthly_rent * 0.6,
            monthly_rent * 0.8,
            monthly_rent,
            monthly_rent * 1.2,
            monthly_rent * 1.4,
        ]
        labels = ["-40%", "-20%", "Current", "+20%", "+40%"]

        rows = ""
        for label, rent in zip(labels, rent_levels):
            r = calculate_roi(
                result["total_score"], rent,
                result.get("brand_type", "restaurant"),
                setup_cost if setup_cost > 0 else None
            )
            is_current = label == "Current"
            bg = "#1a3a2a" if is_current else "transparent"
            rows += (
                f"<tr style='background:{bg}'>"
                f"<td style='padding:8px 12px;color:#9ecfc0;"
                f"font-weight:{'700' if is_current else '400'}'>"
                f"{label}</td>"
                f"<td style='padding:8px 12px;color:white'>"
                f"Rs. {rent:,.0f}</td>"
                f"<td style='padding:8px 12px;"
                f"color:{r['rent_color']};font-weight:600'>"
                f"{r['rent_label']}</td>"
                f"<td style='padding:8px 12px;color:white'>"
                f"Rs. {r['monthly_profit']:,.0f}</td>"
                f"<td style='padding:8px 12px;color:white'>"
                f"{r['payback_months']:.0f} mo"
                if r['payback_months'] < 999
                else "<td style='padding:8px 12px;color:#C0392B'>Not viable"
                f"</td></tr>"
            )

        sensitivity_html = f"""
        <!DOCTYPE html><html><head>
        <style>
          body{{margin:0;background:transparent;font-family:sans-serif}}
          table{{width:100%;border-collapse:collapse;font-size:13px}}
          th{{padding:10px 12px;background:#0A2E26;color:#9ecfc0;
              font-size:11px;text-align:left;letter-spacing:.5px}}
          tr{{border-bottom:1px solid #1a2a1a}}
        </style></head><body>
        <table>
          <thead><tr>
            <th>SCENARIO</th><th>MONTHLY RENT</th>
            <th>RATING</th><th>MONTHLY PROFIT</th>
            <th>PAYBACK</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table></body></html>"""

        components.html(sensitivity_html, height=240)

        # Store ROI in result for PDF
        result["roi"] = roi

    else:
        st.info(
            "Enter monthly rent above to see ROI analysis, "
            "profit estimates, and payback period."
        )

    # PDF
    st.markdown("---")
    with st.spinner("Preparing PDF report..."):
        import tempfile
        safe_name = "".join(
            c for c in result["address"][:20]
            if c.isalnum() or c in (" ", "-", "_")
        ).strip().replace(" ", "_")
        path = os.path.join(tempfile.gettempdir(),
                            f"{safe_name}_report.pdf")
        generate_report(result, path)
        with open(path, "rb") as f:
            pdf_bytes = f.read()
    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name="SiteIQ_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    st.caption("SiteScore Analytics · Gujarat · " "OpenStreetMap + Google Places API")
