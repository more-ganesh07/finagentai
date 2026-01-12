# pdf_builder.py
import os
import datetime as dt
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak

# Proper page break
from reportlab.platypus import PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .utils import inr, _get, as_list


def build_eod_pdf(payload: Dict[str, Any], out_path: str):
    """
    Build a small 2-page EOD PDF:
      - Page 1: summary KPIs + top holdings
      - Page 2: day positions + mutual funds
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm
    )
    styles = getSampleStyleSheet()
    styles["Normal"].fontSize = 10
    styles["Heading1"].fontSize = 16
    styles["Heading2"].fontSize = 12

    story: List[Any] = []

    # --- Guard: handle empty or invalid payload ---
    if not payload or not any(payload.values()):
        story.append(Paragraph("EOD Portfolio Report", styles["Heading1"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "No portfolio data available. Please complete login once and re-run.",
            styles["Normal"],
        ))
        doc.build(story)
        print("⚠️ Skipping empty PDF — no data to render.")
        return


        # Handle empty or invalid payload gracefully
    if not payload or not any(payload.values()):
        story.append(Paragraph("EOD Portfolio Report", styles["Heading1"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "No portfolio data available for this session. "
            "Please ensure Kite MCP is logged in before generating the report.",
            styles["Normal"],
        ))
        doc.build(story)
        return


    # ----- Page 1 -----
    today = dt.date.today().strftime("%d %b %Y")
    profile = payload.get("profile", {})
    margins = payload.get("margins", {})
    holds = payload.get("holdings", {})
    poss = payload.get("positions", {})
    mfs = payload.get("mfs", {})

    user_name = _get(profile, "data", "user_name", default="User")
    broker = _get(profile, "data", "broker", default="")

    story.append(Paragraph(f"EOD Portfolio Brief — {today}", styles["Heading1"]))
    story.append(Paragraph(f"{user_name}  •  {broker}", styles["Normal"]))
    story.append(Spacer(1, 8))

    # KPIs
    hold_rows = as_list(holds.get("data"))
    total_mv = sum(float(h.get("ltp", 0.0)) * float(h.get("qty", 0.0))
                   for h in hold_rows if isinstance(h, dict))
    total_pnl = sum(float(h.get("pnl", 0.0)) for h in hold_rows if isinstance(h, dict))

    eq_cash = (
        _get(margins, "data", "equity", "available", "cash", default=None)
        or _get(margins, "data", "available", "cash", default=0.0)
    )

    kpi_tbl = Table(
        [
            ["Total Portfolio Value", inr(total_mv)],
            ["Total P&L (approx)", inr(total_pnl)],
            ["Cash Available (Equity)", inr(eq_cash)],
        ],
        colWidths=[80*mm, 70*mm]
    )
    kpi_tbl.setStyle(TableStyle([
        ("FONT", (0,0), (-1,-1), "Helvetica", 10),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 12))

    # Holdings (top)
    story.append(Paragraph("Equity Holdings (top)", styles["Heading2"]))
    h_rows = [["Symbol", "Qty", "Avg", "LTP", "P&L"]]
    for h in hold_rows[:8]:
        if not isinstance(h, dict):
            continue
        h_rows.append([
            h.get("symbol") or h.get("tradingsymbol") or "",
            f"{h.get('qty', 0):.0f}",
            inr(h.get("avg", h.get("average_price", 0))),
            inr(h.get("ltp", h.get("last_price", 0))),
            inr(h.get("pnl", 0)),
        ])
    if len(h_rows) == 1:
        h_rows.append(["—", "—", "—", "—", "—"])
    tbl = Table(h_rows, colWidths=[35*mm, 15*mm, 30*mm, 30*mm, 30*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("FONT", (0,0), (-1,-1), "Helvetica", 9),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(tbl)

    story.append(Spacer(1, 14))
    story.append(Paragraph("Notes", styles["Heading2"]))
    story.append(Paragraph(
        "This is an auto-generated daily snapshot. Values are approximate. "
        "Mutual funds and day positions are included on the next page.",
        styles["Normal"],
    ))

    # Page break (simple spacer)
    story.append(PageBreak())

    # ----- Page 2 -----
    # Positions
    story.append(Paragraph("Day Positions", styles["Heading2"]))
    pos_rows = as_list(poss.get("data"))
    p_rows = [["Symbol", "Qty", "P&L"]]
    for p in pos_rows[:10]:
        if not isinstance(p, dict):
            continue
        p_rows.append([
            p.get("symbol") or p.get("tradingsymbol") or "",
            f"{p.get('qty', 0):.0f}",
            inr(p.get("pnl", 0)),
        ])
    if len(p_rows) == 1:
        p_rows.append(["—", "—", "—"])
    ptbl = Table(p_rows, colWidths=[50*mm, 20*mm, 25*mm])
    ptbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("FONT", (0,0), (-1,-1), "Helvetica", 9),
    ]))
    story.append(ptbl)

    story.append(Spacer(1, 12))

    # Mutual Funds
    story.append(Paragraph("Mutual Funds", styles["Heading2"]))
    mf_rows = as_list(mfs.get("data"))
    m_rows = [["Scheme", "Units", "AVG", "NAV", "Value", "Gain%"]]
    for m in mf_rows[:10]:
        if not isinstance(m, dict):
            continue
        m_rows.append([
            (m.get("scheme") or "")[:38],
            f"{m.get('units', 0):.2f}",
            inr(m.get("avg_nav", 0)),
            inr(m.get("nav", 0)),
            inr(m.get("value", 0)),
            f"{float(m.get('gain_pct', 0.0)):.2f}%",
        ])
    if len(m_rows) == 1:
        m_rows.append(["—", "—", "—", "—", "—", "—"])
    mtbl = Table(m_rows, colWidths=[70*mm, 20*mm, 20*mm, 20*mm, 25*mm, 20*mm])
    mtbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("FONT", (0,0), (-1,-1), "Helvetica", 8.5),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(mtbl)

    doc.build(story)
