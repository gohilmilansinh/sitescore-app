import streamlit as st


def render_header():

    st.markdown("""
    <style>

    .site-header {
        background: linear-gradient(90deg,#0A2E26,#005447);
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

    .subtitle {
        color: #9ecfc0;
        font-size: 14px;
        margin-top: 10px;
        margin-left: 18px;
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

    st.image(
        "assets/logo.png",
        width=280,
    )

    st.markdown(
        """
        <div class="subtitle">
            Data-driven retail location intelligence for Gujarat
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)