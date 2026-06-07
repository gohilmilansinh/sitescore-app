import streamlit as st

def render_header():
    st.markdown("""
    <style>
    .site-header {
        background: linear-gradient(90deg, #0A2E26, #005447);
        border-radius: 24px;
        padding: 22px 35px 22px 35px;
        margin-bottom: 30px;
    }
    .header-label {
        color: #9ecfc0;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }
    .header-logo {
        width: 280px;
        height: auto;
        display: block;
        margin-bottom: 10px;
    }
    .subtitle {
        color: #9ecfc0;
        font-size: 14px;
        margin-top: 10px;
        margin-left: 18px;   /* matches original alignment */
    }
    </style>

    <div class="site-header">
        <div class="header-label">RETAIL LOCATION INTELLIGENCE</div>
        <img src="assets/logo.png" class="header-logo" alt="SiteIQ">
        <div class="subtitle">Data-driven retail location intelligence for Gujarat</div>
    </div>
    """, unsafe_allow_html=True)