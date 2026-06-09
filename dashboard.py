from __future__ import annotations

from typing import Any, Dict, List, Tuple
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
from persistence import load_history, is_db_connected


def _score_color(score: float) -> str:
    if score >= 65:
        return "#1D9E75"
    elif score >= 45:
        return "#BA7517"
    return "#C0392B"


def _verdict_icon(verdict: str) -> str:
    return {"Strong": "✅", "Moderate": "⚠️", "Weak": "❌"}.get(
        verdict, "—"
    )


def render_dashboard() -> None:
    history = load_history()

    # ── Header ────────────────────────────────────────────
    db_status = is_db_connected()
    status_color = "#1D9E75" if db_status else "#BA7517"
    status_text  = (
        "Database connected — history is permanent"
        if db_status
        else "Local storage — add Supabase for permanent history"
    )

    st.markdown(
        f"<div style='display:inline-flex;align-items:center;"
        f"gap:6px;background:#0d1f1a;border:1px solid {status_color};"
        f"padding:4px 14px;border-radius:20px;font-size:11px;"
        f"color:{status_color};margin-bottom:20px'>"
        f"<span style='width:6px;height:6px;"
        f"background:{status_color};border-radius:50%;"
        f"display:inline-block'></span>"
        f"{status_text}</div>",
        unsafe_allow_html=True,
    )

    if not history:
        st.markdown(
            "<div style='background:#111;border:1px solid #222;"
            "border-radius:12px;padding:48px;text-align:center;"
            "color:#888;margin-top:16px'>"
            "<div style='font-size:40px;margin-bottom:16px'>📊</div>"
            "<div style='font-size:16px;font-weight:500;"
            "margin-bottom:8px'>No sites scored yet</div>"
            "<div style='font-size:13px'>"
            "Score your first site in Single Site mode "
            "to see your dashboard.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    scored = [
        h for h in history
        if h.get("total_score", 0) > 0
    ]
    if not scored:
        st.info("No scored sites found.")
        return

    scores_list = [h["total_score"] for h in scored]
    avg_score   = round(sum(scores_list) / len(scores_list), 1)
    best        = max(scored, key=lambda x: x["total_score"])
    worst       = min(scored, key=lambda x: x["total_score"])
    strong_ct   = sum(1 for h in scored if h["verdict"] == "Strong")
    moderate_ct = sum(
        1 for h in scored if h["verdict"] == "Moderate")
    weak_ct     = sum(1 for h in scored if h["verdict"] == "Weak")

    # ── KPI row ───────────────────────────────────────────
    st.markdown("### Pipeline Overview")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Sites",    len(scored))
    c2.metric("Average Score",  avg_score)
    c3.metric("Strong Sites",   strong_ct)
    c4.metric("Moderate Sites", moderate_ct)
    c5.metric("Weak Sites",     weak_ct)
    c6.metric("Best Score",     best["total_score"])

    st.markdown("---")

    # ── Charts row ────────────────────────────────────────
    col_dist, col_radar = st.columns([1, 1])

    with col_dist:
        st.markdown("**Score Distribution**")
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=scores_list,
            nbinsx=10,
            marker_color="#1D9E75",
            marker_line_color="#0A2E26",
            marker_line_width=1,
            opacity=0.85,
            name="Sites",
        ))
        fig_dist.add_vline(
            x=avg_score,
            line_dash="dash",
            line_color="#BA7517",
            annotation_text=f"Avg {avg_score}",
            annotation_position="top right",
            annotation_font_color="#BA7517",
        )
        fig_dist.update_layout(
            height=260,
            plot_bgcolor="#0d1f1a",
            paper_bgcolor="transparent",
            xaxis=dict(
                title="Score",
                range=[0, 100],
                gridcolor="#1a3a2a",
                color="#9ecfc0",
            ),
            yaxis=dict(
                title="Sites",
                gridcolor="#1a3a2a",
                color="#9ecfc0",
            ),
            margin=dict(l=10, r=10, t=10, b=40),
            showlegend=False,
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_radar:
        st.markdown("**Average Variable Scores**")
        variable_keys = [
            "demand", "footfall", "competition",
            "accessibility", "catchment", "spending_power",
        ]
        variable_labels = [
            "Demand", "Footfall", "Competition",
            "Accessibility", "Catchment", "Spending",
        ]

        avg_vars = []
        for key in variable_keys:
            vals = [
                h["scores"].get(key, 0)
                for h in scored
                if h.get("scores")
            ]
            avg_vars.append(
                round(sum(vals) / len(vals), 1)
                if vals else 0
            )

        fig_radar = go.Figure(go.Scatterpolar(
            r=avg_vars + [avg_vars[0]],
            theta=variable_labels + [variable_labels[0]],
            fill="toself",
            fillcolor="rgba(29,158,117,0.15)",
            line=dict(color="#1D9E75", width=2),
            marker=dict(color="#1D9E75", size=6),
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="#0d1f1a",
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=8, color="#666"),
                    gridcolor="#1a3a2a",
                ),
                angularaxis=dict(
                    tickfont=dict(size=10, color="#9ecfc0")),
            ),
            showlegend=False,
            height=260,
            margin=dict(l=30, r=30, t=20, b=20),
            paper_bgcolor="transparent",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")

    # ── Top sites ─────────────────────────────────────────
    col_top, col_watch = st.columns(2)

    with col_top:
        st.markdown("**Top Opportunities**")
        top5 = sorted(
            scored,
            key=lambda x: x["total_score"],
            reverse=True,
        )[:5]

        for i, site in enumerate(top5):
            sc  = site["total_score"]
            col = _score_color(sc)
            icon = _verdict_icon(site["verdict"])
            st.markdown(
                f"<div style='display:flex;align-items:center;"
                f"gap:12px;padding:10px 14px;margin-bottom:6px;"
                f"background:#111;border-radius:8px;"
                f"border-left:3px solid {col}'>"
                f"<div style='font-size:13px;font-weight:700;"
                f"color:#9ecfc0;min-width:20px'>#{i+1}</div>"
                f"<div style='flex:1'>"
                f"<div style='font-size:13px;color:white;"
                f"font-weight:500'>"
                f"{site['address'][:45]}</div>"
                f"<div style='font-size:11px;color:#666;"
                f"margin-top:2px'>"
                f"{site.get('brand_type','').title()} · "
                f"{site.get('timestamp','')[:12]}</div>"
                f"</div>"
                f"<div style='text-align:right'>"
                f"<div style='font-size:22px;font-weight:700;"
                f"color:{col}'>{sc}</div>"
                f"<div style='font-size:10px;color:{col}'>"
                f"{icon} {site['verdict']}</div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with col_watch:
        st.markdown("**Sites Needing Attention**")
        watchlist = [
            h for h in scored
            if h["total_score"] < 65 or
            h["scores"].get("competition", 100) < 30 or
            h["scores"].get("demand", 100) < 40
        ]
        watchlist = sorted(
            watchlist,
            key=lambda x: x["total_score"],
        )[:5]

        if not watchlist:
            st.markdown(
                "<div style='background:#0d1f1a;"
                "border-radius:8px;padding:16px;"
                "color:#9ecfc0;font-size:13px'>"
                "✅ All scored sites look healthy."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            for site in watchlist:
                sc   = site["total_score"]
                col  = _score_color(sc)
                risks = []
                if site["scores"].get("competition", 100) < 30:
                    risks.append("High competition")
                if site["scores"].get("demand", 100) < 40:
                    risks.append("Low demand")
                if site["scores"].get("footfall", 100) < 40:
                    risks.append("Low footfall")
                if sc < 45:
                    risks.append("Weak overall score")

                risk_str = " · ".join(risks[:2])
                st.markdown(
                    f"<div style='display:flex;align-items:center;"
                    f"gap:12px;padding:10px 14px;margin-bottom:6px;"
                    f"background:#1a0e0e;border-radius:8px;"
                    f"border-left:3px solid {col}'>"
                    f"<div style='flex:1'>"
                    f"<div style='font-size:13px;color:white;"
                    f"font-weight:500'>"
                    f"{site['address'][:40]}</div>"
                    f"<div style='font-size:11px;color:#C0392B;"
                    f"margin-top:2px'>{risk_str}</div>"
                    f"</div>"
                    f"<div style='font-size:20px;font-weight:700;"
                    f"color:{col}'>{sc}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ── Brand type breakdown ──────────────────────────────
    st.markdown("**Pipeline by Brand Type**")
    brand_counts: Dict[str, Dict] = {}
    for site in scored:
        bt = site.get("brand_type", "restaurant")
        if bt not in brand_counts:
            brand_counts[bt] = {"count": 0, "scores": []}
        brand_counts[bt]["count"] += 1
        brand_counts[bt]["scores"].append(site["total_score"])

    if len(brand_counts) > 1:
        bt_labels = list(brand_counts.keys())
        bt_counts = [brand_counts[bt]["count"]
                     for bt in bt_labels]
        bt_avgs   = [
            round(sum(brand_counts[bt]["scores"]) /
                  len(brand_counts[bt]["scores"]), 1)
            for bt in bt_labels
        ]

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            fig_pie = go.Figure(go.Pie(
                labels=bt_labels,
                values=bt_counts,
                hole=0.5,
                marker_colors=[
                    "#1D9E75", "#BA7517", "#185FA5",
                    "#8B5CF6", "#E67E22",
                ],
                textfont_size=12,
            ))
            fig_pie.update_layout(
                height=220,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="transparent",
                showlegend=True,
                legend=dict(
                    font=dict(color="#9ecfc0", size=11)),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b2:
            for bt, avg in zip(bt_labels, bt_avgs):
                col = _score_color(avg)
                st.markdown(
                    f"<div style='display:flex;"
                    f"justify-content:space-between;"
                    f"align-items:center;padding:8px 12px;"
                    f"margin-bottom:6px;background:#111;"
                    f"border-radius:6px'>"
                    f"<div style='font-size:13px;color:white;"
                    f"text-transform:capitalize'>{bt}</div>"
                    f"<div style='text-align:right'>"
                    f"<span style='font-size:16px;font-weight:700;"
                    f"color:{col}'>{avg}</span>"
                    f"<span style='font-size:11px;color:#666;"
                    f"margin-left:6px'>avg</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ── Score trend over time ─────────────────────────────
    if len(scored) >= 3:
        st.markdown("**Score Trend — Recent Activity**")
        recent = list(reversed(scored[:20]))
        labels = [
            h["address"].split(",")[0][:20]
            for h in recent
        ]
        values = [h["total_score"] for h in recent]
        cols_trend = [_score_color(v) for v in values]

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=list(range(len(recent))),
            y=values,
            mode="lines+markers",
            line=dict(color="#1D9E75", width=2),
            marker=dict(
                color=cols_trend,
                size=10,
                line=dict(color="#0A2E26", width=2),
            ),
            text=labels,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Score: %{y}<extra></extra>"
            ),
        ))
        fig_trend.add_hline(
            y=65,
            line_dash="dash",
            line_color="#1D9E75",
            opacity=0.4,
            annotation_text="Strong threshold",
            annotation_font_color="#1D9E75",
            annotation_font_size=10,
        )
        fig_trend.add_hline(
            y=45,
            line_dash="dash",
            line_color="#BA7517",
            opacity=0.4,
            annotation_text="Moderate threshold",
            annotation_font_color="#BA7517",
            annotation_font_size=10,
        )
        fig_trend.update_layout(
            height=280,
            plot_bgcolor="#0d1f1a",
            paper_bgcolor="transparent",
            xaxis=dict(
                tickvals=list(range(len(recent))),
                ticktext=labels,
                tickangle=-35,
                tickfont=dict(size=9, color="#666"),
                gridcolor="#1a3a2a",
            ),
            yaxis=dict(
                range=[0, 105],
                gridcolor="#1a3a2a",
                color="#9ecfc0",
                title="Score",
            ),
            margin=dict(l=10, r=10, t=20, b=80),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.caption(
        "SiteIQ Analytics · Dashboard · "
        "Showing last 50 scored sites"
    )