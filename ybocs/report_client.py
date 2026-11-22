"""Client-facing Y-BOCS PDF report: supportive, plain-language, no raw
item-level clinical formulation.

Per clinic policy, report structure/narrative is ALWAYS in English,
regardless of which language the client completed the assessment in. The
one exception is the item-by-item Q&A appendix at the end, which reflects
the client's actual answer wording (Arabic if they answered in Arabic) so
the record matches what was actually read and answered - see
answer_language and build_qa_appendix in pdf_base.py.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)

from .pdf_base import (
    base_styles, header_footer, NAVY, SLATE, GOLD, LINE_GRAY, BG_PANEL,
    TEXT_DARK, BAND_COLORS, obsession_compulsion_chart, severity_gauge,
    category_endorsement_chart, build_qa_appendix,
)
from .content import BAND_DESCRIPTIONS


def _kv_table(rows, ss, col_widths=(1.9 * inch, 4.4 * inch)):
    label_bold = ParagraphStyle("lblb", parent=ss["BodySmall"], textColor=NAVY)
    data = [(Paragraph(label, label_bold), Paragraph(str(value), ss["Body"])) for label, value in rows]
    t = Table(data, colWidths=list(col_widths))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BG_PANEL),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def generate_client_pdf(client_info, scores, narrative, category_counts,
                         severity_answers=None, severity_items_display=None,
                         checklist_categories_display=None, checklist_answers=None,
                         answer_language="en", lang="en"):
    """client_info: {"name": str}. scores: dict from scoring.score_severity().
    narrative: dict from groq_utils.generate_client_narrative() JSON (always
    English). category_counts: list from scoring.checklist_category_counts(),
    using the ENGLISH category labels (charts are always English).

    severity_answers/severity_items_display/checklist_categories_display/
    checklist_answers/answer_language: optional - when given, an item-by-item
    Q&A appendix is appended in the client's own answer language, matching
    the therapist report's appendix. `lang` is accepted for backwards
    compatibility and is otherwise unused (report body is always English).
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        title="Y-BOCS Client Report",
    )
    ss = base_styles()
    story = []

    # ---------------- Cover ----------------
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Y-BOCS", ParagraphStyle(
        name="Brand", fontName="Helvetica-Bold", fontSize=14,
        textColor=GOLD, alignment=TA_CENTER, leading=18, spaceAfter=4)))
    story.append(Paragraph("Your Assessment Report", ParagraphStyle(
        name="BrandTitle", fontName="Helvetica-Bold", fontSize=26,
        textColor=NAVY, alignment=TA_CENTER, leading=32, spaceAfter=20)))
    story.append(HRFlowable(width="40%", thickness=1, color=GOLD, hAlign="CENTER", spaceAfter=24))

    client_name = client_info.get("name") or "Confidential Client"
    story.append(Paragraph(client_name, ParagraphStyle(
        name="ClientName", fontName="Helvetica-Bold", fontSize=17,
        textColor=TEXT_DARK, alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph(datetime.now().strftime("Assessment date: %B %d, %Y"), ParagraphStyle(
        name="ClientDate", fontName="Helvetica", fontSize=11,
        textColor=SLATE, alignment=TA_CENTER, spaceAfter=40)))

    band_label = scores["band"]
    story.append(Paragraph(f"{scores['total']}/40 — {band_label}", ParagraphStyle(
        name="PrimaryBanner", fontName="Helvetica-Bold", fontSize=16,
        textColor=colors.white, alignment=TA_CENTER,
        backColor=colors.HexColor(BAND_COLORS.get(band_label, "#1B2A4A")),
        borderPadding=(10, 14, 10, 14), leading=20)))
    story.append(Spacer(1, 1.1 * inch))
    story.append(Paragraph(
        "This report is a tool to support your work with your therapist. It is not, on its own, a "
        "medical or psychiatric diagnosis.",
        ss["CoverFooter"]))
    story.append(PageBreak())

    # ---------------- Summary ----------------
    story.append(Paragraph("Your Results Summary", ss["SectionHeader"]))
    rows = [
        ("Obsessions subtotal", f"{scores['obsession_subtotal']}/20"),
        ("Compulsions subtotal", f"{scores['compulsion_subtotal']}/20"),
        ("Total score", f"{scores['total']}/40"),
        ("Level", band_label),
    ]
    story.append(_kv_table(rows, ss))
    story.append(Spacer(1, 10))

    band_desc = BAND_DESCRIPTIONS["en"].get(band_label, "")
    story.append(Paragraph(band_desc, ss["Body"]))
    story.append(Spacer(1, 10))

    story.append(obsession_compulsion_chart(scores["obsession_subtotal"], scores["compulsion_subtotal"], lang="en"))
    story.append(Spacer(1, 6))
    story.append(severity_gauge(scores["total"], band_label, lang="en"))

    # ---------------- AI narrative ----------------
    story.append(PageBreak())
    story.append(Paragraph("What Your Results Show", ss["SectionHeader"]))

    if narrative:
        sec_titles = {
            "overview": "Overview", "what_stood_out": "What Stood Out",
            "strengths_noted": "Strengths We Noticed", "next_steps": "Next Steps",
        }
        for key in ("overview", "what_stood_out", "strengths_noted", "next_steps"):
            text = narrative.get(key)
            if not text:
                continue
            story.append(Paragraph(sec_titles[key], ss["SubHeader"]))
            story.append(Paragraph(text, ss["Body"]))
    else:
        story.append(Paragraph(
            "A narrative summary could not be generated for this report — please review the "
            "results above directly with your therapist.",
            ss["Body"]))

    # ---------------- Themes (category chart) ----------------
    cat_chart = category_endorsement_chart(category_counts, lang="en")
    if cat_chart:
        story.append(PageBreak())
        story.append(Paragraph("Themes From Your Symptom Checklist", ss["SectionHeader"]))
        story.append(Paragraph(
            "The chart below shows how many items you marked in each category of the Symptom Checklist.",
            ss["BodySmall"]))
        story.append(Spacer(1, 6))
        story.append(cat_chart)

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.6, color=LINE_GRAY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This report is confidential and was prepared to support your therapy sessions. It does not "
        "replace direct clinical discussion with your therapist.",
        ss["BodySmall"]))

    # ---------------- Q&A appendix (answer-language wording) ----------------
    if severity_answers is not None and severity_items_display is not None \
            and checklist_categories_display is not None and checklist_answers is not None:
        story.extend(build_qa_appendix(
            ss, severity_answers, severity_items_display, checklist_categories_display,
            checklist_answers, answer_language=answer_language,
        ))

    generated_text = f"Generated {datetime.now().strftime('%B %d, %Y')}"
    doc.build(
        story,
        onFirstPage=header_footer("Y-BOCS Client Report", "Confidential", generated_text, "Page"),
        onLaterPages=header_footer("Y-BOCS Client Report", "Confidential", generated_text, "Page"),
    )
    return buf.getvalue()
