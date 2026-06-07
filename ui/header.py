import streamlit as st
import base64


def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


import streamlit as st


def render_header():

    st.markdown("""
    <style>
    .site-header {
        background: linear-gradient(90deg,#0A2E26,#004538);
        border-radius: 18px;
        padding: 30px;
        margin-bottom: 25px;
    }

    .header-label {
        color:#9ecfc0;
        font-size:11px;
        letter-spacing:3px;
        margin-bottom:10px;
    }

    .header-title {
        color:white;
        font-size:36px;
        font-weight:700;
        margin:0;
    }

    .header-subtitle {
        color:#9ecfc0;
        font-size:15px;
        margin-top:4px;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():

        st.markdown(
            """
            <div class="site-header">
            <div class="header-label">
            RETAIL LOCATION INTELLIGENCE
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([2, 8])

        with col1:
            st.image("assets/logo.png", width=180)

        with col2:
            st.markdown(
                """
                <div class="header-title">
                    SiteIQ
                </div>

                <div class="header-subtitle">
                    Data-driven retail location intelligence for Gujarat
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)