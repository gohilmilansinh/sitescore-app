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
    st.markdown(
            """
        <style>
        .site-header {
            background: linear-gradient(90deg,#0A2E26,#003D35);
            border-radius: 18px;
            padding: 30px 40px;
            margin-bottom: 24px;
        }

        .logo-row {
            display:flex;
            align-items:center;
            gap:18px;
        }

        .logo-row img {
            width:110px;
            height:auto;
        }

        .header-label {
            color:#9ecfc0;
            font-size:11px;
            letter-spacing:3px;
            margin-bottom:12px;
        }

        .header-title {
            color:white;
            font-size:42px;
            font-weight:700;
            line-height:1;
        }

        .header-subtitle {
            color:#9ecfc0;
            font-size:16px;
            margin-top:8px;
        }
        </style>

        <div class="site-header">

            <div class="header-label">
                RETAIL LOCATION INTELLIGENCE
            </div>

            <div class="logo-row">

                <img src="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/sitelogo.png">

                <div>
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
            unsafe_allow_html=True
        )

