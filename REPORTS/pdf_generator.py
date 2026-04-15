"""
REPORTS/pdf_generator.py
Professional SAR PDF report generator using ReportLab
"""
from __future__ import annotations
import os
import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus import Image as RLImage
from reportlab.lib.colors import HexColor
from loguru import logger

# ─── Color palette ────────────────────────────────────────────────────────────
C_NAVY     = HexColor("#1a237e")
C_BLUE     = HexColor("#283593")
C_ACCENT   = HexColor("#1976d2")
C_RED      = HexColor("#c62828")
C_ORANGE   = HexColor("#e65100")
C_GREEN    = HexColor("#2e7d32")
C_GREY_BG  = HexColor("#f5f5f5")
C_GREY_TXT = HexColor("#555555")
C_WHITE    = colors.white
C_BLACK    = colors.black

RISK_COLORS = {"HIGH": C_RED, "MEDIUM": C_ORANGE, "LOW": C_GREEN}


def _styles():
    base = getSampleStyleSheet()
    return {
        "title":    ParagraphStyle("title",    fontSize=18, textColor=C_WHITE,
                                   fontName="Helvetica-Bold", alignment=TA_CENTER,
                                   spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontSize=10, textColor=HexColor("#bbdefb"),
                                   fontName="Helvetica", alignment=TA_CENTER),
        "section":  ParagraphStyle("section",  fontSize=11, textColor=C_NAVY,
                                   fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
                                   borderPad=4),
        "body":     ParagraphStyle("body",     fontSize=9,  textColor=C_GREY_TXT,
                                   fontName="Helvetica", leading=14, alignment=TA_JUSTIFY),
        "mono":     ParagraphStyle("mono",     fontSize=8,  textColor=C_GREY_TXT,
                                   fontName="Courier", leading=12),
        "label":    ParagraphStyle("label",    fontSize=8,  textColor=C_GREY_TXT,
                                   fontName="Helvetica"),
        "value":    ParagraphStyle("value",    fontSize=9,  textColor=C_BLACK,
                                   fontName="Helvetica-Bold"),
        "footer":   ParagraphStyle("footer",   fontSize=7,  textColor=HexColor("#999999"),
                                   fontName="Helvetica", alignment=TA_CENTER),
        "risk_high":ParagraphStyle("risk_h",   fontSize=11, textColor=C_RED,
                                   fontName="Helvetica-Bold"),
        "risk_med": ParagraphStyle("risk_m",   fontSize=11, textColor=C_ORANGE,
                                   fontName="Helvetica-Bold"),
        "risk_low": ParagraphStyle("risk_l",   fontSize=11, textColor=C_GREEN,
                                   fontName="Helvetica-Bold"),
    }


def _header_table(verdict: dict, styles: dict) -> Table:
    """Dark navy header box."""
    txn_id    = verdict.get("transaction_id", "N/A")
    risk_lvl  = verdict.get("risk_level",     "N/A")
    today     = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    sar_id    = f"SAR-{datetime.now().strftime('%Y%m%d')}-{txn_id[:8].upper()}"

    data = [[
        Paragraph("PROOFSAR AI — REGULATORY COMPLIANCE", styles["title"]),
        Paragraph("", styles["title"]),
    ], [
        Paragraph("Suspicious Transaction Report (STR) — Form 102 (India)", styles["subtitle"]),
        Paragraph(f"FIU-IND REF: {sar_id}", styles["subtitle"]),
    ]]
    t = Table(data, colWidths=["60%", "40%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), C_NAVY),
        ("TOPPADDING",  (0,0), (-1,-1), 12),
        ("BOTTOMPADDING",(0,0),(-1,-1), 12),
        ("LEFTPADDING", (0,0), (-1,-1), 16),
        ("RIGHTPADDING",(0,0), (-1,-1), 16),
        ("GRID",        (0,0), (-1,-1), 0, C_NAVY),
    ]))
    return t


def _info_table(verdict: dict, styles: dict) -> Table:
    """Key-value info table with alternating rows."""
    meta     = verdict.get("metadata", {})
    amount   = float(meta.get("amount",   0))
    channel  = meta.get("channel",  "N/A")
    location = meta.get("location", "N/A")
    risk_sc  = float(verdict.get("risk_score", 0))
    risk_lvl = verdict.get("risk_level", "N/A")
    acc      = verdict.get("account_id", "N/A")
    txn_id   = verdict.get("transaction_id", "N/A")
    today    = datetime.now(timezone.utc).strftime("%d %B %Y")
    color    = RISK_COLORS.get(risk_lvl, C_BLACK)

    rows = [
        ["Field",            "Value"],
        ["Transaction ID",   txn_id],
        ["Account ID",       acc],
        ["Amount",           f"INR {amount:,.2f}"],
        ["Channel",          channel],
        ["Location",         location],
        ["Date of Detection", today],
        ["Risk Score",       f"{risk_sc:.2%}"],
        ["Risk Level",       risk_lvl],
        ["Reporting Entity", "ProofSAR Digital Assets Ltd. (FIN-99238)"],
    ]

    table_data = []
    for i, (k, v) in enumerate(rows):
        if i == 0:
            table_data.append([
                Paragraph(k, ParagraphStyle("hk", fontSize=9, fontName="Helvetica-Bold",
                                            textColor=C_WHITE)),
                Paragraph(v, ParagraphStyle("hv", fontSize=9, fontName="Helvetica-Bold",
                                            textColor=C_WHITE))
            ])
        elif k == "Risk Level":
            table_data.append([
                Paragraph(k, styles["label"]),
                Paragraph(v, ParagraphStyle("rv", fontSize=9, fontName="Helvetica-Bold",
                                            textColor=color))
            ])
        elif k == "Risk Score":
            table_data.append([
                Paragraph(k, styles["label"]),
                Paragraph(v, ParagraphStyle("rsv", fontSize=9, fontName="Helvetica-Bold",
                                            textColor=color))
            ])
        else:
            table_data.append([
                Paragraph(k, styles["label"]),
                Paragraph(str(v), styles["value"])
            ])

    t = Table(table_data, colWidths=["35%", "65%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),   C_ACCENT),
        ("BACKGROUND",   (0,1), (-1,1),   C_GREY_BG),
        ("BACKGROUND",   (0,3), (-1,3),   C_GREY_BG),
        ("BACKGROUND",   (0,5), (-1,5),   C_GREY_BG),
        ("BACKGROUND",   (0,7), (-1,7),   C_GREY_BG),
        ("GRID",         (0,0), (-1,-1),  0.5, HexColor("#e0e0e0")),
        ("TOPPADDING",   (0,0), (-1,-1),  6),
        ("BOTTOMPADDING",(0,0), (-1,-1),  6),
        ("LEFTPADDING",  (0,0), (-1,-1),  10),
        ("RIGHTPADDING", (0,0), (-1,-1),  10),
        ("VALIGN",       (0,0), (-1,-1),  "MIDDLE"),
    ]))
    return t


def _risk_indicators_table(top_reasons: list, styles: dict) -> Table:
    """SHAP-based risk indicators table."""
    rows = [["#", "Risk Indicator", "Direction", "Impact"]]
    for i, r in enumerate(top_reasons[:5], 1):
        direction = r.get("direction", "")
        impact    = f"{r.get('importance', 0):.4f}"
        dir_text  = "↑ Increases Risk" if direction == "risk_increasing" else "↓ Decreases Risk"
        rows.append([str(i), r.get("reason", r.get("description", "N/A")), dir_text, impact])

    t = Table(rows, colWidths=["5%", "60%", "22%", "13%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),   C_NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0),   C_WHITE),
        ("FONTNAME",      (0,0), (-1,0),   "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1),  8),
        ("FONTNAME",      (0,1), (-1,-1),  "Helvetica"),
        ("TEXTCOLOR",     (0,1), (-1,-1),  C_GREY_TXT),
        ("ROWBACKGROUNDS",(0,1), (-1,-1),  [C_WHITE, C_GREY_BG]),
        ("GRID",          (0,0), (-1,-1),  0.4, HexColor("#e0e0e0")),
        ("TOPPADDING",    (0,0), (-1,-1),  5),
        ("BOTTOMPADDING", (0,0), (-1,-1),  5),
        ("LEFTPADDING",   (0,0), (-1,-1),  8),
        ("ALIGN",         (0,0), (0,-1),   "CENTER"),
        ("ALIGN",         (3,0), (3,-1),   "CENTER"),
    ]))
    return t


def _legal_table(violations: list, styles: dict) -> Table:
    """Legal violations table."""
    if not violations:
        return Paragraph("No specific violations mapped.", styles["body"])

    rows = [["Regulation", "Section", "Description"]]
    for v in violations:
        rows.append([v.get("act","PMLA 2002"),
                     v.get("section","N/A"),
                     v.get("description","N/A")])

    t = Table(rows, colWidths=["25%", "25%", "50%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),   C_ACCENT),
        ("TEXTCOLOR",     (0,0), (-1,0),   C_WHITE),
        ("FONTNAME",      (0,0), (-1,0),   "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1),  8),
        ("FONTNAME",      (0,1), (-1,-1),  "Helvetica"),
        ("TEXTCOLOR",     (0,1), (-1,-1),  C_GREY_TXT),
        ("ROWBACKGROUNDS",(0,1), (-1,-1),  [C_WHITE, C_GREY_BG]),
        ("GRID",          (0,0), (-1,-1),  0.4, HexColor("#e0e0e0")),
        ("TOPPADDING",    (0,0), (-1,-1),  5),
        ("BOTTOMPADDING", (0,0), (-1,-1),  5),
        ("LEFTPADDING",   (0,0), (-1,-1),  8),
        ("VALIGN",        (0,0), (-1,-1),  "TOP"),
    ]))
    return t


def generate_pdf(
    verdict: dict,
    sar_text: str,
    audit_hash: str = "",
    shap_chart_path: str = None,
    output_path: str = None
) -> bytes:
    """
    Generate a complete SAR PDF report.
    Returns raw PDF bytes. Also saves to output_path if provided.
    """
    styles    = _styles()
    buf       = io.BytesIO()
    doc       = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(_header_table(verdict, styles))
    story.append(Spacer(1, 12))

    # ── Transaction Info ────────────────────────────────────────────────────
    story.append(Paragraph("SECTION 1 — TRANSACTION INFORMATION", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT))
    story.append(Spacer(1, 6))
    story.append(_info_table(verdict, styles))
    story.append(Spacer(1, 12))

    # ── Risk Indicators ─────────────────────────────────────────────────────
    story.append(Paragraph("SECTION 2 — AI RISK INDICATORS (SHAP Analysis)", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT))
    story.append(Spacer(1, 6))
    top_reasons = verdict.get("top_reasons", [])
    if top_reasons:
        story.append(_risk_indicators_table(top_reasons, styles))
    else:
        story.append(Paragraph("SHAP analysis not available for this transaction.", styles["body"]))

    # ── SHAP chart ──────────────────────────────────────────────────────────
    if shap_chart_path and os.path.exists(shap_chart_path):
        story.append(Spacer(1, 8))
        img = RLImage(shap_chart_path, width=16*cm, height=7*cm)
        story.append(img)

    story.append(Spacer(1, 12))

    # ── Legal Mapping ───────────────────────────────────────────────────────
    story.append(Paragraph("SECTION 3 — LEGAL & REGULATORY MAPPING", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT))
    story.append(Spacer(1, 6))
    violations = verdict.get("legal_violations", [])
    story.append(_legal_table(violations, styles))
    story.append(Spacer(1, 12))

    # ── SAR Narrative ───────────────────────────────────────────────────────
    story.append(Paragraph("SECTION 4 — SAR NARRATIVE", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT))
    story.append(Spacer(1, 6))
    # Clean SAR text for PDF
    clean_sar = sar_text.replace("╔","").replace("╚","").replace("╗","").replace("╝","") \
                        .replace("║","").replace("━","─").replace("═","─")
    for line in clean_sar.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
        elif line.startswith("SECTION") or line.startswith("─"):
            story.append(Paragraph(f"<b>{line}</b>", styles["body"]))
        else:
            story.append(Paragraph(line, styles["body"]))

    story.append(Spacer(1, 16))

    # ── Audit Chain ─────────────────────────────────────────────────────────
    story.append(Paragraph("SECTION 5 — AUDIT INTEGRITY", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT))
    story.append(Spacer(1, 6))
    audit_rows = [
        ["Audit Hash (SHA-256)", audit_hash or "N/A"],
        ["Generated At", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")],
        ["System",       "ProofSAR AI v1.0.0"],
        ["Compliance",   "PMLA 2002 | RBI AML/CFT Guidelines | FATF"],
    ]
    at = Table(audit_rows, colWidths=["30%", "70%"])
    at.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (1,0), (1,-1), "Courier"),
        ("FONTSIZE",  (0,0), (-1,-1), 8),
        ("TEXTCOLOR", (0,0), (0,-1), C_GREY_TXT),
        ("TEXTCOLOR", (1,0), (1,-1), C_NAVY),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[C_WHITE, C_GREY_BG]),
        ("GRID",      (0,0), (-1,-1), 0.4, HexColor("#e0e0e0")),
        ("TOPPADDING",(0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
    ]))
    story.append(at)
    story.append(Spacer(1, 24))

    # ── Sign-off ────────────────────────────────────────────────────────────
    story.append(Paragraph("SECTION 6 — AUTHORIZATION", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT))
    story.append(Spacer(1, 12))
    sig_data = [[
        Paragraph("__________________________<br/>Principal Officer Signature", styles["body"]),
        Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}<br/>Place: Mumbai, India", styles["body"])
    ]]
    st_sig = Table(sig_data, colWidths=["60%", "40%"])
    story.append(st_sig)
    story.append(Spacer(1, 20))

    # ── Footer ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "CONFIDENTIAL — FOR REGULATORY USE ONLY | This report was auto-generated by ProofSAR AI "
        "and must be reviewed by a qualified AML Compliance Officer before submission to FIU-IND.",
        styles["footer"]
    ))

    doc.build(story)
    pdf_bytes = buf.getvalue()

    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        logger.success(f"PDF saved → {output_path}")

    return pdf_bytes
