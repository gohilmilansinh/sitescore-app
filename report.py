from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from datetime import datetime
from benchmarks import get_category_context


# ── Colour palette ────────────────────────────────────────
C_DARK    = colors.HexColor("#0A2E26")
C_GREEN   = colors.HexColor("#1D9E75")
C_GREEN2  = colors.HexColor("#F0FAF6")
C_AMBER   = colors.HexColor("#BA7517")
C_RED     = colors.HexColor("#C0392B")
C_GREY    = colors.HexColor("#888888")
C_LGREY   = colors.HexColor("#F5F5F5")
C_LINE    = colors.HexColor("#EEEEEE")
C_DLINE   = colors.HexColor("#222222")
C_WHITE   = colors.white
C_BLACK   = colors.black
C_BG      = colors.HexColor("#0d1f1a")
C_AMBER_L = colors.HexColor("#FFF8F0")
C_GREEN_L = colors.HexColor("#F0FAF6")


def generate_report(result: dict, output_path: str = "siteiq_report.pdf") -> str:
    scores  = result.get("scores", {})
    total   = result.get("total_score", 0)
    raw     = result.get("raw", {})
    W, H    = A4

    score_color = C_GREEN if total >= 65 else C_AMBER if total >= 45 else C_RED
    verdict     = "STRONG SITE"   if total >= 65 else \
                  "MODERATE SITE" if total >= 45 else "WEAK SITE"
    recommend   = "Proceed to lease negotiation" if total >= 65 else \
                  "Address risk flags before committing" if total >= 45 else \
                  "Seek alternative locations"

    LM = 18 * mm
    RM = 18 * mm
    CW = W - LM - RM
    cx = W / 2

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle("SiteIQ — Retail Location Intelligence Report")
    c.setAuthor("SiteIQ Analytics")

    # ── Helpers ───────────────────────────────────────────
    def txt(x, y, t, size=10, bold=False, color=C_BLACK, align="left"):
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.setFillColor(color)
        s = str(t)
        if align == "center": c.drawCentredString(x, y, s)
        elif align == "right": c.drawRightString(x, y, s)
        else: c.drawString(x, y, s)

    def box(x, y, w, h, fill=C_LGREY, stroke=None, r=3):
        c.setFillColor(fill)
        c.setStrokeColor(stroke or fill)
        c.setLineWidth(0.5)
        c.roundRect(x, y, w, h, r, fill=1, stroke=1 if stroke else 0)

    def hline(y, x0=None, x1=None, color=C_LINE, lw=0.5):
        c.setStrokeColor(color)
        c.setLineWidth(lw)
        c.line(x0 or LM, y, x1 or (W - RM), y)

    def score_bar(x, y, w, h, score):
        col = C_GREEN if score >= 65 else C_AMBER if score >= 45 else C_RED
        box(x, y, w, h, fill=C_LINE)
        filled = max(0, (score / 100) * w)
        if filled > 0:
            box(x, y, filled, h, fill=col)

    def section_title(y, title):
        box(LM, y - 4, CW, 24, fill=C_GREEN2, r=4)
        c.setFillColor(C_GREEN)
        c.setStrokeColor(C_GREEN)
        c.setLineWidth(3)
        c.line(LM, y - 4, LM, y + 20)
        txt(LM + 12, y + 5, title, size=12, bold=True, color=C_DARK)
        return y - 36

    def kv(y, label, value, label_color=None, value_color=None):
        txt(LM, y, label, size=9, color=label_color or C_GREY)
        txt(W - RM, y, value, size=10, bold=True,
            color=value_color or C_DARK, align="right")
        hline(y - 7)
        return y - 22

    def wrap(text, max_w, size=9):
        c.setFont("Helvetica", size)
        words, lines, line = text.split(), [], ""
        for w in words:
            test = f"{line} {w}".strip()
            if c.stringWidth(test, "Helvetica", size) <= max_w:
                line = test
            else:
                if line: lines.append(line)
                line = w
        if line: lines.append(line)
        return lines

    def body(x, y, text, size=9, color=C_GREY, max_w=None):
        for line in wrap(text, max_w or CW, size):
            c.setFont("Helvetica", size)
            c.setFillColor(color)
            c.drawString(x, y, line)
            y -= size * 1.65
        return y

    def footer(page_num):
        hline(22, color=C_LINE)
        txt(LM, 10, "SiteIQ Analytics  |  Confidential  |  Data: OpenStreetMap + Google Places API",
            size=7, color=C_GREY)
        txt(W - RM, 10, f"Page {page_num}", size=7, color=C_GREY, align="right")

    def risk_box(y, text, is_warning=True):
        bg  = C_AMBER_L if is_warning else C_GREEN_L
        bdr = C_AMBER   if is_warning else C_GREEN
        box(LM, y - 14, CW, 26, fill=bg, stroke=None, r=3)
        c.setFillColor(bdr)
        c.setStrokeColor(bdr)
        c.setLineWidth(3)
        c.line(LM, y - 14, LM, y + 12)
        prefix = "[!]" if is_warning else "[OK]"
        txt(LM + 10, y - 1, f"{prefix}  {text}", size=9,
            color=colors.HexColor("#555555"))
        return y - 32

    # ════════════════════════════════════════════════════
    # PAGE 1 — COVER
    # ════════════════════════════════════════════════════
    # Dark header band
    box(0, H - 90, W, 90, fill=C_DARK, r=0)

    # Brand name
    txt(LM, H - 34, "SiteIQ", size=22, bold=True, color=C_GREEN)
    txt(LM + 76, H - 34, "Analytics", size=22, bold=False, color=C_WHITE)
    txt(LM, H - 52, "RETAIL LOCATION INTELLIGENCE", size=8,
        bold=False, color=C_GREY)

    # Report date top right
    date_str = datetime.now().strftime("%d %b %Y")
    txt(W - RM, H - 34, date_str, size=9, color=C_GREY, align="right")
    txt(W - RM, H - 50, "Confidential Report", size=8,
        color=C_GREY, align="right")

    # Green accent line
    c.setFillColor(C_GREEN)
    c.rect(0, H - 94, W, 4, fill=1, stroke=0)

    # Site address block
    txt(LM, H - 116, "SITE INTELLIGENCE REPORT", size=8,
        color=C_GREY, bold=False)
    # Word-wrap long addresses
    addr_lines = wrap(result.get("address", "Unknown Address"), CW, size=14)
    addr_y = H - 134
    for addr_line in addr_lines:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(C_BLACK)
        c.drawString(LM, addr_y, addr_line)
        addr_y -= 18
    txt(LM, addr_y - 6,
        f"{result.get('lat', 0):.4f} N,  {result.get('lng', 0):.4f} E  |  Gujarat, India",
        size=9, color=C_GREY)
    txt(LM, addr_y - 20,
        f"Brand category: {result.get('brand_type', 'restaurant').title()}",
        size=9, color=C_GREY)

    hline(addr_y - 30, color=C_LINE)

    # Score card
    card_h = 160
    card_y = addr_y - 200   # dynamic — sits below coordinates
    box(LM + CW * 0.1, card_y, CW * 0.8, card_h, fill=C_GREEN2, r=8)

    # Upper section: score number
    # Large text baseline needs to be placed higher than mid
    upper_mid = card_y + card_h * 0.68
    txt(cx, upper_mid, str(total), size=52, bold=True,
        color=score_color, align="center")
    txt(cx, upper_mid - 22, "out of 100", size=9,
        color=C_GREY, align="center")

    # Divider
    divider_y = card_y + card_h * 0.44
    hline(divider_y, color=C_LINE,
          x0=LM + CW * 0.2, x1=LM + CW * 0.8)

    # Lower section: verdict and recommendation
    lower_mid = card_y + card_h * 0.28
    txt(cx, lower_mid, verdict, size=12, bold=True,
        color=score_color, align="center")
    txt(cx, lower_mid - 18, recommend, size=9,
        color=C_GREY, align="center")

    # Mini score pills
    pill_labels = ["Demand", "Footfall", "Competition",
                   "Accessibility", "Catchment", "Spending"]
    pill_keys   = ["demand", "footfall", "competition",
                   "accessibility", "catchment", "spending_power"]
    pill_w = CW / 6
    pill_y = card_y - 24

    for i, (lbl, key) in enumerate(zip(pill_labels, pill_keys)):
        s   = scores.get(key, 0)
        col = C_GREEN if s >= 65 else C_AMBER if s >= 45 else C_RED
        px  = LM + i * pill_w
        box(px + 2, pill_y - 30, pill_w - 4, 36, fill=C_LGREY, r=4)
        txt(px + pill_w / 2, pill_y - 6, str(s), size=12, bold=True,
            color=col, align="center")
        txt(px + pill_w / 2, pill_y - 22, lbl, size=7,
            color=C_GREY, align="center")

    # Introduction text
    intro_y = pill_y - 56
    hline(intro_y + 14, color=C_LINE)
    intro = (
        "This report scores the candidate retail site across six "
        "location intelligence variables using live data from "
        "OpenStreetMap, Google Places API, and Census of India 2011. "
        "Scores are weighted composites designed for franchise brand "
        "site selection in Gujarat."
    )
    body(LM, intro_y, intro, size=9,
         color=colors.HexColor("#555555"))

    footer(1)
    c.showPage()

    # ════════════════════════════════════════════════════
    # PAGE 2 — SCORE BREAKDOWN
    # ════════════════════════════════════════════════════
    y = H - 40
    y = section_title(y, "Score Breakdown")
    txt(LM, y, f"Weighted composite score: {total} / 100  |  "
        f"Category: {result.get('brand_type','restaurant').title()}",
        size=9, color=C_GREY)
    y -= 20

    variable_rows = [
        ("Demand Potential",  "demand",        0.20,
         "Census 2011 ward population estimate within 1km"),
        ("Footfall Proxy",    "footfall",      0.20,
         "Anchor stores within 500m — supermarkets, hospitals, schools, banks"),
        ("Competition",       "competition",   0.20,
         "QSR competitor density within 500m, weighted by review count"),
        ("Accessibility",     "accessibility", 0.15,
         "Road intersection density within 300m via OSM drive network"),
        ("Catchment Quality", "catchment",     0.10,
         "Commercial activity density within 1km — cafes, shops, services"),
        ("Spending Power",    "spending_power",0.15,
         "Average Google Places price level within 1km as income proxy"),
    ]

    for label, key, weight, note in variable_rows:
        sc  = scores.get(key, 0)
        col = C_GREEN if sc >= 65 else C_AMBER if sc >= 45 else C_RED

        txt(LM, y, label, size=10, bold=True, color=C_DARK)
        txt(W - RM, y, f"weight: {int(weight * 100)}%",
            size=8, color=C_GREY, align="right")
        y -= 15

        bar_w = CW - 48
        score_bar(LM, y - 2, bar_w, 9, sc)
        txt(W - RM, y + 2, str(sc), size=11, bold=True,
            color=col, align="right")
        y -= 14

        txt(LM, y, note, size=8, color=C_GREY)
        y -= 12
        hline(y + 4, color=C_LINE)
        y -= 14

    # Weight calibration note
    y -= 4
    box(LM, y - 18, CW, 38, fill=C_GREEN2, r=4)
    txt(LM + 10, y + 6,
        "Model note: Weights are initialised using domain logic (v1). "
        "After 20+ outlet performance data", size=8,
        color=colors.HexColor("#0A6E50"))
    txt(LM + 10, y - 8,
        "points are collected, weights will be recalibrated via "
        "regression to reflect brand-specific performance.", size=8,
        color=colors.HexColor("#0A6E50"))

    footer(2)
    c.showPage()

    # ════════════════════════════════════════════════════
    # PAGE 3 — DEMAND, FOOTFALL & SPENDING POWER
    # ════════════════════════════════════════════════════
    y = H - 40
    y = section_title(y, "Demand Analysis")

    method = raw.get("demand_method", "osm_buildings")
    if method == "census_2011":
        y = kv(y, "Demand score",
               f"{scores.get('demand', 0)} / 100")
        y = kv(y, "Data source",
               "Census of India 2011 — ward population estimates")
        y = kv(y, "Estimated population within 1km",
               f"{raw.get('demand_population', 0):,}")
        y = kv(y, "Estimated households within 1km",
               f"{raw.get('demand_households', 0):,}")
        wards = raw.get("demand_wards", [])
        if wards:
            ward_str = "  |  ".join(
                f"{w['name']} ({w['city']})" for w in wards[:3])
            y = kv(y, "Contributing wards", ward_str)
    else:
        y = kv(y, "Demand score",
               f"{scores.get('demand', 0)} / 100")
        y = kv(y, "Data source",
               "OpenStreetMap residential buildings")
        y = kv(y, "Buildings counted within 1km",
               str(raw.get("demand_buildings", 0)))

    demand_txt = (
        "High demand score — dense residential catchment within 1km. "
        "Strong population base for walk-in customer acquisition."
        if scores.get("demand", 0) >= 65 else
        "Moderate demand — mixed residential and commercial zone. "
        "Footfall will depend more on anchors than residential density."
        if scores.get("demand", 0) >= 45 else
        "Low demand — sparse residential density within 1km. Revenue "
        "will depend almost entirely on destination visits."
    )
    y -= 4
    body(LM, y, demand_txt, size=9, color=C_GREY)
    y -= 28

    y = section_title(y, "Footfall Analysis")
    anchors      = raw.get("footfall_anchors", {})
    anchor_total = sum(anchors.values()) if anchors else 0
    y = kv(y, "Footfall score",
           f"{scores.get('footfall', 0)} / 100")
    y = kv(y, "Analysis radius", "500 m")
    y = kv(y, "Anchor stores found", str(anchor_total))

    if anchors:
        for anchor_type, count in list(anchors.items())[:5]:
            y = kv(y, f"  — {anchor_type.replace('_', ' ').title()}",
                   str(count))

    footfall_txt = (
        "Strong anchor presence drives consistent footfall. "
        "Location benefits from multiple demand generators nearby."
        if scores.get("footfall", 0) >= 65 else
        "Moderate anchor presence. Footfall is present but not dominant. "
        "Brand visibility and signage will be important."
        if scores.get("footfall", 0) >= 45 else
        "Weak anchor presence. Very few footfall drivers nearby. "
        "Site relies on destination traffic only."
    )
    y -= 4
    body(LM, y, footfall_txt, size=9, color=C_GREY)
    y -= 28

    y = section_title(y, "Spending Power Analysis")
    spending      = raw.get("spending_data", {})
    avg_price     = spending.get("avg_price_level")
    sample_size   = spending.get("sample_size", 0)
    distribution  = spending.get("distribution", {})

    y = kv(y, "Spending power score",
           f"{scores.get('spending_power', 0)} / 100")
    y = kv(y, "Data source",
           "Google Places price levels within 1km")
    y = kv(y, "Places sampled", str(sample_size))
    if avg_price:
        y = kv(y, "Average price level", f"{avg_price} / 4.0")
        y = kv(y, "Budget places (level 0-1)",
               str(distribution.get("budget (0-1)", 0)))
        y = kv(y, "Moderate places (level 2)",
               str(distribution.get("moderate (2)", 0)))
        y = kv(y, "Premium places (level 3-4)",
               str(distribution.get("premium (3-4)", 0)))
    else:
        y = kv(y, "Note", "Insufficient price data — defaulted to 50")

    footer(3)
    c.showPage()

    # ════════════════════════════════════════════════════
    # PAGE 4 — COMPETITION & ACCESSIBILITY
    # ════════════════════════════════════════════════════
    y = H - 40
    y = section_title(y, "Competitive Landscape")

    comp_score   = scores.get("competition", 0)
    comp_count   = raw.get("competitor_count", 0)
    comp_density = (
        "High — strong branded competitors present (15+)"
        if comp_score < 30 else
        "Moderate — mix of branded and local competitors (5-14)"
        if comp_score < 70 else
        "Low — mostly weak or unreviewed local competitors (<5)"
    )
    y = kv(y, "Competition score",
           f"{comp_score} / 100")
    y = kv(y, "Analysis radius", "500 m")
    y = kv(y, "Competitor density", comp_density)
    y = kv(y, "Competitors found and weighted", str(comp_count))
    y = kv(y, "Weighting method",
           "Review count (70%) + Rating (30%) — branded = higher weight")

    comp_txt = (
        "Saturated market. Strong branded competitors present. "
        "Success depends on brand differentiation and marketing investment."
        if comp_score < 30 else
        "Moderate competition. Established players exist but the market "
        "is not saturated. A well-positioned brand can capture real share."
        if comp_score < 70 else
        "White space detected. Low competitor density means first-mover "
        "advantage is available. Customer acquisition will cost less."
    )
    y -= 8
    body(LM, y, comp_txt, size=9, color=C_GREY)
    y -= 28

    # Competitor detail table if available
    competitors = result.get("competitor_details", [])
    if competitors:
        top_comps = sorted(
            competitors, key=lambda x: x.get("strength", 0),
            reverse=True)[:6]
        y -= 8

        # Table header
        box(LM, y - 4, CW, 18, fill=C_DARK, r=3)
        txt(LM + 6,       y + 4, "Competitor",
            size=8, bold=True, color=C_WHITE)
        txt(LM + CW*0.50, y + 4, "Reviews",
            size=8, bold=True, color=C_WHITE)
        txt(LM + CW*0.65, y + 4, "Rating",
            size=8, bold=True, color=C_WHITE)
        txt(LM + CW*0.80, y + 4, "Strength",
            size=8, bold=True, color=C_WHITE)
        y -= 22

        for i, comp in enumerate(top_comps):
            row_fill = C_LGREY if i % 2 == 0 else C_WHITE
            box(LM, y - 4, CW, 16, fill=row_fill, r=0)
            strength = comp.get("strength", 0)
            s_col = (C_RED if strength > 0.6
                     else C_AMBER if strength > 0.3 else C_GREEN)
            s_lbl = ("Strong" if strength > 0.6
                     else "Moderate" if strength > 0.3 else "Weak")
            name = comp.get("name", "")[:28]
            txt(LM + 6,       y + 4, name, size=8, color=C_DARK)
            txt(LM + CW*0.50, y + 4,
                f"{comp.get('reviews', 0):,}", size=8, color=C_GREY)
            txt(LM + CW*0.65, y + 4,
                str(comp.get("rating", 0)), size=8, color=C_GREY)
            txt(LM + CW*0.80, y + 4, s_lbl, size=8,
                bold=True, color=s_col)
            y -= 18

    y -= 10
    y = section_title(y, "Accessibility & Catchment")

    intersections = raw.get("intersections", 0)
    road_nodes    = raw.get("road_nodes", 0)
    catchment_n   = raw.get("catchment_places", 0)

    y = kv(y, "Accessibility score",
           f"{scores.get('accessibility', 0)} / 100")
    y = kv(y, "Road network analysis radius", "300 m")
    y = kv(y, "Road intersections counted", str(intersections))
    y = kv(y, "Total road nodes in network", str(road_nodes))
    y -= 6
    y = kv(y, "Catchment quality score",
           f"{scores.get('catchment', 0)} / 100")
    y = kv(y, "Commercial places within 1km",
           str(catchment_n))
    y = kv(y, "Data source",
           "OpenStreetMap road network + Google Places API")

    acc_txt = (
        "Strong road connectivity. High intersection density indicates "
        "an arterial or commercial road — positive for visibility."
        if scores.get("accessibility", 0) >= 65 else
        "Moderate connectivity. Accessible but not a primary arterial. "
        "Signage and frontage will matter for impulse visits."
        if scores.get("accessibility", 0) >= 45 else
        "Limited road connectivity. Low intersection count suggests a "
        "side lane. Walk-by traffic will be minimal."
    )
    y -= 4
    body(LM, y, acc_txt, size=9, color=C_GREY)

    footer(4)
    c.showPage()

    # ════════════════════════════════════════════════════
    # PAGE 5 — ROI ANALYSIS (only if rent data available)
    # ════════════════════════════════════════════════════
    roi = result.get("roi")
    if roi:
        y = H - 40
        y = section_title(y, "ROI & Investment Analysis")
        y = y +20
        # Combined score banner
        banner_h = 70
        banner_y = y - banner_h
        box(LM, banner_y, CW, banner_h, fill=C_DARK, r=6)

        # Left side — label at top, big score below
        txt(LM + 16, banner_y + banner_h - 16,
            "COMBINED SCORE", size=8, color=C_GREY)
        txt(LM + 16, banner_y + 18,
            f"{roi['combined_score']} / 100",
            size=24, bold=True,
            color=colors.HexColor(roi["verdict_color"]))

        # Right side — verdict at top, recommendation below
        txt(W - RM - 16, banner_y + banner_h - 16,
            roi["verdict"], size=13, bold=True,
            color=colors.HexColor(roi["verdict_color"]),
            align="right")
        txt(W - RM - 16, banner_y + 18,
            roi["recommendation"], size=9,
            color=C_GREY, align="right")

        y = banner_y - 16

        y = kv(y, "Location score",
               f"{roi['location_score']} / 100")
        y = kv(y, "ROI score",
               f"{roi['roi_score']} / 100")
        y = kv(y, "Combined score (70% location + 30% ROI)",
               f"{roi['combined_score']} / 100")

        y -= 6
        y = section_title(y, "Financial Summary")

        def fmt(n):
            if n >= 100000:
                return f"Rs. {n/100000:.1f}L"
            return f"Rs. {n:,.0f}"

        y = kv(y, "Est. monthly revenue",
               fmt(roi["est_monthly_revenue"]))
        y = kv(y, "Monthly rent",
               fmt(roi["monthly_rent"]))
        y = kv(y, "Monthly profit",
               fmt(roi["monthly_profit"]),
               value_color=C_GREEN if roi["monthly_profit"] > 0
               else C_RED)
        y = kv(y, "Annual profit",
               fmt(roi["annual_profit"]))
        y = kv(y, "Rent as % of revenue",
               f"{roi['rent_pct_of_revenue']}%")
        y = kv(y, "Rent rating",
               roi["rent_label"],
               value_color=colors.HexColor(roi["rent_color"]))
        y = kv(y, "Setup / fit-out cost",
               fmt(roi["setup_cost"]))
        y = kv(y, "Estimated payback period",
               f"{roi['payback_months']:.0f} months"
               if roi["payback_months"] < 999
               else "Not viable at current rent")

        y -= 10
        disclaimer = (
            "Revenue estimates are based on Gujarat market benchmarks "
            "for the selected brand category. Actual revenue will vary "
            "based on brand strength, operations, and local market "
            "conditions. These estimates should be validated against "
            "actual outlet performance data before final commitment."
        )
        body(LM, y, disclaimer, size=8, color=C_GREY)

        footer(5)
        c.showPage()

    # ════════════════════════════════════════════════════
    # PAGE 6 — FINAL RECOMMENDATION
    # ════════════════════════════════════════════════════
    y = H - 40
    y = section_title(y, "Final Recommendation")
    y= y+20
    # Score banner
    banner_h = 80
    banner_y = y - banner_h
    box(LM, banner_y, CW, banner_h, fill=C_DARK, r=6)

    txt(LM + 16, banner_y + 56, "OVERALL SITE SCORE",
        size=8, color=C_GREY)
    txt(LM + 16, banner_y + 26,
        f"{total} / 100", size=28, bold=True, color=score_color)
    txt(W - RM - 16, banner_y + 56, verdict, size=13,
        bold=True, color=score_color, align="right")
    txt(W - RM - 16, banner_y + 30, recommend, size=9,
        color=C_GREY, align="right")
    txt(W - RM - 16, banner_y + 14,
        result.get("address", "")[:50], size=8,
        color=colors.HexColor("#4a8a78"), align="right")

    y = banner_y - 20

    # Benchmark context
    brand_type = result.get("brand_type", "restaurant")
    bm         = get_category_context(total, brand_type)
    stats      = bm["stats"]
    percentile = bm["percentile"]
    y = y -10
    y = section_title(y, "Benchmark Comparison")
    y=y+6
    y = kv(y, "Percentile rank",
           f"Better than {percentile}% of similar sites")
    y = kv(y, "Benchmark average score",
           str(stats.get("average", 0)))
    y = kv(y, "Top sites average",
           str(stats.get("top_sites_avg", 0)))
    y = kv(y, "Reference sites in dataset",
           str(stats.get("count", 0)))
    y -= 4
    body(LM, y, bm.get("context", ""), size=9, color=C_GREY)
    y -= 36

    # Score contributions
    from score_explainer import explain_scores
    explanation = explain_scores(
        scores=scores,
        brand_type=result.get("brand_type", "restaurant"),
        total_score=total,
    )

    y -= 6
    y = section_title(y, "Score Contribution Analysis")
    y=y+8
    if explanation["narrative"]:
        y = body(LM, y, explanation["narrative"],
                 size=9, color=C_GREY)
        y -= 8

    for contrib in explanation["contributions"]:
        score_c = (C_GREEN if contrib["score"] >= 65
                   else C_AMBER if contrib["score"] >= 45 else C_RED)
        delta_c = (C_GREEN if contrib["delta"] >= 0 else C_RED)
        delta_s = (f"+{contrib['delta']}"
                   if contrib["delta"] >= 0
                   else str(contrib["delta"]))

        txt(LM, y, contrib["label"], size=9,
            bold=True, color=C_DARK)
        txt(LM + 90, y, str(contrib["score"]),
            size=9, bold=True, color=score_c)
        txt(LM + 130, y,
            f"wt:{contrib['weight_pct']}%",
            size=8, color=C_GREY)
        txt(LM + 175, y, f"contrib: {delta_s}",
            size=8, bold=True, color=delta_c)
        txt(LM + 260, y, contrib["insight"],
            size=7, color=C_GREY)
        y -= 16
        score_bar(LM, y, CW * 0.5, 5, contrib["score"])
        y -= 26
    
    y = y - 10

    # Risk flags
    y = section_title(y, "Key Risk Flags")
    y=y+6
    risks = []
    if scores.get("competition", 100)   < 30:
        risks.append((True,
            "HIGH competitor density within 500m — market may be saturated"))
    if scores.get("demand", 100)        < 40:
        risks.append((True,
            "LOW residential population density — walk-in base limited"))
    if scores.get("footfall", 100)      < 40:
        risks.append((True,
            "FEW anchor stores nearby — footfall is destination-only"))
    if scores.get("accessibility", 100) < 40:
        risks.append((True,
            "LIMITED road connectivity — access may reduce convenience"))
    if scores.get("spending_power", 100) < 35:
        risks.append((True,
            "LOW spending power area — premium pricing may face resistance"))
    if not risks:
        risks.append((False,
            "No significant risk flags detected at this location"))

    for is_warning, risk_text in risks:
        y = risk_box(y, risk_text, is_warning=is_warning)

    y -= 8
    y = section_title(y, "Methodology Note")
    y=y+6
    method_txt = (
        "This report uses publicly available data from OpenStreetMap, "
        "Google Places API, and Census of India 2011. Scores are a "
        "weighted composite across six location intelligence variables. "
        "All scores are indicative and should be used alongside "
        "on-ground site visits and formal lease terms review. Model "
        "weights will be empirically calibrated against actual outlet "
        "performance data as client engagement progresses."
    )
    body(LM, y, method_txt, size=8, color=C_GREY)

    # Footer bar
    box(0, 0, W, 36, fill=C_DARK, r=0)
    txt(LM, 22,
        "SiteIQ Analytics  |  Ahmedabad, Gujarat  |  "
        "Confidential — prepared exclusively for client use",
        size=8, color=C_GREY)
    txt(W - RM, 22,
        f"Generated {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
        size=8, color=C_GREY, align="right")
    txt(cx, 10, "Page 6", size=7, color=C_GREY, align="center")
    c.showPage()
    c.save()
    print(f"Report saved: {output_path}")
    return output_path