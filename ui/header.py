import streamlit as st
import base64


def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def render_header():

    logo = image_to_base64("assets/logo.png")

    st.markdown(
        f"""
<style>

.site-header {{
    background: linear-gradient(90deg,#0A2E26,#004538);
    border-radius: 18px;
    padding: 28px 36px;
    margin-bottom: 28px;
}}

.header-label {{
    color: #9ecfc0;
    font-size: 11px;
    letter-spacing: 3px;
    margin-bottom: 18px;
}}

.logo-container {{
    display: flex;
    align-items: center;
    gap: 20px;
}}

.logo-container img {{
    width: 220px;
    height: auto;
}}

.header-text {{
    display: flex;
    flex-direction: column;
}}

.header-title {{
    color: white;
    font-size: 38px;
    font-weight: 700;
    line-height: 1.1;
}}

.header-subtitle {{
    color: #9ecfc0;
    font-size: 15px;
    margin-top: 8px;
}}

</style>

<div class="site-header">

    <div class="header-label">
        RETAIL LOCATION INTELLIGENCE
    </div>

    <div class="logo-container">

        <img src="data:image/png;base64,{logo}">

        <div class="header-text">

            <div class="header-title">
                SiteIQ
            </div>

            <div class="header-subtitle">
                Data-driven retail location intelligence for Gujarat
            </div>

        </div>

    </div>

</div>
""",
        unsafe_allow_html=True,
    )

