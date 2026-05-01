"""
utils/report_generator.py
FormOptiX — Bill of Quantities PDF Generator

Academic basis:
  IS 1200 (Part 1). (1992). Method of Measurement of Building and Civil
    Engineering Works. Bureau of Indian Standards.
    → Defines the standard column structure for BoQ tables used in Indian
      construction procurement. Validates: SKU, Week, Qty, Cost columns.

  PMI. (2021). A Guide to the Project Management Body of Knowledge
    (PMBOK Guide, 7th ed.). Project Management Institute.
    → Section 4.3: BoQ is a formal project procurement document.
      Must be signable, dateable, and handable to a vendor.

  ACI 347R-14. (2014). Guide to Formwork for Concrete.
    American Concrete Institute. Section 2.
    → Formwork planning documentation requirements.

  reportlab: BSD-licensed, pure-Python. No external server needed.
  PuLP/CBC: described in lp_optimizer.py.
"""

import pandas as pd
from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ─────────────────────────────────────────────────────────────────
# Colour palette — mirrors the Streamlit dark-theme tokens
# ─────────────────────────────────────────────────────────────────
_ORANGE  = colors.HexColor("#E8611A")
_DARK    = colors.HexColor("#0D1117")
_TEAL    = colors.HexColor("#0D9488")
_GREEN   = colors.HexColor("#16A34A")
_RED     = colors.HexColor("#DC2626")
_AMBER   = colors.HexColor("#D97706")
_GRAY    = colors.HexColor("#374151")
_LGRAY   = colors.HexColor("#F3F4F6")
_WHITE   = colors.white
_BLACK   = colors.black
_IDLE_BG = colors.HexColor("#FFCDD2")   # light red  — idle rows
_REUSE_BG= colors.HexColor("#C8E6C9")   # light green — reuse rows
_ALT_BG  = colors.HexColor("#F9FAFB")   # alternating row tint


# ─────────────────────────────────────────────────────────────────
# Style helpers
# ─────────────────────────────────────────────────────────────────
def _styles():
    ss = getSampleStyleSheet()

    title = ParagraphStyle(
        "fo_title",
        fontSize=20, leading=24, spaceAfter=4,
        textColor=_ORANGE, fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )
    subtitle = ParagraphStyle(
        "fo_subtitle",
        fontSize=12, leading=16, spaceAfter=2,
        textColor=_GRAY, fontName="Helvetica",
        alignment=TA_LEFT,
    )
    body = ParagraphStyle(
        "fo_body",
        fontSize=9, leading=13, spaceAfter=4,
        textColor=_BLACK, fontName="Helvetica",
    )
    caption = ParagraphStyle(
        "fo_caption",
        fontSize=7.5, leading=11, spaceAfter=2,
        textColor=_GRAY, fontName="Helvetica-Oblique",
    )
    page_title = ParagraphStyle(
        "fo_page_title",
        fontSize=14, leading=18, spaceBefore=4, spaceAfter=6,
        textColor=_DARK, fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )
    ref_title = ParagraphStyle(
        "fo_ref_title",
        fontSize=11, leading=15, spaceBefore=6, spaceAfter=4,
        textColor=_ORANGE, fontName="Helvetica-Bold",
    )
    ref_body = ParagraphStyle(
        "fo_ref_body",
        fontSize=8.5, leading=13, spaceAfter=3,
        textColor=_BLACK, fontName="Helvetica",
        leftIndent=12,
    )
    return dict(
        title=title, subtitle=subtitle, body=body,
        caption=caption, page_title=page_title,
        ref_title=ref_title, ref_body=ref_body,
    )


def _header_style(col_widths):
    """Common TableStyle for a header row."""
    return [
        ("BACKGROUND", (0, 0), (-1, 0), _DARK),
        ("TEXTCOLOR",  (0, 0), (-1, 0), _WHITE),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [_WHITE, _ALT_BG]),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 7.5),
        ("GRID",       (0, 0), (-1, -1), 0.4, _GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",      (0, 0), (0, -1), "LEFT"),   # first col left
    ]


# ─────────────────────────────────────────────────────────────────
# PAGE 1 — Summary
# ─────────────────────────────────────────────────────────────────
def _page1_summary(story, styles, metrics, project_name):
    s = styles

    story.append(Paragraph("FormOptiX \u2014 Bill of Quantities Report", s["title"]))
    story.append(Paragraph(project_name, s["subtitle"]))
    story.append(Paragraph(f"Generated: {date.today().strftime('%d %B %Y')}", s["caption"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_ORANGE, spaceAfter=10))

    story.append(Paragraph("Executive Summary", s["page_title"]))
    story.append(Spacer(1, 0.2 * cm))

    rows = [
        ["Metric", "Value"],
        ["Optimized Procurement Cost",
         f"Rs {metrics.get('optimized_cr', 0):.2f} Cr"],
        ["Baseline (Traditional) Cost",
         f"Rs {metrics.get('baseline_cr', 0):.2f} Cr"],
        ["Total Savings",
         f"Rs {metrics.get('savings_cr', 0):.2f} Cr"],
        ["Savings Percentage",
         f"{metrics.get('savings_pct', 0):.1f}%"],
        ["Panel Reuse Rate",
         f"{metrics.get('overall_reuse_rate', 0) * 100:.1f}%"],
        ["Design Instability Index (DI)",
         (f"{metrics.get('di_value', 0):.1f}%  "
          f"({metrics.get('di_status', 'N/A')})")],
    ]

    col_w = [9 * cm, 7 * cm]
    tbl = Table(rows, colWidths=col_w)
    ts = _header_style(col_w)

    # Colour the DI row based on status
    di_status = metrics.get("di_status", "SAFE")
    di_row = len(rows) - 1  # last row
    if di_status == "HALT":
        ts.append(("BACKGROUND", (0, di_row), (-1, di_row), _IDLE_BG))
        ts.append(("TEXTCOLOR",  (1, di_row), (1, di_row), _RED))
    elif di_status == "WARNING":
        ts.append(("BACKGROUND", (0, di_row), (-1, di_row), colors.HexColor("#FFF9C4")))
        ts.append(("TEXTCOLOR",  (1, di_row), (1, di_row), _AMBER))
    else:
        ts.append(("TEXTCOLOR",  (1, di_row), (1, di_row), _GREEN))

    tbl.setStyle(TableStyle(ts))
    story.append(tbl)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "Note: All costs in Indian Rupees (Rs). "
        "1 Cr = Rs 1,00,00,000. "
        "Procurement costs derived from LP optimisation "
        "(Hillier & Lieberman, 2021).",
        s["caption"],
    ))
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────
# PAGE 2 — Full BoQ Table
# ─────────────────────────────────────────────────────────────────
def _page2_boq(story, styles, boq_df):
    s = styles
    story.append(Paragraph("Complete Bill of Quantities", s["page_title"]))
    story.append(Paragraph(
        "IS 1200 (Part 1, 1992) column structure: SKU | Week | Procure | Reuse | "
        "Hold | Idle | Week Cost (Rs) | Cumulative Cost (Rs)",
        s["caption"],
    ))
    story.append(HRFlowable(width="100%", thickness=0.8, color=_ORANGE, spaceAfter=6))

    if boq_df is None or boq_df.empty:
        story.append(Paragraph("No BoQ data available.", s["body"]))
        story.append(PageBreak())
        return

    # Ensure cumulative_cost column
    if "cumulative_cost" not in boq_df.columns:
        boq_df = boq_df.copy()
        boq_df["cumulative_cost"] = boq_df["week_cost"].cumsum()

    header = ["SKU", "Wk", "Procure", "Reuse", "Hold", "Idle",
              "Wk Cost (Rs)", "Cum. Cost (Rs)"]
    rows = [header]
    idle_rows = []
    reuse_rows = []

    for idx, row in boq_df.iterrows():
        data_row = [
            str(row.get("sku", "")),
            str(int(row.get("week", 0))),
            str(int(row.get("procure", 0))),
            str(int(row.get("reuse", 0))),
            str(int(row.get("hold", 0))),
            str(int(row.get("idle", 0))),
            f"{int(row.get('week_cost', 0)):,}",
            f"{int(row.get('cumulative_cost', 0)):,}",
        ]
        rows.append(data_row)
        ri = len(rows) - 1  # table row index (1-based after header)
        if int(row.get("idle", 0)) > 0:
            idle_rows.append(ri)
        elif int(row.get("reuse", 0)) > 0:
            reuse_rows.append(ri)

    # Column widths proportional to A4 width minus margins
    col_w = [1.8*cm, 0.8*cm, 1.6*cm, 1.6*cm, 1.4*cm, 1.4*cm, 3.0*cm, 3.2*cm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    ts = _header_style(col_w)

    # Row colour coding
    for ri in idle_rows:
        ts.append(("BACKGROUND", (0, ri), (-1, ri), _IDLE_BG))
    for ri in reuse_rows:
        ts.append(("BACKGROUND", (0, ri), (-1, ri), _REUSE_BG))

    tbl.setStyle(TableStyle(ts))
    story.append(tbl)
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Red rows: idle panels on site (cost leak). "
        "Green rows: reuse occurring (savings active). "
        "Source: IS 1200 (1992); ACI 347R-14.",
        s["caption"],
    ))
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────
# PAGE 3 — Delivery Schedule
# ─────────────────────────────────────────────────────────────────
def _page3_delivery(story, styles, delivery_df):
    s = styles
    story.append(Paragraph("Procurement & Delivery Schedule", s["page_title"]))
    story.append(Paragraph(
        "Orders to place per week for site manager. "
        "Bold rows: delivery within 2 weeks of report date (action required).",
        s["caption"],
    ))
    story.append(HRFlowable(width="100%", thickness=0.8, color=_ORANGE, spaceAfter=6))

    if delivery_df is None or delivery_df.empty:
        story.append(Paragraph("No procurement rows (procure > 0) found.", s["body"]))
        story.append(PageBreak())
        return

    # Current calendar week (approximation)
    today_week = date.today().isocalendar().week

    header = ["SKU", "Week to Order", "Qty to Order",
              "Est. Delivery Wk", "Procurement Cost (Rs)"]
    rows = [header]
    urgent_rows = []

    for idx, row in delivery_df.iterrows():
        delivery_wk = int(row.get("estimated_delivery_week", 0))
        data_row = [
            str(row.get("sku", "")),
            str(int(row.get("week", 0))),
            str(int(row.get("procure", 0))),
            str(delivery_wk),
            f"{int(row.get('week_cost', 0)):,}",
        ]
        rows.append(data_row)
        ri = len(rows) - 1
        if delivery_wk <= today_week + 2:
            urgent_rows.append(ri)

    col_w = [2.5*cm, 3.0*cm, 3.0*cm, 3.5*cm, 4.2*cm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    ts = _header_style(col_w)

    for ri in urgent_rows:
        ts.append(("FONTNAME",   (0, ri), (-1, ri), "Helvetica-Bold"))
        ts.append(("BACKGROUND", (0, ri), (-1, ri), colors.HexColor("#FFF3E0")))

    tbl.setStyle(TableStyle(ts))
    story.append(tbl)
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Sorted by Week to Order ascending. "
        "Estimated Delivery Week = Order Week + transport buffer. "
        "PMBOK 7th ed. S.4.3: BoQ is a formal procurement document.",
        s["caption"],
    ))
    story.append(PageBreak())


# ─────────────────────────────────────────────────────────────────
# PAGE 4 — Methodology
# ─────────────────────────────────────────────────────────────────
def _page4_methodology(story, styles):
    s = styles
    story.append(Paragraph("Methodology & Academic References", s["page_title"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=_ORANGE, spaceAfter=8))

    refs = [
        (
            "Clustering — DBSCAN",
            "Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). "
            "\"A density-based algorithm for discovering clusters in large "
            "spatial databases with noise.\" KDD-96, AAAI Press, pp. 226-231. "
            "USE: Identifies floor-type clusters without pre-specifying k. "
            "Noise points (unique floors) are excluded from reuse eligibility.",
        ),
        (
            "Optimisation — Linear Programming",
            "Hillier, F.S., & Lieberman, G.J. (2021). Introduction to Operations "
            "Research (11th ed.). McGraw-Hill. Ch.3. "
            "USE: LP minimises total procurement + holding + idle cost over the "
            "52-week horizon subject to weekly demand-balance constraints. "
            "Also: Biruk, S., & Jaskowski, P. (2017). Archives of Civil Engineering, 63(1). "
            "USE: Validates per-week decision variable structure for construction scheduling.",
        ),
        (
            "Design Freeze — CV Method",
            "Ibbs, C.W. (1997). Quantitative impacts of project change. "
            "J. Construction Engineering and Management, 123(3), 308-311. "
            "USE: 60 projects — scope variance >15% gives 3x rework cost multiplier. "
            "FormOptiX sets DI=15% as the HALT threshold. "
            "Also: Montgomery, D.C. (2019). Introduction to Statistical Quality Control (8th ed.). "
            "USE: CV as a statistical uniformity proxy for floor geometry.",
        ),
        (
            "Formwork Standards",
            "ACI 347R-14. (2014). Guide to Formwork for Concrete. Section 2. "
            "USE: Formwork planning documentation requirements. "
            "Also: IS 1200 (Part 1). (1992). Method of Measurement of Building "
            "and Civil Engineering Works. Bureau of Indian Standards. "
            "USE: Defines BoQ column structure used in Indian construction procurement.",
        ),
        (
            "Procurement Documentation — PMBOK",
            "PMI. (2021). A Guide to the Project Management Body of Knowledge "
            "(PMBOK Guide, 7th ed.). Project Management Institute. "
            "Section 4.3: BoQ is a formal project procurement document — "
            "must be signable, dateable, and transferable to a vendor.",
        ),
    ]

    for ref_title, ref_text in refs:
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(ref_title, s["ref_title"]))
        story.append(Paragraph(ref_text, s["ref_body"]))

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "FormOptiX \u2014 CreaTech '26 \u00b7 L&T \u00b7 Problem Statement 4",
        ParagraphStyle(
            "fo_footer",
            fontSize=8, textColor=_GRAY,
            fontName="Helvetica-Oblique", alignment=TA_CENTER,
        ),
    ))


# ─────────────────────────────────────────────────────────────────
# PUBLIC FUNCTION
# ─────────────────────────────────────────────────────────────────

# PDF generation — IS 1200 (1992) BoQ format
# PMBOK 7th ed. S.4.3: BoQ is a formal procurement document.
# reportlab: BSD-licensed, no external server needed.
def generate_boq_pdf(
    boq_df: pd.DataFrame,
    delivery_df: pd.DataFrame,
    metrics: dict,
    project_name: str = "FormOptiX Project",
) -> bytes:
    """
    Generate a 4-page PDF Bill of Quantities report.

    Parameters
    ----------
    boq_df       : Full BoQ DataFrame (all SKUs, all weeks).
                   Expected columns: sku, week, procure, reuse, hold,
                   idle, week_cost. cumulative_cost is added if missing.
    delivery_df  : Delivery schedule DataFrame (rows where procure > 0).
                   Expected columns: sku, week, procure,
                   estimated_delivery_week, week_cost.
    metrics      : dict with keys:
                     optimized_cr  — optimised total cost (Rs Cr)
                     baseline_cr   — baseline cost (Rs Cr)
                     savings_cr    — total savings (Rs Cr)
                     savings_pct   — savings as percentage
                     overall_reuse_rate — 0..1 float
                     di_value      — Design Instability Index (%)
                     di_status     — "SAFE" | "WARNING" | "HALT"
    project_name : String for the PDF header subtitle.

    Returns
    -------
    bytes : PDF content (can be passed directly to st.download_button).

    Academic basis
    --------------
    IS 1200 (Part 1, 1992) — BoQ column structure.
    PMBOK 7th ed. S.4.3   — BoQ as formal procurement document.
    ACI 347R-14 S.2       — Formwork documentation requirements.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title=f"FormOptiX BoQ — {project_name}",
        author="FormOptiX Engine",
        subject="Bill of Quantities — Formwork Procurement",
    )

    s = _styles()
    story = []

    _page1_summary(story, s, metrics, project_name)
    _page2_boq(story, s, boq_df)
    _page3_delivery(story, s, delivery_df)
    _page4_methodology(story, s)

    doc.build(story)
    return buffer.getvalue()
