"""Therapist-only confidential Y-BOCS report: full clinical formulation,
differential considerations, symptom-dimension breakdown, treatment
recommendations, session material, and a complete item-by-item appendix.

Narrative/section headers always render in English (clinical documentation
convention). The appendix reflects the client's actual answer wording in
whichever language they completed the assessment in (with Arabic
shaping/RTL applied when relevant) - see answer_language.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, ListFlowable, ListItem,
)

from .pdf_base import (
    base_styles, header_footer, ar, NAVY, SLATE, SLATE_LIGHT, GOLD, LINE_GRAY,
    BG_PANEL, TEXT_DARK, BAND_COLORS, obsession_compulsion_chart, severity_gauge,
    severity_items_chart, category_endorsement_chart, build_qa_appendix,
)
from .content import BAND_DESCRIPTIONS, SYMPTOM_DIMENSIONS


def _bullets(items, style):
    return ListFlowable(
        [ListItem(Paragraph(t, style), leftIndent=10, bulletColor=GOLD) for t in items],
        bulletType="bullet", start="•", leftIndent=14,
    )


def generate_therapist_pdf(client_info, scores, severity_answers, severity_items,
                            category_counts, checklist_categories, checklist_answers,
                            intervention, answer_language="en", severity_items_display=None):
    """intervention: dict from groq_utils.generate_therapist_intervention() JSON,
    or None if generation failed (report still builds with the raw data).

    severity_items: ALWAYS the English item bank - drives the (always-English)
    severity chart. severity_items_display: the item bank in the client's own
    answer language, used only for Appendix A's wording; defaults to
    severity_items (English) when not given."""
    severity_items_display = severity_items_display or severity_items
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        title="Y-BOCS Therapist Confidential Report",
    )
    ss = base_styles()
    story = []
    client_name = client_info.get("name") or "Confidential Client"
    band_label = scores["band"]

    # ---------------- Cover ----------------
    story.append(Spacer(1, 1.3 * inch))
    story.append(Paragraph("CONFIDENTIAL — PRACTITIONER ONLY", ParagraphStyle(
        "ConfBanner", fontName="Helvetica-Bold", fontSize=11, textColor=colors.white,
        alignment=TA_CENTER, backColor=colors.HexColor("#9B3B3B"),
        borderPadding=(8, 12, 8, 12), leading=14)))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Y-BOCS", ParagraphStyle(
        "Brand", fontName="Helvetica-Bold", fontSize=14, textColor=GOLD,
        alignment=TA_CENTER, leading=18, spaceAfter=4)))
    story.append(Paragraph("Intervention &amp; Session Planning Report", ParagraphStyle(
        "BrandTitle", fontName="Helvetica-Bold", fontSize=25, textColor=NAVY,
        alignment=TA_CENTER, leading=30, spaceAfter=18)))
    story.append(HRFlowable(width="40%", thickness=1, color=GOLD, hAlign="CENTER", spaceAfter=22))
    story.append(Paragraph(client_name, ParagraphStyle(
        "ClientName", fontName="Helvetica-Bold", fontSize=17, textColor=TEXT_DARK,
        alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph(datetime.now().strftime("Assessment date: %B %d, %Y"), ParagraphStyle(
        "ClientDate", fontName="Helvetica", fontSize=11, textColor=SLATE,
        alignment=TA_CENTER, spaceAfter=36)))
    story.append(Paragraph(
        f"Total: {scores['total']}/40 — {band_label}  "
        f"(Obsessions {scores['obsession_subtotal']}/20 · Compulsions {scores['compulsion_subtotal']}/20)",
        ParagraphStyle("PrimaryBanner", fontName="Helvetica-Bold", fontSize=14, textColor=colors.white,
                       alignment=TA_CENTER, backColor=colors.HexColor(BAND_COLORS.get(band_label, "#1B2A4A")),
                       borderPadding=(10, 14, 10, 14), leading=18)))
    story.append(Spacer(1, 1.0 * inch))
    story.append(Paragraph(
        "This content is hypothesis-generating to support clinical decision-making, not a diagnosis. "
        "It is intended solely for the treating clinician's confidential use and should never be shared "
        "with the client unedited.",
        ss["CoverFooter"]))
    story.append(PageBreak())

    # ---------------- Clinical summary table ----------------
    story.append(Paragraph("Clinical Summary", ss["SectionHeader"]))
    insight_labels = {0: "Good", 1: "Fair", 2: "Fair-poor", 3: "Poor", 4: "Absent (delusional)"}
    summary_rows = [
        ["Obsessions Subtotal (items 1–5)", f"{scores['obsession_subtotal']}/20"],
        ["Compulsions Subtotal (items 6–10)", f"{scores['compulsion_subtotal']}/20"],
        ["Total Severity Score", f"{scores['total']}/40 — {band_label}"],
        ["Insight (item 11)", f"{scores['insight']}/4 — {insight_labels.get(scores['insight'], 'n/a')}"],
        ["Answer language", "Arabic" if answer_language == "ar" else "English"],
    ]
    t = Table(summary_rows, colWidths=[2.6 * inch, 3.7 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BG_PANEL),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.3),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))
    band_desc = BAND_DESCRIPTIONS["en"].get(band_label, "")
    story.append(Paragraph(band_desc, ss["Body"]))

    # ---------------- Charts ----------------
    story.append(PageBreak())
    story.append(Paragraph("Severity Item Breakdown", ss["SectionHeader"]))
    story.append(severity_items_chart(severity_answers, severity_items, lang="en"))
    story.append(Spacer(1, 10))
    story.append(obsession_compulsion_chart(scores["obsession_subtotal"], scores["compulsion_subtotal"], lang="en"))
    story.append(Spacer(1, 6))
    story.append(severity_gauge(scores["total"], band_label, lang="en"))

    cat_chart = category_endorsement_chart(category_counts, lang="en")
    if cat_chart:
        story.append(Spacer(1, 14))
        story.append(Paragraph("Symptom Checklist — Category Endorsement", ss["SectionHeader"]))
        story.append(cat_chart)

    # ---------------- LLM-generated clinical content ----------------
    if intervention:
        cf = intervention.get("clinical_formulation", {})
        story.append(PageBreak())
        story.append(Paragraph("Clinical Formulation", ss["SectionHeader"]))
        for key, label in [
            ("symptom_pattern_summary", "Symptom Pattern"),
            ("functional_impact", "Functional Impact"),
            ("insight_level", "Insight"),
            ("maintaining_factors", "Likely Maintaining Factors"),
        ]:
            val = cf.get(key)
            if val:
                story.append(Paragraph(label, ss["SubHeader"]))
                story.append(Paragraph(val, ss["Body"]))

        risk = cf.get("risk_flags")
        if risk:
            story.append(Spacer(1, 6))
            story.append(Paragraph("⚠ RISK SCREENING NOTE: " + risk, ss["RiskFlag"]))

        diffs = intervention.get("differential_considerations") or []
        if diffs:
            story.append(Paragraph("Differential Considerations", ss["SectionHeader"]))
            story.append(_bullets(diffs, ss["YBullet"]))

        dims = intervention.get("symptom_dimension_breakdown") or []
        if dims:
            story.append(PageBreak())
            story.append(Paragraph("Symptom Dimension Breakdown", ss["SectionHeader"]))
            dim_rows = [["Dimension", "Relevance", "Clinical Note"]]
            for d in dims:
                dim_rows.append([
                    Paragraph(d.get("dimension", ""), ss["BodySmall"]),
                    Paragraph(d.get("relevance", ""), ss["BodySmall"]),
                    Paragraph(d.get("clinical_note", ""), ss["BodySmall"]),
                ])
            dt = Table(dim_rows, colWidths=[1.5 * inch, 2.6 * inch, 2.2 * inch])
            dt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE9E3")),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ]))
            story.append(dt)

        strengths = intervention.get("strengths_and_resources") or []
        if strengths:
            story.append(Spacer(1, 12))
            story.append(Paragraph("Strengths & Resources", ss["SectionHeader"]))
            story.append(_bullets(strengths, ss["YBullet"]))

        recs = intervention.get("treatment_recommendations") or []
        if recs:
            story.append(PageBreak())
            story.append(Paragraph("Treatment Recommendations", ss["SectionHeader"]))
            rec_rows = [["Modality", "Priority", "Rationale", "Implementation Note"]]
            for r in recs:
                rec_rows.append([
                    Paragraph(r.get("modality", ""), ss["BodySmall"]),
                    Paragraph(r.get("priority", ""), ss["BodySmall"]),
                    Paragraph(r.get("rationale", ""), ss["BodySmall"]),
                    Paragraph(r.get("implementation_note", ""), ss["BodySmall"]),
                ])
            rt = Table(rec_rows, colWidths=[1.3 * inch, 0.8 * inch, 2.1 * inch, 2.1 * inch])
            rt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE9E3")),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ]))
            story.append(rt)

        sq = intervention.get("session_questions") or []
        if sq:
            story.append(Spacer(1, 14))
            story.append(Paragraph("Suggested Session Questions", ss["SectionHeader"]))
            story.append(_bullets(sq, ss["YBullet"]))

        roadmap = intervention.get("session_roadmap") or []
        if roadmap:
            story.append(PageBreak())
            story.append(Paragraph("Session Roadmap", ss["SectionHeader"]))
            rm_rows = [["Phase", "Focus"]]
            for p in roadmap:
                rm_rows.append([
                    Paragraph(p.get("phase", ""), ss["BodySmall"]),
                    Paragraph(p.get("focus", ""), ss["BodySmall"]),
                ])
            rmt = Table(rm_rows, colWidths=[1.8 * inch, 4.5 * inch])
            rmt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE9E3")),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            story.append(rmt)
    else:
        story.append(PageBreak())
        story.append(Paragraph("Clinical Formulation", ss["SectionHeader"]))
        story.append(Paragraph(
            "Automated clinical formulation could not be generated for this submission "
            "(AI service unavailable). Raw scores, charts, and the full item-by-item appendix below "
            "remain complete and accurate.",
            ss["Body"]))

    # ---------------- Appendix: full item-by-item data ----------------
    # Shared with the client report - section headers stay English always;
    # only item wording reflects the client's actual answer language.
    story.extend(build_qa_appendix(
        ss, severity_answers, severity_items_display, checklist_categories,
        checklist_answers, answer_language=answer_language,
    ))

    generated_text = f"Generated {datetime.now().strftime('%B %d, %Y')}"
    doc.build(
        story,
        onFirstPage=header_footer("Y-BOCS Therapist Report", "Confidential — Practitioner Only", generated_text, "Page"),
        onLaterPages=header_footer("Y-BOCS Therapist Report", "Confidential — Practitioner Only", generated_text, "Page"),
    )
    return buf.getvalue()
