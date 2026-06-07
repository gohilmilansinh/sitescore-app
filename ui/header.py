import streamlit as st
import base64


def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()



def render_header():

    st.markdown("""
        <style>
        .site-header{
            background: linear-gradient(90deg,#0A2E26,#004538);
            border-radius:18px;
            padding:30px 40px;
            margin-bottom:24px;
        }

        .header-label{
            color:#9ecfc0;
            font-size:11px;
            letter-spacing:3px;
            margin-bottom:18px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<div class="site-header">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="header-label">
            RETAIL LOCATION INTELLIGENCE
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1.5, 6])

    with col1:
        st.image("assets/logo.png", width=160)

    with col2:
        st.markdown(
            """
            <h1 style="
                color:white;
                margin-bottom:0;
                margin-top:15px;
                font-size:42px;
            ">
                SiteIQ
            </h1>

            <p style="
                color:#9ecfc0;
                font-size:18px;
                margin-top:6px;
            ">
                Data-driven retail location intelligence for Gujarat
            </p>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)