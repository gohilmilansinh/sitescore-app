from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

def generate_report(result, output_path="site_report.pdf"):
    scores  = result["scores"]
    total   = result["total_score"]
    W, H    = A4  # 595 x 842 pts

    # ── Colours ──────────────────────────────────────────────
    C_GREEN  = colors.HexColor("#1D9E75")
    C_DARK   = colors.HexColor("#0A2E26")
    C_AMBER  = colors.HexColor("#BA7517")
    C_RED    = colors.HexColor("#C0392B")
    C_LGREY  = colors.HexColor("#F5F5F5")
    C_GREY   = colors.HexColor("#888888")
    C_LTGRN  = colors.HexColor("#F0FAF6")
    C_WHITE  = colors.white
    C_LINE   = colors.HexColor("#EEEEEE")

    score_color = C_GREEN if total >= 65 else C_AMBER if total >= 45 else C_RED
    verdict     = "STRONG SITE"   if total >= 65 else "MODERATE SITE" if total >= 45 else "WEAK SITE"
    recommend   = "Proceed to lease negotiation" if total >= 65 else \
                  "Address risk flags before committing" if total >= 45 else \
                  "Seek alternative locations"

    LM, RM = 18*mm, 18*mm          # left / right margin
    CW = W - LM - RM               # content width  (~159mm)

    c = canvas.Canvas(output_path, pagesize=A4)

    # ── helpers ──────────────────────────────────────────────
    def text(x, y, txt, size=11, bold=False, color=colors.black, align="left"):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.setFillColor(color)
        if align == "center": c.drawCentredString(x, y, str(txt))
        elif align == "right": c.drawRightString(x, y, str(txt))
        else: c.drawString(x, y, str(txt))

    def rect(x, y, w, h, fill=C_LGREY, stroke=None, radius=3):
        c.setFillColor(fill)
        if stroke:
            c.setStrokeColor(stroke)
            c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
        else:
            c.setStrokeColor(fill)
            c.roundRect(x, y, w, h, radius, fill=1, stroke=0)

    def hline(y, color=C_LINE, x0=None, x1=None, thickness=0.5):
        c.setStrokeColor(color)
        c.setLineWidth(thickness)
        c.line(x0 or LM, y, x1 or (W-RM), y)

    def score_bar(x, y, w, h, score):
        col = C_GREEN if score >= 65 else C_AMBER if score >= 45 else C_RED
        # background
        c.setFillColor(C_LINE)
        c.setStrokeColor(C_LINE)
        c.roundRect(x, y, w, h, 2, fill=1, stroke=0)
        # fill
        filled = (score / 100) * w
        if filled > 0:
            c.setFillColor(col)
            c.roundRect(x, y, filled, h, 2, fill=1, stroke=0)

    def section_header(y, title):
        rect(LM, y-4, CW, 22, fill=C_LTGRN)
        c.setFillColor(C_GREEN)
        c.setStrokeColor(C_GREEN)
        c.setLineWidth(3)
        c.line(LM, y-4, LM, y+18)
        text(LM+10, y+4, title, size=12, bold=True, color=C_DARK)
        return y - 34

    def kv_row(y, label, value):
        text(LM, y, label, size=10, color=C_GREY)
        text(W-RM, y, value, size=10, bold=True, color=C_DARK, align="right")
        hline(y-6)
        return y - 20

    def wrap_text(txt, max_width, size=10):
        """Split text into lines that fit within max_width."""
        c.setFont("Helvetica", size)
        words = txt.split()
        lines, line = [], ""
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, "Helvetica", size) <= max_width:
                line = test
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
        return lines

    def body_text(x, y, txt, size=10, color=colors.HexColor("#444444"), max_width=None):
        mw = max_width or CW
        lines = wrap_text(txt, mw, size)
        c.setFont("Helvetica", size)
        c.setFillColor(color)
        for line in lines:
            c.drawString(x, y, line)
            y -= size * 1.6
        return y

    # ════════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ════════════════════════════════════════════════════════
    # Dark header band
    rect(0, H-80, W, 80, fill=C_DARK, radius=0)
    text(LM, H-28, "SITE INTELLIGENCE REPORT", size=8, bold=True, color=C_WHITE)
    text(LM, H-46, result["address"], size=16, bold=True, color=C_WHITE)
    text(LM, H-62, f"{result['lat']:.4f} N,  {result['lng']:.4f} E  |  Gujarat, India",
         size=9, color=colors.HexColor("#9ecfc0"))

    # Green divider
    c.setFillColor(C_GREEN)
    c.rect(0, H-84, W, 4, fill=1, stroke=0)

    # Score box — centred
    box_y = H - 280
    rect(LM + CW*0.2, box_y, CW*0.6, 160, fill=C_LTGRN, radius=6)

    # Big score number — perfectly centred
    cx = W / 2
    text(cx, box_y + 95, str(total), size=64, bold=True,
         color=score_color, align="center")
    text(cx, box_y + 72, "out of 100", size=11,
         color=C_GREY, align="center")

    # Thin divider inside box
    hline(box_y + 62, color=C_LINE,
          x0=LM+CW*0.25, x1=LM+CW*0.75)

    text(cx, box_y + 44, verdict, size=15, bold=True,
         color=score_color, align="center")
    text(cx, box_y + 24, recommend, size=10,
         color=C_GREY, align="center")

    # Intro paragraph
    intro = ("This report scores the candidate site across 5 location intelligence "
             "variables: demand potential, footfall proxies, competitive density, "
             "road accessibility, and catchment quality.")
    body_text(LM, box_y - 30, intro, size=10,
              color=colors.HexColor("#555555"))

    # Footer
    hline(30, color=C_LINE)
    text(W/2, 16, "SiteScore Analytics  |  Ahmedabad, Gujarat  |  Confidential",
         size=8, color=C_GREY, align="center")

    c.showPage()

    # ════════════════════════════════════════════════════════
    # PAGE 2 — SCORE BREAKDOWN
    # ════════════════════════════════════════════════════════
    y = H - 40
    y = section_header(y, "Score Breakdown")
    text(LM, y, f"Weighted composite score:  {total} / 100", size=10, color=C_GREY)
    y -= 24

    rows = [
        ("Demand Potential",  scores["demand"],        0.25,
         "Residential buildings within 1km  (OpenStreetMap)"),
        ("Footfall Proxy",    scores["footfall"],      0.25,
         "Anchor stores within 500m: supermarket, hospital, school, bank, transit"),
        ("Competition",       scores["competition"],   0.20,
         "QSR competitor density within 500m  (higher = less competition)"),
        ("Accessibility",     scores["accessibility"], 0.20,
         "Road intersection density within 300m  (OSM network)"),
        ("Catchment Quality", scores["catchment"],     0.10,
         "Commercial activity within 1km: shops, cafes, services"),
         ("Spending Power",scores.get("spending_power", 50),0.15,
            "Average price level of nearby places within 1km (Google Places)"),
    ]

    for label, score, weight, note in rows:
        sc = C_GREEN if score >= 65 else C_AMBER if score >= 45 else C_RED
        # Label + weight
        text(LM, y, label, size=11, bold=True, color=C_DARK)
        text(W-RM, y, f"wt: {int(weight*100)}%", size=9, color=C_GREY, align="right")
        y -= 16
        # Bar + score number on same line
        bar_w = CW - 42
        score_bar(LM, y-2, bar_w, 10, score)
        text(W-RM, y+2, str(score), size=11, bold=True, color=sc, align="right")
        y -= 18
        # Note
        text(LM, y, note, size=8, color=C_GREY)
        y -= 12
        hline(y+4, color=C_LINE)
        y -= 14

    # Calibration note
    y -= 6
    rect(LM, y-14, CW, 36, fill=C_LTGRN, radius=4)
    text(LM+10, y+8, "Note: Weights are equal-initialised (v1). Will be recalibrated via regression", size=8, color=colors.HexColor("#0A6E50"))
    text(LM+10, y-4, "once 20+ outlet performance data points are collected.", size=8, color=colors.HexColor("#0A6E50"))

    hline(30, color=C_LINE)
    text(W/2, 16, "SiteScore Analytics  |  Confidential", size=8, color=C_GREY, align="center")
    c.showPage()

    # ════════════════════════════════════════════════════════
    # PAGE 3 — DEMAND & FOOTFALL
    # ════════════════════════════════════════════════════════
    y = H - 40
    y = section_header(y, "Demand & Footfall Analysis")

    y = kv_row(y, "Demand score",    f"{scores['demand']} / 100")
    y = kv_row(y, "Analysis radius", "1,000 m")
    y = kv_row(y, "Data source",     "OpenStreetMap residential buildings")
    y -= 6
    y = kv_row(y, "Footfall score",  f"{scores['footfall']} / 100")
    y = kv_row(y, "Anchor radius",   "500 m")
    y = kv_row(y, "Anchor types",    "Supermarket  |  Hospital  |  School  |  Bank  |  Transit")

    y -= 10
    y = section_header(y, "Interpretation")

    demand_txt = (
        "High demand score indicates dense residential catchment within 1km. "
        "Combined with strong footfall anchors, this location benefits from both "
        "destination and pass-by traffic."
        if scores["demand"] >= 65 else
        "Moderate demand score suggests a mixed residential-commercial zone. "
        "Footfall depends more on anchor proximity than walk-in residential traffic."
        if scores["demand"] >= 45 else
        "Low demand score indicates sparse residential density. Revenue will depend "
        "almost entirely on destination visits and anchor-driven footfall."
    )
    y = body_text(LM, y, demand_txt)
    y -= 16  # breathing room after paragraph
    spending_data = result.get("raw", {}).get("spending_data", {})
    avg_price     = spending_data.get("avg_price_level")
    distribution  = spending_data.get("distribution", {})
    sample_size   = spending_data.get("sample_size", 0)
    spending_score = scores.get("spending_power", 50)

    y -= 10
    y = section_header(y, "Spending Power Analysis")

    y = kv_row(y, "Spending power score", f"{spending_score} / 100")
    y = kv_row(y, "Data source",          "Google Places price levels within 1km")
    y = kv_row(y, "Places sampled",       str(sample_size))

    if avg_price:
        y = kv_row(y, "Average price level",
                   f"{avg_price} / 4.0")
        y = kv_row(y, "Budget places (0-1)",
                   str(distribution.get("budget (0-1)", 0)))
        y = kv_row(y, "Moderate places (2)",
                   str(distribution.get("moderate (2)", 0)))
        y = kv_row(y, "Premium places (3-4)",
                   str(distribution.get("premium (3-4)", 0)))
    else:
        y = kv_row(y, "Note",
                   "Insufficient price data — score defaulted to 50")

    y -= 6
    spending_txt = (
        "High spending power area. Nearby places are predominantly "
        "moderate to premium priced, indicating strong consumer "
        "purchasing capacity. Suitable for premium brand positioning."
        if spending_score >= 65 else
        "Moderate spending power. Mix of budget and mid-range places "
        "nearby. Value-for-money positioning will outperform premium "
        "pricing in this catchment."
        if spending_score >= 40 else
        "Lower spending power area. Predominantly budget-priced places "
        "nearby. Premium brands may face resistance — value positioning "
        "strongly recommended."
    )
    y = body_text(LM, y, spending_txt, size=10, color=C_GREY)

    hline(30, color=C_LINE)
    text(W/2, 16, "SiteScore Analytics  |  Confidential", size=8, color=C_GREY, align="center")
    c.showPage()

    # ════════════════════════════════════════════════════════
    # PAGE 4 — COMPETITION
    # ════════════════════════════════════════════════════════
    y = H - 40
    y = section_header(y, "Competitive Landscape")

    # Replace the simple comp_density with this
    comp_density = (
        "High — strong branded competitors present"
        if scores["competition"] < 30 else
        "Moderate — mix of branded and local competitors"
        if scores["competition"] < 70 else
        "Low — mostly unrated or weak local competitors"
    )
    y = kv_row(y, "Competition score",  f"{scores['competition']} / 100")
    y = kv_row(y, "Analysis radius",    "500 m")
    y = kv_row(y, "Data source",        "Google Places API — QSR keyword search")
    y = kv_row(y, "Competitor density", comp_density)

    y -= 10
    y = section_header(y, "White Space Assessment")

    comp_txt = (
        "High competitor density detected. This is a mature QSR market. "
        "New entrants will compete for existing customers rather than capturing "
        "unserved demand. Success depends on brand differentiation and marketing spend."
        if scores["competition"] < 30 else
        "Moderate competition. Established players exist but the market is not "
        "saturated. A well-positioned brand can capture meaningful share."
        if scores["competition"] < 70 else
        "Low competitor density — genuine white space in the QSR category. "
        "First-mover advantage available. Customer acquisition costs will be lower."
    )
    body_text(LM, y, comp_txt)

    hline(30, color=C_LINE)
    text(W/2, 16, "SiteScore Analytics  |  Confidential", size=8, color=C_GREY, align="center")
    c.showPage()

    # ════════════════════════════════════════════════════════
    # PAGE 5 — ACCESSIBILITY
    # ════════════════════════════════════════════════════════
    y = H - 40
    y = section_header(y, "Accessibility & Visibility")

    y = kv_row(y, "Accessibility score",     f"{scores['accessibility']} / 100")
    y = kv_row(y, "Analysis radius",         "300 m")
    y = kv_row(y, "Data source",             "OpenStreetMap road network (osmnx)")
    y -= 6
    y = kv_row(y, "Catchment quality score", f"{scores['catchment']} / 100")
    y = kv_row(y, "Commercial radius",       "1,000 m")
    y = kv_row(y, "Commercial data source",  "Google Places API")

    y -= 10
    y = section_header(y, "Interpretation")

    acc_txt = (
        "Strong road connectivity with multiple access points. High intersection "
        "density within 300m indicates an arterial or commercial road — positive "
        "for visibility and impulse visits."
        if scores["accessibility"] >= 65 else
        "Moderate road connectivity. Accessible but may not benefit from "
        "high-speed pass-by traffic. Signage and frontage will be important."
        if scores["accessibility"] >= 45 else
        "Limited road connectivity. Low intersection count suggests a residential "
        "lane. Walk-by traffic will be low — delivery model must compensate."
    )
    body_text(LM, y, acc_txt)

    hline(30, color=C_LINE)
    text(W/2, 16, "SiteScore Analytics  |  Confidential", size=8, color=C_GREY, align="center")
    c.showPage()

    # ════════════════════════════════════════════════════════
    # PAGE 6 — RECOMMENDATION
    # ════════════════════════════════════════════════════════
    y = H - 40
    y = section_header(y, "Final Recommendation")

    # Score banner — dark box, fixed height 80pt
    banner_y = y - 80
    rect(LM, banner_y, CW, 76, fill=C_DARK, radius=6)

    # Left side: label + score
    text(LM+14, banner_y+52, "OVERALL SITE SCORE", size=8,
         bold=False, color=colors.HexColor("#9ecfc0"))
    text(LM+14, banner_y+22, f"{total} / 100", size=28,
         bold=True, color=score_color)

    # Right side: verdict + recommendation
    text(W-RM-14, banner_y+52, verdict, size=13,
         bold=True, color=score_color, align="right")
    text(W-RM-14, banner_y+28, recommend, size=9,
         color=colors.HexColor("#9ecfc0"), align="right")

    y = banner_y - 24

    # Risk flags
    risks = []
    if scores["competition"]   < 30: risks.append("HIGH competitor density within 500m — market may be saturated")
    if scores["demand"]        < 40: risks.append("LOW residential population density — walk-in customer base limited")
    if scores["footfall"]      < 40: risks.append("FEW anchor stores nearby — footfall dependent on destination visits")
    if scores["accessibility"] < 40: risks.append("LIMITED road connectivity — may reduce customer convenience")
    if not risks:                    risks.append("No significant risk flags detected at this location")

    is_warning = len(risks) > 0 and "No significant" not in risks[0]
    y = section_header(y, "Key Risk Flags")

    for risk in risks:
        bg  = colors.HexColor("#FFF8F0") if is_warning else C_LTGRN
        bdr = C_AMBER if is_warning else C_GREEN
        prefix = "[!]" if is_warning else "[OK]"
        rect(LM, y-14, CW, 26, fill=bg, radius=3)
        c.setFillColor(bdr)
        c.setStrokeColor(bdr)
        c.setLineWidth(3)
        c.line(LM, y-14, LM, y+12)
        text(LM+10, y, f"{prefix}  {risk}", size=10, color=colors.HexColor("#555555"))
        y -= 36

    y -= 4
    y = section_header(y, "Methodology Note")
    body_text(LM, y,
        "This report uses publicly available data (OpenStreetMap, Google Places API, "
        "Census 2011 proxies) and a weighted scoring model. Scores are indicative and "
        "should be used alongside on-ground site visits and lease terms review. "
        "Weights will be calibrated against actual outlet performance data as "
        "client engagement progresses.",
        size=9, color=C_GREY)

    hline(30, color=C_LINE)
    text(W/2, 16,
         "SiteScore Analytics  |  Ahmedabad, Gujarat  |  Confidential — prepared exclusively for client use",
         size=8, color=C_GREY, align="center")

    c.showPage()
    c.save()
    print(f"Report saved: {output_path}")
    return output_path