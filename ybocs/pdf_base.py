"""Shared PDF building blocks: palette, fonts (incl. Arabic shaping/RTL),
chart helpers, and header/footer used by both the client and therapist
Y-BOCS reports."""

import io
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image as PILImage, ImageDraw, ImageFont

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from matplotlib import font_manager

_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
pdfmetrics.registerFont(TTFont("Arabic", os.path.join(_FONT_DIR, "NotoNaskhArabic-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Arabic-Bold", os.path.join(_FONT_DIR, "NotoNaskhArabic-Bold.ttf")))

# Matplotlib has no built-in Arabic shaping/RTL either - we feed it the same
# reshaped+bidi-reordered text (via ar()) and render it with this font so
# chart axis labels/titles display correctly for the Arabic report.
ARABIC_FONT_PROP = font_manager.FontProperties(
    fname=os.path.join(_FONT_DIR, "NotoNaskhArabic-Regular.ttf"))
ARABIC_FONT_PROP_BOLD = font_manager.FontProperties(
    fname=os.path.join(_FONT_DIR, "NotoNaskhArabic-Bold.ttf"))


def ar(text):
    """Reshape (join Arabic letterforms) + bidi-reorder so RTL text renders
    correctly in ReportLab, which has no native RTL/shaping support."""
    if text is None:
        return ""
    return get_display(arabic_reshaper.reshape(str(text)))


def rtl_para_style(name, base, **overrides):
    """Clone a style for right-to-left Arabic rendering: Arabic font + right
    alignment, so paragraphs read correctly in a predominantly LTR document."""
    kwargs = dict(
        fontName="Arabic-Bold" if "Bold" in base.fontName else "Arabic",
        alignment=TA_RIGHT,
    )
    kwargs.update(overrides)
    return ParagraphStyle(name, parent=base, **kwargs)


# ---------------------------------------------------------------------------
# Palette - muted clinical "premium letterhead" feel
# ---------------------------------------------------------------------------
NAVY = colors.HexColor("#1B2A4A")
SLATE = colors.HexColor("#4A5568")
SLATE_LIGHT = colors.HexColor("#8A94A6")
GOLD = colors.HexColor("#B8975A")
LINE_GRAY = colors.HexColor("#D8DCE3")
BG_PANEL = colors.HexColor("#F6F7F9")
TEXT_DARK = colors.HexColor("#1F2430")

BAND_COLORS = {
    "Subclinical": "#3F7D5B",
    "Mild": "#5B8A3F",
    "Moderate": "#C98A3E",
    "Severe": "#B8622E",
    "Extreme": "#9B3B3B",
}

mpl_rc = {
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#D8DCE3",
    "axes.labelcolor": "#4A5568",
    "text.color": "#1F2430",
    "xtick.color": "#4A5568",
    "ytick.color": "#4A5568",
}
plt.rcParams.update(mpl_rc)


def _fig_to_image(fig, width_in=6.4):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", transparent=False, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    img = Image(buf)
    aspect = img.imageHeight / float(img.imageWidth)
    img.drawWidth = width_in * inch
    img.drawHeight = width_in * inch * aspect
    return img


def _lbl(lang, text):
    return ar(text) if lang == "ar" else text


# ---------------------------------------------------------------------------
# Arabic charts are rendered with PIL instead of matplotlib. matplotlib's
# Agg/freetype text path was found to mis-render certain Arabic presentation-
# form glyphs (e.g. a final meem drawn as a heh) even though the exact same
# font file renders correctly via ReportLab and via PIL/ImageDraw directly -
# a matplotlib-specific glyph-lookup quirk, not a font or shaping bug. PIL
# is confirmed correct, so Arabic chart text goes through it; English charts
# keep the existing matplotlib implementation unchanged.
# ---------------------------------------------------------------------------
_PIL_SCALE = 3  # supersample then downscale on embed for crisp text at 200dpi


def _pil_font(size, bold=False):
    path = os.path.join(_FONT_DIR, "NotoNaskhArabic-Bold.ttf" if bold else "NotoNaskhArabic-Regular.ttf")
    return ImageFont.truetype(path, size)


def _pil_to_flowable(img, width_in=6.4):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    rl_img = Image(buf)
    aspect = rl_img.imageHeight / float(rl_img.imageWidth)
    rl_img.drawWidth = width_in * inch
    rl_img.drawHeight = width_in * inch * aspect
    return rl_img


def _wrap_arabic_lines(draw, text, font, max_width):
    """Wrap LOGICAL (unshaped) Arabic text to max_width, shaping each
    candidate line independently so word-wrap boundaries never split an
    already-shaped glyph run (which would corrupt joining)."""
    words = text.split(" ")
    lines, cur = [], []
    for w in words:
        trial = cur + [w]
        shaped = ar(" ".join(trial))
        width = draw.textbbox((0, 0), shaped, font=font)[2]
        if width <= max_width or not cur:
            cur = trial
        else:
            lines.append(ar(" ".join(cur)))
            cur = [w]
    if cur:
        lines.append(ar(" ".join(cur)))
    return lines


def _pil_hbar_chart(items, max_value, xlabel_plain, value_fmt="{v}/{m}",
                     width_in=6.4, label_frac=0.42, bar_frac=0.42):
    """RTL horizontal bar chart. items: list of (label_plain, value, color_hex).
    Bars grow rightward from the label column (i.e. visually from right edge
    inward), matching how the English/matplotlib charts grow from x=0."""
    S = _PIL_SCALE
    row_h = 46 * S
    pad = 24 * S
    width_px = int(width_in * 100 * S)
    label_w = int(width_px * label_frac)
    bar_area_w = int(width_px * bar_frac)
    height_px = pad * 2 + row_h * len(items) + 50 * S

    img = PILImage.new("RGB", (width_px, height_px), "white")
    d = ImageDraw.Draw(img)
    font_label = _pil_font(13 * S)
    font_value = _pil_font(12 * S)
    font_axis = _pil_font(11 * S)

    bar_right_x = width_px - pad - label_w - 10 * S
    bar_left_x = bar_right_x - bar_area_w

    for i, (label, value, color) in enumerate(items):
        y0 = pad + i * row_h
        y_mid = y0 + row_h * 0.42
        frac = min(value / max_value, 1.0) if max_value else 0
        bar_w = int(bar_area_w * frac)
        d.rectangle([bar_right_x - bar_w, y0 + 6 * S, bar_right_x, y0 + row_h - 14 * S], fill=color)
        shaped_label = ar(label)
        lb = d.textbbox((0, 0), shaped_label, font=font_label)
        d.text((width_px - pad - (lb[2] - lb[0]), y_mid - (lb[3] - lb[1]) / 2 - lb[1]),
               shaped_label, font=font_label, fill="#1F2430")
        val_text = value_fmt.format(v=value, m=max_value)
        vb = d.textbbox((0, 0), val_text, font=font_value)
        d.text((bar_right_x - bar_w - 8 * S - (vb[2] - vb[0]), y_mid - (vb[3] - vb[1]) / 2 - vb[1]),
               val_text, font=font_value, fill="#4A5568")

    axis_y = pad + row_h * len(items) + 14 * S
    d.line([(bar_left_x, axis_y), (bar_right_x, axis_y)], fill="#D8DCE3", width=2 * S)
    shaped_axis = ar(xlabel_plain)
    ab = d.textbbox((0, 0), shaped_axis, font=font_axis)
    d.text(((bar_left_x + bar_right_x) / 2 - (ab[2] - ab[0]) / 2, axis_y + 10 * S),
           shaped_axis, font=font_axis, fill="#4A5568")

    img = img.resize((width_px // S, height_px // S), PILImage.LANCZOS)
    return _pil_to_flowable(img, width_in=width_in)


def obsession_compulsion_chart(obsession_subtotal, compulsion_subtotal, lang="en"):
    if lang == "ar":
        items = [
            ("الوساوس", obsession_subtotal, "#1B2A4A"),
            ("الأفعال القهرية", compulsion_subtotal, "#B8975A"),
        ]
        return _pil_hbar_chart(items, max_value=20, xlabel_plain="المجموع الفرعي (0-20)",
                                width_in=5.8, label_frac=0.3, bar_frac=0.5)

    labels = ["Obsessions", "Compulsions"]
    fig, ax = plt.subplots(figsize=(6, 2.6))
    values = [obsession_subtotal, compulsion_subtotal]
    bar_colors = ["#1B2A4A", "#B8975A"]
    y_pos = np.arange(2)
    ax.barh(y_pos, values, color=bar_colors, height=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 20)
    ax.set_xlabel("Subtotal (0–20)", fontsize=9)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for i, v in enumerate(values):
        ax.text(v + 0.4, y_pos[i], f"{v}/20", va="center", ha="left", fontsize=9.5, color="#4A5568")
    fig.tight_layout()
    return _fig_to_image(fig, width_in=5.8)


def _pil_severity_gauge(total, band_label_plain, width_in=6.2):
    S = _PIL_SCALE
    width_px = int(width_in * 100 * S)
    height_px = int(1.3 * 100 * S)
    img = PILImage.new("RGB", (width_px, height_px), "white")
    d = ImageDraw.Draw(img)

    band_bounds = [0, 8, 16, 24, 32, 40]
    band_colors = ["#3F7D5B", "#5B8A3F", "#C98A3E", "#B8622E", "#9B3B3B"]
    bar_y0, bar_y1 = int(height_px * 0.32), int(height_px * 0.56)
    pad = 20 * S
    bar_w = width_px - 2 * pad
    # RTL: 0 on the right, 40 on the left (mirrors the English 0->40 L-to-R axis)
    for i in range(5):
        x_start = pad + bar_w * (1 - band_bounds[i] / 40)
        x_end = pad + bar_w * (1 - band_bounds[i + 1] / 40)
        d.rectangle([x_end, bar_y0, x_start, bar_y1], fill=band_colors[i])

    marker_x = pad + bar_w * (1 - total / 40)
    d.line([(marker_x, bar_y0 - 6 * S), (marker_x, bar_y1 + 6 * S)], fill="#1F2430", width=3 * S)
    d.polygon([(marker_x - 7 * S, bar_y0 - 20 * S), (marker_x + 7 * S, bar_y0 - 20 * S),
               (marker_x, bar_y0 - 6 * S)], fill="#1F2430")

    font_tick = _pil_font(10 * S)
    for v in [0, 8, 16, 24, 32, 40]:
        x = pad + bar_w * (1 - v / 40)
        t = str(v)
        tb = d.textbbox((0, 0), t, font=font_tick)
        d.text((x - (tb[2] - tb[0]) / 2, bar_y1 + 8 * S), t, font=font_tick, fill="#4A5568")

    font_label = _pil_font(13 * S, bold=True)
    label_text = f"{total}/40 — {ar(band_label_plain)}"
    lb = d.textbbox((0, 0), label_text, font=font_label)
    d.text((width_px / 2 - (lb[2] - lb[0]) / 2, bar_y1 + 30 * S), label_text, font=font_label, fill="#1F2430")

    img = img.resize((width_px // S, height_px // S), PILImage.LANCZOS)
    return _pil_to_flowable(img, width_in=width_in)


def severity_gauge(total, band_label, lang="en", band_label_display=None):
    if lang == "ar":
        return _pil_severity_gauge(total, band_label_display or band_label)

    fig, ax = plt.subplots(figsize=(6.4, 1.3))
    band_bounds = [0, 8, 16, 24, 32, 41]
    band_colors = ["#3F7D5B", "#5B8A3F", "#C98A3E", "#B8622E", "#9B3B3B"]
    for i in range(5):
        ax.barh([0], [band_bounds[i + 1] - band_bounds[i]], left=band_bounds[i],
                color=band_colors[i], height=0.5, alpha=0.85)
    ax.set_xlim(0, 40)
    ax.set_ylim(-0.6, 0.6)
    ax.axvline(total, color="#1F2430", linewidth=2.2)
    ax.plot(total, 0.32, marker="v", color="#1F2430", markersize=9)
    ax.set_yticks([])
    ax.set_xticks([0, 8, 16, 24, 32, 40])
    ax.tick_params(axis="x", labelsize=8)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.text(total, -0.52, f"{total}/40 — {band_label}", ha="center", fontsize=9.5,
             color="#1F2430", weight="bold")
    fig.tight_layout()
    return _fig_to_image(fig, width_in=6.2)


def _pil_wrapped_hbar_chart(items, max_value, xlabel_plain, value_fmt="{v}",
                             width_in=6.4, label_frac=0.52):
    """Like _pil_hbar_chart but wraps long labels onto up to 2 lines."""
    S = _PIL_SCALE
    width_px = int(width_in * 100 * S)
    label_w = int(width_px * label_frac) - 20 * S
    pad = 20 * S
    bar_area_w = width_px - 2 * pad - label_w - 10 * S
    bar_right_x = width_px - pad - label_w

    font_label = _pil_font(11 * S)
    font_value = _pil_font(11 * S)
    font_axis = _pil_font(10.5 * S)

    tmp = PILImage.new("RGB", (10, 10))
    dtmp = ImageDraw.Draw(tmp)
    row_infos = []
    line_h = 15 * S
    for label, value, color in items:
        lines = _wrap_arabic_lines(dtmp, label, font_label, label_w)[:2]
        row_h = max(34 * S, len(lines) * line_h + 14 * S)
        row_infos.append((lines, value, color, row_h))

    height_px = pad + sum(r[3] for r in row_infos) + 50 * S
    img = PILImage.new("RGB", (width_px, int(height_px)), "white")
    d = ImageDraw.Draw(img)

    y = pad
    for lines, value, color, row_h in row_infos:
        y_mid = y + row_h / 2
        frac = min(value / max_value, 1.0) if max_value else 0
        bar_w = int(bar_area_w * frac)
        d.rectangle([bar_right_x - bar_w, y + row_h * 0.22, bar_right_x, y + row_h * 0.78], fill=color)
        val_text = value_fmt.format(v=value)
        vb = d.textbbox((0, 0), val_text, font=font_value)
        d.text((bar_right_x - bar_w - 8 * S - (vb[2] - vb[0]), y_mid - (vb[3] - vb[1]) / 2 - vb[1]),
               val_text, font=font_value, fill="#4A5568")
        text_block_h = len(lines) * line_h
        ly = y_mid - text_block_h / 2
        for line in lines:
            lb = d.textbbox((0, 0), line, font=font_label)
            d.text((width_px - pad - (lb[2] - lb[0]), ly), line, font=font_label, fill="#1F2430")
            ly += line_h
        y += row_h

    axis_y = y + 10 * S
    d.line([(pad, axis_y), (bar_right_x, axis_y)], fill="#D8DCE3", width=2 * S)
    shaped_axis = ar(xlabel_plain)
    ab = d.textbbox((0, 0), shaped_axis, font=font_axis)
    d.text(((pad + bar_right_x) / 2 - (ab[2] - ab[0]) / 2, axis_y + 8 * S),
           shaped_axis, font=font_axis, fill="#4A5568")

    img = img.resize((width_px // S, int(height_px) // S), PILImage.LANCZOS)
    return _pil_to_flowable(img, width_in=width_in)


def severity_items_chart(severity_answers, severity_items, lang="en", title_lookup=None):
    """Horizontal bar chart of the 10 scored severity items (0-4 each).
    title_lookup: optional dict {item_id: localized_title} for Arabic labels."""
    if lang == "ar":
        titles = title_lookup or {}
        items = [
            (f"{q['id']}. {titles.get(q['id'], q['title'])}", severity_answers.get(q["id"], 0),
             "#1B2A4A" if q["kind"] == "obsession" else "#B8975A")
            for q in severity_items
        ]
        return _pil_wrapped_hbar_chart(items, max_value=4, xlabel_plain="الدرجة (0-4)",
                                        value_fmt="{v}", width_in=6.4, label_frac=0.55)

    ids = [q["id"] for q in severity_items]
    values = [severity_answers.get(i, 0) for i in ids]
    labels = [f"{q['id']}. {q['title']}" for q in severity_items]
    colors_item = ["#1B2A4A" if q["kind"] == "obsession" else "#B8975A" for q in severity_items]

    fig, ax = plt.subplots(figsize=(7, 4.6))
    y_pos = np.arange(len(ids))[::-1]
    ax.barh(y_pos, values, color=colors_item, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=7.8)
    ax.set_xlim(0, 4)
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xlabel("Score (0–4)", fontsize=9)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#D8DCE3")
    for i, v in enumerate(values):
        ax.text(v + 0.08, y_pos[i], str(v), va="center", ha="left", fontsize=8, color="#4A5568")
    fig.tight_layout()
    return _fig_to_image(fig, width_in=6.4)


def _pil_category_chart(rows, width_in=6.4):
    """rows: list of (label_plain, current, past_only), sorted desc already."""
    S = _PIL_SCALE
    width_px = int(width_in * 100 * S)
    label_frac = 0.42
    label_w = int(width_px * label_frac) - 20 * S
    pad = 20 * S
    bar_area_w = width_px - 2 * pad - label_w - 10 * S
    bar_right_x = width_px - pad - label_w
    max_value = max((r[1] + r[2]) for r in rows) or 1

    font_label = _pil_font(11 * S)
    font_small = _pil_font(10 * S)

    row_h = 34 * S
    height_px = pad + row_h * len(rows) + 60 * S
    img = PILImage.new("RGB", (width_px, height_px), "white")
    d = ImageDraw.Draw(img)

    y = pad
    for label, current, past_only in rows:
        y_mid = y + row_h / 2
        total = current + past_only
        total_w = int(bar_area_w * (total / max_value))
        cur_w = int(bar_area_w * (current / max_value))
        d.rectangle([bar_right_x - total_w, y + row_h * 0.22, bar_right_x - total_w + cur_w, y + row_h * 0.78],
                    fill="#9B3B3B")
        d.rectangle([bar_right_x - total_w + cur_w, y + row_h * 0.22, bar_right_x, y + row_h * 0.78],
                    fill="#D8B48A")
        shaped = ar(label)
        lb = d.textbbox((0, 0), shaped, font=font_label)
        d.text((width_px - pad - (lb[2] - lb[0]), y_mid - (lb[3] - lb[1]) / 2 - lb[1]),
               shaped, font=font_label, fill="#1F2430")
        y += row_h

    legend_y = y + 14 * S
    sw = 12 * S
    cur_lbl = ar("حاليًا")
    past_lbl = ar("سابقًا فقط")
    clb = d.textbbox((0, 0), cur_lbl, font=font_small)
    plb = d.textbbox((0, 0), past_lbl, font=font_small)
    x = bar_right_x
    d.rectangle([x - sw, legend_y, x, legend_y + sw], fill="#9B3B3B")
    x -= sw + 6 * S
    d.text((x - (clb[2] - clb[0]), legend_y - 2 * S), cur_lbl, font=font_small, fill="#4A5568")
    x -= (clb[2] - clb[0]) + 20 * S
    d.rectangle([x - sw, legend_y, x, legend_y + sw], fill="#D8B48A")
    x -= sw + 6 * S
    d.text((x - (plb[2] - plb[0]), legend_y - 2 * S), past_lbl, font=font_small, fill="#4A5568")

    img = img.resize((width_px // S, height_px // S), PILImage.LANCZOS)
    return _pil_to_flowable(img, width_in=width_in)


def category_endorsement_chart(category_counts, lang="en"):
    """category_counts: list of (cat_key, cat_label, current, past_only, total_items)."""
    rows = [r for r in category_counts if r[2] or r[3]]
    if not rows:
        return None
    rows = sorted(rows, key=lambda r: (r[2], r[3]), reverse=True)

    if lang == "ar":
        pil_rows = [(r[1], r[2], r[3]) for r in rows]
        return _pil_category_chart(pil_rows, width_in=6.4)

    labels = [r[1] for r in rows]
    current = [r[2] for r in rows]
    past_only = [r[3] for r in rows]

    fig, ax = plt.subplots(figsize=(7, max(2.2, 0.42 * len(rows))))
    y_pos = np.arange(len(rows))[::-1]
    ax.barh(y_pos, current, color="#9B3B3B", height=0.55, label="Current")
    ax.barh(y_pos, past_only, left=current, color="#D8B48A", height=0.55, label="Past only")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel("Items endorsed", fontsize=9)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.legend(loc="lower right", fontsize=7.5, frameon=False)
    fig.tight_layout()
    return _fig_to_image(fig, width_in=6.4)


def base_styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="ReportTitle", fontName="Helvetica-Bold", fontSize=24,
                           textColor=NAVY, leading=28, spaceAfter=6))
    ss.add(ParagraphStyle(name="ReportSubtitle", fontName="Helvetica", fontSize=12,
                           textColor=SLATE, leading=16, spaceAfter=2))
    ss.add(ParagraphStyle(name="SectionHeader", fontName="Helvetica-Bold", fontSize=14.5,
                           textColor=NAVY, leading=18, spaceBefore=16, spaceAfter=7))
    ss.add(ParagraphStyle(name="SubHeader", fontName="Helvetica-Bold", fontSize=11,
                           textColor=GOLD, leading=14, spaceBefore=9, spaceAfter=4))
    ss.add(ParagraphStyle(name="Body", fontName="Helvetica", fontSize=9.6,
                           textColor=TEXT_DARK, leading=14.2, spaceAfter=6))
    ss.add(ParagraphStyle(name="BodySmall", fontName="Helvetica", fontSize=8.5,
                           textColor=SLATE, leading=12.3, spaceAfter=4))
    ss.add(ParagraphStyle(name="Label", fontName="Helvetica-Bold", fontSize=8.3,
                           textColor=SLATE, leading=11))
    ss.add(ParagraphStyle(name="YBullet", fontName="Helvetica", fontSize=9.4,
                           textColor=TEXT_DARK, leading=13.6, spaceAfter=4, leftIndent=12,
                           bulletIndent=0))
    ss.add(ParagraphStyle(name="RiskFlag", fontName="Helvetica-Bold", fontSize=9.6,
                           textColor=colors.HexColor("#9B3B3B"), leading=14, spaceAfter=6,
                           backColor=colors.HexColor("#FBEAEA"), borderPadding=(8, 10, 8, 10)))
    ss.add(ParagraphStyle(name="CoverFooter", fontName="Helvetica", fontSize=9,
                           textColor=SLATE_LIGHT, alignment=TA_CENTER, leading=12))
    # Arabic variants
    ss.add(ParagraphStyle(name="ArTitle", fontName="Arabic-Bold", fontSize=22,
                           textColor=NAVY, leading=30, alignment=TA_RIGHT, spaceAfter=6))
    ss.add(ParagraphStyle(name="ArSectionHeader", fontName="Arabic-Bold", fontSize=14,
                           textColor=NAVY, leading=22, alignment=TA_RIGHT, spaceBefore=16, spaceAfter=7))
    ss.add(ParagraphStyle(name="ArSubHeader", fontName="Arabic-Bold", fontSize=11,
                           textColor=GOLD, leading=18, alignment=TA_RIGHT, spaceBefore=9, spaceAfter=4))
    ss.add(ParagraphStyle(name="ArBody", fontName="Arabic", fontSize=10,
                           textColor=TEXT_DARK, leading=18, alignment=TA_RIGHT, spaceAfter=6))
    ss.add(ParagraphStyle(name="ArBodySmall", fontName="Arabic", fontSize=9,
                           textColor=SLATE, leading=16, alignment=TA_RIGHT, spaceAfter=4))
    return ss


def header_footer(brand_text, confidential_text, generated_text, page_label, lang="en"):
    """All text args must already be fully reshaped+bidi-reordered (via ar())
    by the caller when lang == 'ar' - ReportLab's canvas does no text shaping
    of its own. generated_text is the complete "Generated <date>" string
    (built by the caller so the Arabic label and the Latin date get shaped
    together as one bidi unit, rather than concatenated after shaping)."""
    font_name = "Arabic" if lang == "ar" else "Helvetica"

    def _draw(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE_GRAY)
        canvas.setLineWidth(0.6)
        canvas.line(0.75 * inch, LETTER[1] - 0.6 * inch, LETTER[0] - 0.75 * inch, LETTER[1] - 0.6 * inch)
        canvas.setFont(font_name, 8)
        canvas.setFillColor(SLATE_LIGHT)
        canvas.drawString(0.75 * inch, LETTER[1] - 0.5 * inch, brand_text)
        canvas.drawRightString(LETTER[0] - 0.75 * inch, LETTER[1] - 0.5 * inch, confidential_text)

        canvas.setStrokeColor(LINE_GRAY)
        canvas.line(0.75 * inch, 0.65 * inch, LETTER[0] - 0.75 * inch, 0.65 * inch)
        canvas.setFont(font_name, 8)
        canvas.setFillColor(SLATE_LIGHT)
        canvas.drawString(0.75 * inch, 0.5 * inch, generated_text)
        canvas.drawRightString(LETTER[0] - 0.75 * inch, 0.5 * inch, f"{page_label} {doc.page}")
        canvas.restoreState()
    return _draw


def build_qa_appendix(ss, severity_answers, severity_items_display, checklist_categories_display,
                       checklist_answers, answer_language="en"):
    """Builds the shared "Appendix A (Severity Scale) / Appendix B (Symptom
    Checklist)" flowables used by BOTH the client and therapist reports.
    Section headers stay in English always (report structure is always
    English per clinic policy); only the item wording itself reflects the
    client's actual answer language, so the reader sees exactly what the
    client read when they answered. severity_items_display and
    checklist_categories_display must already be in that answer language."""
    ar_mode = (answer_language == "ar")
    item_style = ss["ArBodySmall"] if ar_mode else ss["BodySmall"]
    sub_style = ss["ArSubHeader"] if ar_mode else ss["SubHeader"]

    def _t(text):
        return ar(text) if ar_mode else text

    story = [PageBreak()]
    story.append(Paragraph("Appendix A — Severity Scale, Item by Item" +
                            (" (Arabic wording as answered)" if ar_mode else ""), ss["SectionHeader"]))
    sev_rows = [["#", "Item", "Score"]]
    for q in severity_items_display:
        sev_rows.append([
            Paragraph(str(q["id"]), ss["BodySmall"]),
            Paragraph(_t(q["title"]), item_style),
            Paragraph(str(severity_answers.get(q["id"], "")), ss["BodySmall"]),
        ])
    svt = Table(sev_rows, colWidths=[0.35 * inch, 5.4 * inch, 0.55 * inch])
    svt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE9E3")),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(svt)

    story.append(PageBreak())
    story.append(Paragraph("Appendix B — Symptom Checklist, Items Endorsed" +
                            (" (Arabic wording as answered)" if ar_mode else ""), ss["SectionHeader"]))
    any_endorsed = False
    for cat_key, cat_label, items in checklist_categories_display:
        rows_for_cat = []
        for item_id, text, _ex in items:
            ans = checklist_answers.get(item_id, {})
            if ans.get("current") or ans.get("past"):
                any_endorsed = True
                status = "Current" if ans.get("current") else "Past only"
                rows_for_cat.append([str(item_id), _t(text), status])
        if rows_for_cat:
            story.append(Paragraph(_t(cat_label) if ar_mode else cat_label, sub_style))
            cat_rows = [["#", "Item", "Status"]] + [
                [Paragraph(r[0], ss["BodySmall"]), Paragraph(r[1], item_style), Paragraph(r[2], ss["BodySmall"])]
                for r in rows_for_cat
            ]
            ct = Table(cat_rows, colWidths=[0.35 * inch, 5.1 * inch, 0.85 * inch])
            ct.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE9E3")),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.3),
            ]))
            story.append(ct)
            story.append(Spacer(1, 8))
    if not any_endorsed:
        story.append(Paragraph("No symptom checklist items were marked as past or current.", ss["Body"]))

    return story
