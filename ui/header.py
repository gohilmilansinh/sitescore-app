import streamlit as st


def render_header() -> None:
    # Header styling
    st.markdown(
        """
        <style>
        .site-header {
            background: #0A2E26;
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 24px;
        }

        .header-label {
            color: #9ecfc0;
            font-size: 11px;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }

        .header-title {
            color: white;
            font-size: 30px;
            font-weight: 700;
            margin: 0;
            padding: 0;
        }

        .header-subtitle {
            color: #9ecfc0;
            font-size: 14px;
            margin-top: 4px;
        }

        .score-box {
            background: #0A2E26;
            border-radius: 12px;
            padding: 28px;
            text-align: center;
            color: white;
        }

        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 16px;
            border: 1px solid #EEEEEE;
            text-align: center;
            margin-bottom: 10px;
        }

        .metric-val {
            font-size: 28px;
            font-weight: 700;
        }

        .metric-lbl {
            font-size: 11px;
            color: #888;
            margin-top: 2px;
        }

        .risk-box {
            background: #FFF8F0;
            border-left: 4px solid #BA7517;
            padding: 10px 14px;
            border-radius: 0 8px 8px 0;
            font-size: 13px;
            color: #555;
            margin-bottom: 8px;
        }

        .ok-box {
            background: #F0FAF6;
            border-left: 4px solid #1D9E75;
            padding: 10px 14px;
            border-radius: 0 8px 8px 0;
            font-size: 13px;
            color: #0A6E50;
            margin-bottom: 8px;
        }

        .rank-1 {
            background: #F0FAF6;
            border: 2px solid #1D9E75;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 10px;
        }

        .rank-2 {
            background: #FFFDF0;
            border: 2px solid #BA7517;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 10px;
        }

        .rank-3 {
            background: #FFF5F5;
            border: 2px solid #C0392B;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 10px;
        }

        .rank-label {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }

        .rank-score {
            font-size: 36px;
            font-weight: 700;
            line-height: 1;
        }

        .rank-addr {
            font-size: 11px;
            color: #666;
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Start header container
    st.markdown("<div class='site-header'>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class='header-label'>
            RETAIL LOCATION INTELLIGENCE
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 12])

    with col1:
        st.image("assets/logo.png", width=60)

    with col2:
        st.markdown(
            """
            <div class='header-title'>
                SiteIQ
            </div>

            <div class='header-subtitle'>
                Data-driven retail location intelligence for Gujarat
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

