from __future__ import annotations

from typing import Any, Dict

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm


def generate_report(result: Dict[str, Any], output_path: str = "site_report.pdf") -> None:
    scores = result["scores"]
    total = result["total_score"]
    W, H = A4

    C_GREEN = colors.HexColor("#1D9E75")
    C_DARK = colors.HexColor("#0A2E26")
    C_AMBER = colors.HexColor("#BA7517")
    C_RED = colors.HexColor("#C0392B")
    C_LGREY = colors.HexColor("#F5F5F5")
    C_GREY = colors.HexColor("#888888")
    C_LTGRN = colors.HexColor("#F0FAF6")
    C_WHITE = colors.white
    C_LINE = colors.HexColor("#EEEEEE")

    score_color = C_GREEN if total >= 65 else C_AMBER if total >= 45 else C_RED
    verdict = "STRONG SITE" if total >= 65 else "MODERATE SITE" if total >= 45 else "WEAK SITE"
    recommend = (
        "Proceed to lease negotiation"
        if total >= 65
        else "Address risk flags before committing"
        if total >= 45
        else "Seek alternative locations"
    )

    LM, RM = 18 * mm, 18 * mm
    CW = W - LM - RM

    c = canvas.Canvas(output_path, pagesize=A4)

    def text(x: float, y: float, txt: str, size: int = 11, bold: bool = False, color=colors.black, align: str = "left") -> None:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.setFillColor(color)
        if align == "center":
            c.drawCentredString(x, y, str(txt))
        elif align == "right":
            c.drawRightString(x, y, str(txt))
        else:
            c.drawString(x, y, str(txt))

    def rect(x: float, y: float, w: float, h: float, fill=C_LGREY, stroke=None, radius: int = 3) -> None:
        c.setFillColor(fill)
        if stroke:
            c.setStrokeColor(stroke)
            c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
        else:
            c.setStrokeColor(fill)
            c.roundRect(x, y, w, h, radius, fill=1, stroke=0)

    def hline(y: float, color=C_LINE, x0=None, x1=None, thickness: float = 0.5) -> None:
        c.setStrokeColor(color)
        c.setLineWidth(thickness)
        c.line(x0 or LM, y, x1 or (W - RM), y)

    def score_bar(x: float, y: float, w: float, h: float, score: float) -> None:
        col = C_GREEN if score >= 65 else C_AMBER if score >= 45 else C_RED
        c.setFillColor(C_LINE)
        c.setStrokeColor(C_LINE)
        c.roundRect(x, y, w, h, 2, fill=1, stroke=0)
        filled = (score / 100) * w
        if filled > 0:
            c.setFillColor(col)
            c.roundRect(x, y, filled, h, 2, fill=1, stroke=0)

    def section_header(y: float, title: str) -> float:
        rect(LM, y - 4, CW, 22, fill=C_LTGRN)
        c.setFillColor(C_GREEN)
        c.setStrokeColor(C_GREEN)
        c.setLineWidth(3)
        c.line(LM, y - 4, LM, y + 18)
        text(LM + 10, y + 4, title, size=12, bold=True, color=C_DARK)
        return y - 34

    def wrap_text(txt: str, max_width: float, size: int = 10) -> list[str]:
        c.setFont("Helvetica", size)
        words = txt.split()
        lines: list[str] = []
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if c.stringWidth(test, "Helvetica", size) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    def body_text(x: float, y: float, txt: str, size: int = 10, color=colors.HexColor("#444444"), max_width: float | None = None) -> float:
        mw = max_width or CW
        lines = wrap_text(txt, mw, size)
        c.setFont("Helvetica", size)
        c.setFillColor(color)
        for line in lines:
            c.drawString(x, y, line)
            y -= size * 1.6
        return y

    y = H - 40
    y = section_header(y, "Score Breakdown")
    text(LM, y, f"Weighted composite score:  {total} / 100", size=10, color=C_GREY)
    y -= 24

    rows = [
        ("Demand Potential", scores["demand"], 0.25, "Residential buildings within 1km  (OpenStreetMap)"),
        ("Footfall Proxy", scores["footfall"], 0.25, "Anchor stores within 500m: supermarket, hospital, school, bank, transit"),
        ("Competition", scores["competition"], 0.20, "QSR competitor density within 500m  (higher = less competition)"),
        ("Accessibility", scores["accessibility"], 0.20, "Road intersection density within 300m  (OSM network)"),
        ("Catchment Quality", scores["catchment"], 0.10, "Commercial activity within 1km: shops, cafes, services"),
        ("Spending Power", scores.get("spending_power", 50), 0.15, "Average price level of nearby places within 1km (Google Places)"),
    ]

    for label, score, weight, note in rows:
        sc = C_GREEN if score >= 65 else C_AMBER if score >= 45 else C_RED
        text(LM, y, label, size=11, bold=True, color=C_DARK)
        text(W - RM, y, f"wt: {int(weight * 100)}%", size=9, color=C_GREY, align="right")
        y -= 16
        bar_w = CW - 42
        score_bar(LM, y - 2, bar_w, 10, score)
        text(W - RM, y + 2, str(score), size=11, bold=True, color=sc, align="right")
        y -= 18
        text(LM, y, note, size=8, color=C_GREY)
        y -= 12
        hline(y + 4, color=C_LINE)
        y -= 14

    y -= 6
    rect(LM, y - 14, CW, 36, fill=C_LTGRN, radius=4)
    text(LM + 10, y + 8, "Note: Weights are equal-initialised (v1). Will be recalibrated via regression", size=8, color=colors.HexColor("#0A6E50"))
    text(LM + 10, y - 4, "once 20+ outlet performance data points are collected.", size=8, color=colors.HexColor("#0A6E50"))

    c.showPage()
    c.save()
