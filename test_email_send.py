"""One-off script: generate a real English and Arabic client+therapist PDF
set from sample answers and email both via Resend, exactly as app.py does.

Run this yourself with:
    .venv\\Scripts\\python.exe test_email_send.py

Reads secrets from .streamlit/secrets.toml (same file Streamlit itself
reads) - make sure that file exists and has real GROQ_API_KEY,
RESEND_API_KEY, and RESEND_FROM_ADDRESS values before running.
"""
import tomllib

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomllib.load(f)

from ybocs.questions import CHECKLIST_CATEGORIES, SCORED_SEVERITY_ITEMS
from ybocs.questions_ar import CHECKLIST_CATEGORIES_AR, SCORED_SEVERITY_ITEMS_AR
from ybocs.scoring import score_severity, checklist_category_counts
from ybocs.report_client import generate_client_pdf
from ybocs.report_therapist import generate_therapist_pdf
from ybocs import groq_utils, email_utils

SEV_ANSWERS = {1: 3, 2: 2, 3: 3, 4: 1, 5: 2, 6: 1, 7: 1, 8: 2, 9: 1, 10: 1, 11: 1}
CHECKLIST = {
    1: {"past": True, "current": True},
    11: {"past": True, "current": True},
    38: {"past": True, "current": True},
    42: {"past": False, "current": True},
}

GROQ_KEY = secrets["GROQ_API_KEY"]
RESEND_KEY = secrets["RESEND_API_KEY"]
RESEND_FROM = secrets["RESEND_FROM_ADDRESS"]


def run(lang, client_name):
    categories = CHECKLIST_CATEGORIES_AR if lang == "ar" else CHECKLIST_CATEGORIES
    severity_display = SCORED_SEVERITY_ITEMS_AR if lang == "ar" else SCORED_SEVERITY_ITEMS

    scores = score_severity(SEV_ANSWERS)
    category_counts = checklist_category_counts(CHECKLIST, categories)
    category_counts_en = (
        category_counts if lang == "en"
        else checklist_category_counts(CHECKLIST, CHECKLIST_CATEGORIES)
    )

    endorsed_current = {}
    for cat_key, cat_label, items in categories:
        texts = [text for item_id, text, _ex in items if CHECKLIST.get(item_id, {}).get("current")]
        if texts:
            endorsed_current[cat_label] = texts

    print(f"[{lang}] generating client narrative via Groq...")
    try:
        narrative = groq_utils.generate_client_narrative(client_name, scores, endorsed_current, lang, GROQ_KEY)
        print(f"[{lang}] narrative ok: {list(narrative.keys())}")
    except Exception as e:
        print(f"[{lang}] narrative FAILED: {e}")
        narrative = None

    print(f"[{lang}] generating therapist intervention via Groq...")
    try:
        intervention = groq_utils.generate_therapist_intervention(
            client_name, scores, SEV_ANSWERS, SCORED_SEVERITY_ITEMS, category_counts, endorsed_current, GROQ_KEY)
        print(f"[{lang}] intervention ok: {list(intervention.keys())}")
    except Exception as e:
        print(f"[{lang}] intervention FAILED: {e}")
        intervention = None

    client_pdf = generate_client_pdf({"name": client_name}, scores, narrative, category_counts, lang=lang)
    therapist_pdf = generate_therapist_pdf(
        {"name": client_name}, scores, SEV_ANSWERS, SCORED_SEVERITY_ITEMS,
        category_counts_en, categories, CHECKLIST, intervention,
        answer_language=lang, severity_items_display=severity_display,
    )
    print(f"[{lang}] client pdf {len(client_pdf)} bytes, therapist pdf {len(therapist_pdf)} bytes")

    result = email_utils.send_ybocs_reports(
        RESEND_KEY, RESEND_FROM, client_pdf, therapist_pdf, client_name, scores["band"], scores["total"])
    print(f"[{lang}] Resend result: {result}")


run("en", "Test Client (English)")
run("ar", "عميل اختبار (عربي)")
