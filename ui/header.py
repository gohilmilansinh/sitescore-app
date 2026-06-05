import streamlit as st


def render_header() -> None:
    st.markdown(
        """
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
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
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
""",
        unsafe_allow_html=True,
    )
