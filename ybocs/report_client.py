"""Client-facing Y-BOCS PDF report: supportive, plain-language, no raw
item-by-item clinical data dump. Fully bilingual - renders entirely in
English or entirely in Arabic (RTL) depending on the language the client
used to complete the assessment."""

import io
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)

from .pdf_base import (
    base_styles, header_footer, ar, NAVY, SLATE, GOLD, LINE_GRAY, BG_PANEL,
    TEXT_DARK, BAND_COLORS, obsession_compulsion_chart, severity_gauge,
    category_endorsement_chart,
)
from .content import BAND_DESCRIPTIONS, BAND_LABEL_AR


def _kv_table(rows, lang, ss, col_widths=(1.9 * inch, 4.4 * inch)):
    label_style = ss["ArBodySmall"] if lang == "ar" else ss["BodySmall"]
    value_style = ss["ArBody"] if lang == "ar" else ss["Body"]
    label_bold = ParagraphStyle("lblb", parent=label_style, fontName=label_style.fontName, textColor=NAVY)
    data = []
    for label, value in rows:
        lp = Paragraph(ar(label) if lang == "ar" else label, label_bold)
        vp = Paragraph(ar(str(value)) if lang == "ar" else str(value), value_style)
        data.append((vp, lp) if lang == "ar" else (lp, vp))
    widths = list(col_widths)[::-1] if lang == "ar" else list(col_widths)
    t = Table(data, colWidths=widths)
    label_col = 1 if lang == "ar" else 0
    t.setStyle(TableStyle([
        ("BACKGROUND", (label_col, 0), (label_col, -1), BG_PANEL),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def generate_client_pdf(client_info, scores, narrative, category_counts, lang="en"):
    """client_info: {"name": str}. scores: dict from scoring.score_severity().
    narrative: dict from groq_utils.generate_client_narrative() JSON.
    category_counts: list from scoring.checklist_category_counts().
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
    ar_mode = (lang == "ar")

    title_style = ss["ArTitle"] if ar_mode else ss["ReportTitle"]
    sub_style = ss["ArBody"] if ar_mode else ss["ReportSubtitle"]
    section_style = ss["ArSectionHeader"] if ar_mode else ss["SectionHeader"]
    sub_header_style = ss["ArSubHeader"] if ar_mode else ss["SubHeader"]
    body_style = ss["ArBody"] if ar_mode else ss["Body"]
    body_small_style = ss["ArBodySmall"] if ar_mode else ss["BodySmall"]

    # ---------------- Cover ----------------
    story.append(Spacer(1, 1.5 * inch))
    brand_en, brand_ar = "Y-BOCS", "مقياس ييل-براون"
    story.append(Paragraph(ar(brand_ar) if ar_mode else brand_en, ParagraphStyle(
        name="Brand", fontName=("Arabic-Bold" if ar_mode else "Helvetica-Bold"), fontSize=14,
        textColor=GOLD, alignment=TA_CENTER, leading=18, spaceAfter=4)))
    title_text = ("تقريرك الشخصي"
                  if ar_mode else "Your Assessment Report")
    story.append(Paragraph(ar(title_text) if ar_mode else title_text, ParagraphStyle(
        name="BrandTitle", fontName=("Arabic-Bold" if ar_mode else "Helvetica-Bold"), fontSize=26,
        textColor=NAVY, alignment=TA_CENTER, leading=32, spaceAfter=20)))
    story.append(HRFlowable(width="40%", thickness=1, color=GOLD, hAlign="CENTER", spaceAfter=24))

    client_name = client_info.get("name") or ("عميل سري" if ar_mode else "Confidential Client")
    story.append(Paragraph(ar(client_name) if ar_mode else client_name, ParagraphStyle(
        name="ClientName", fontName=("Arabic-Bold" if ar_mode else "Helvetica-Bold"), fontSize=17,
        textColor=TEXT_DARK, alignment=TA_CENTER, spaceAfter=6)))
    date_label = ("تاريخ التقييم: " if ar_mode else "Assessment date: ") + datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(ar(date_label) if ar_mode else date_label, ParagraphStyle(
        name="ClientDate", fontName=("Arabic" if ar_mode else "Helvetica"), fontSize=11,
        textColor=SLATE, alignment=TA_CENTER, spaceAfter=40)))

    band_label = scores["band"]
    # Keep one PLAIN (unshaped) Arabic label for anything that still needs to
    # compose it with other text or pass it through a helper (like _kv_table)
    # that shapes on its own - shaping twice corrupts the glyphs.
    band_display_plain = BAND_LABEL_AR.get(band_label, band_label) if ar_mode else band_label
    banner_text = f"{scores['total']}/40 — {band_display_plain}"
    story.append(Paragraph(ar(banner_text) if ar_mode else banner_text, ParagraphStyle(
        name="PrimaryBanner", fontName=("Arabic-Bold" if ar_mode else "Helvetica-Bold"), fontSize=16,
        textColor=colors.white, alignment=TA_CENTER,
        backColor=colors.HexColor(BAND_COLORS.get(band_label, "#1B2A4A")),
        borderPadding=(10, 14, 10, 14), leading=20)))
    story.append(Spacer(1, 1.1 * inch))
    footer_text = (
        "هذا التقرير أداة داعمة للعمل العلاجي مع معالجك، وليس تشخيصًا طبيًا أو نفسيًا مستقلًا."
        if ar_mode else
        "This report is a tool to support your work with your therapist. It is not, on its own, a "
        "medical or psychiatric diagnosis."
    )
    story.append(Paragraph(ar(footer_text) if ar_mode else footer_text, ss["CoverFooter"] if not ar_mode else ParagraphStyle(
        "ArCoverFooter", parent=ss["ArBodySmall"], alignment=TA_CENTER)))
    story.append(PageBreak())

    # ---------------- Summary ----------------
    heading = "ملخص نتائجك" if ar_mode else "Your Results Summary"
    story.append(Paragraph(ar(heading) if ar_mode else heading, section_style))

    obs_lbl = "Obsessions subtotal" if not ar_mode else "المجموع الفرعي للوساوس"
    comp_lbl = "Compulsions subtotal" if not ar_mode else "المجموع الفرعي للأفعال القهرية"
    total_lbl = "Total score" if not ar_mode else "الدرجة الكلية"
    level_lbl = "Level" if not ar_mode else "المستوى"
    rows = [
        (obs_lbl, f"{scores['obsession_subtotal']}/20"),
        (comp_lbl, f"{scores['compulsion_subtotal']}/20"),
        (total_lbl, f"{scores['total']}/40"),
        (level_lbl, band_display_plain),
    ]
    story.append(_kv_table(rows, lang, ss))
    story.append(Spacer(1, 10))

    band_desc = BAND_DESCRIPTIONS["ar" if ar_mode else "en"].get(band_label, "")
    story.append(Paragraph(ar(band_desc) if ar_mode else band_desc, body_style))
    story.append(Spacer(1, 10))

    story.append(obsession_compulsion_chart(scores["obsession_subtotal"], scores["compulsion_subtotal"], lang=lang))
    story.append(Spacer(1, 6))
    story.append(severity_gauge(scores["total"], band_label, lang=lang, band_label_display=band_display_plain if ar_mode else None))

    # ---------------- AI narrative ----------------
    story.append(PageBreak())
    heading2 = "ما تظهره نتائجك" if ar_mode else "What Your Results Show"
    story.append(Paragraph(ar(heading2) if ar_mode else heading2, section_style))

    if narrative:
        sec_titles_en = {
            "overview": "Overview", "what_stood_out": "What Stood Out",
            "strengths_noted": "Strengths We Noticed", "next_steps": "Next Steps",
        }
        sec_titles_ar = {
            "overview": "نظرة عامة",
            "what_stood_out": "أبرز ما لاحظناه",
            "strengths_noted": "نقاط قوة لاحظناها",
            "next_steps": "الخطوات التالية",
        }
        for key in ("overview", "what_stood_out", "strengths_noted", "next_steps"):
            text = narrative.get(key)
            if not text:
                continue
            title = (sec_titles_ar if ar_mode else sec_titles_en)[key]
            story.append(Paragraph(ar(title) if ar_mode else title, sub_header_style))
            story.append(Paragraph(ar(text) if ar_mode else text, body_style))
    else:
        fallback = (
            "لم يتم إنشاء ملخص سردي لهذا التقرير — يرجى مراجعة النتائج مع معالجك مباشرة."
            if ar_mode else
            "A narrative summary could not be generated for this report — please review the results above directly with your therapist."
        )
        story.append(Paragraph(fallback, body_style))

    # ---------------- Themes (category chart) ----------------
    cat_chart = category_endorsement_chart(category_counts, lang=lang)
    if cat_chart:
        story.append(PageBreak())
        heading3 = "المواضيع التي ظهرت في قائمة الأعراض" if ar_mode else "Themes From Your Symptom Checklist"
        story.append(Paragraph(ar(heading3) if ar_mode else heading3, section_style))
        note = (
            "يوضح الرسم البياني أدناه عدد البنود التي وضعت علامة عليها في كل فئة من قائمة الأعراض."
            if ar_mode else
            "The chart below shows how many items you marked in each category of the Symptom Checklist."
        )
        story.append(Paragraph(ar(note) if ar_mode else note, body_small_style))
        story.append(Spacer(1, 6))
        story.append(cat_chart)

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.6, color=LINE_GRAY))
    story.append(Spacer(1, 6))
    disclaimer = (
        "هذا التقرير سري. تم إعداده لدعم جلساتك العلاجية وليس بديلاً عن التقييم السريري المباشر مع معالجك."
        if ar_mode else
        "This report is confidential and was prepared to support your therapy sessions. It does not "
        "replace direct clinical discussion with your therapist."
    )
    story.append(Paragraph(ar(disclaimer) if ar_mode else disclaimer, body_small_style))

    date_str = datetime.now().strftime("%B %d, %Y")
    if ar_mode:
        brand_footer = ar("تقرير العميل — Y-BOCS")
        confidential = ar("سري")
        generated_text = ar(f"تاريخ الإنشاء {date_str}")
        page_label = ar("صفحة")
    else:
        brand_footer = "Y-BOCS Client Report"
        confidential = "Confidential"
        generated_text = f"Generated {date_str}"
        page_label = "Page"

    doc.build(
        story,
        onFirstPage=header_footer(brand_footer, confidential, generated_text, page_label, lang=lang),
        onLaterPages=header_footer(brand_footer, confidential, generated_text, page_label, lang=lang),
    )
    return buf.getvalue()
