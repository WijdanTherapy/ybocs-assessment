import os
import secrets as _secrets
import datetime

import streamlit as st
import streamlit.components.v1 as components

from ybocs.i18n import t
from ybocs.questions import (
    CHECKLIST_CATEGORIES, SEVERITY_ITEMS, SCORED_SEVERITY_ITEMS,
    OBSESSION_CATEGORY_KEYS, COMPULSION_CATEGORY_KEYS,
)
from ybocs.questions_ar import CHECKLIST_CATEGORIES_AR, SEVERITY_ITEMS_AR, SCORED_SEVERITY_ITEMS_AR
from ybocs.scoring import score_severity, checklist_category_counts
from ybocs import groq_utils, email_utils, persistence
from ybocs.report_client import generate_client_pdf
from ybocs.report_therapist import generate_therapist_pdf

REPORTS_DIR = "reports"

st.set_page_config(
    page_title="Y-BOCS Assessment",
    page_icon="\U0001FA7A",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session token (for autosave across refresh / reconnect) + state bootstrap
# ---------------------------------------------------------------------------
qp = st.query_params
if qp.get("page") != "admin":
    token = qp.get("s")
    if not token:
        token = _secrets.token_urlsafe(12)
        st.query_params["s"] = token
    st.session_state.setdefault("_session_token", token)

    if "stage" not in st.session_state:
        restored = persistence.load_session(token)
        if restored:
            for k, v in restored.items():
                st.session_state[k] = v
        st.session_state.setdefault("stage", "intro")
        st.session_state.setdefault("lang", "en")
        st.session_state.setdefault("client_name", "")
        st.session_state.setdefault("client_notes", "")
        st.session_state.setdefault("consented", False)
        st.session_state.setdefault("submitted", False)
        st.session_state.setdefault("checklist_answers", {})
        st.session_state.setdefault("severity_answers", {})


def autosave():
    if st.session_state.get("_session_token"):
        persistence.save_session(st.session_state["_session_token"], st.session_state)


# ---------------------------------------------------------------------------
# Global CSS (direction-aware)
# ---------------------------------------------------------------------------
def inject_css(lang):
    rtl = (lang == "ar")
    direction = "rtl" if rtl else "ltr"
    text_align = "right" if rtl else "left"
    font_family = "'Noto Naskh Arabic', 'Tahoma', sans-serif" if rtl else "'DM Sans', sans-serif"
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@300;400;500&family=DM+Sans:wght@300;400;500&family=Noto+Naskh+Arabic:wght@400;500;700&display=swap');

    :root {{
        --bg: #F7F4F0; --white: #FFFFFF; --deep: #1C1917; --warm: #6B5B45;
        --accent: #8B6F47; --border: #DDD5C8; --selected: #2D2926;
    }}
    html, body, [class*="css"] {{
        font-family: {font_family};
        background-color: var(--bg); color: var(--deep);
    }}

    /* Streamlit wraps every page in several nested containers (testids vary
       slightly by version); direction/text-align must be forced on all of
       them with !important, since Streamlit's own stylesheet sets physical
       left/ltr values on some of these that plain inheritance won't override. */
    html, body, .stApp,
    [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stHeader"], section.main, .main .block-container,
    [data-testid="stVerticalBlock"], [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stHorizontalBlock"], [data-testid="stForm"],
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
    [data-testid="stTextInput"], [data-testid="stTextArea"],
    [data-testid="stCheckbox"], [data-testid="stRadio"] {{
        direction: {direction} !important;
    }}
    .stApp {{ background-color: var(--bg); }}
    .main .block-container, [data-testid="stVerticalBlock"],
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] p,
    [data-testid="stMarkdownContainer"] p {{
        text-align: {text_align} !important;
    }}
    /* Checkbox: put the box on the trailing side (right in RTL) instead of
       always-left, so it reads in the same order as the Arabic label text. */
    div[data-testid="stCheckbox"] > label {{
        flex-direction: {"row-reverse" if rtl else "row"} !important;
        justify-content: flex-end !important;
    }}

    .page-header {{ text-align: center; padding: 2.2rem 0 1.6rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1.6rem; }}
    .page-header h1 {{ font-family: {"'Noto Naskh Arabic', serif" if rtl else "'Playfair Display', serif"}; font-size: 2.1rem; font-weight: 400; color: var(--deep); margin-bottom: 0.3rem; }}
    .page-header p {{ color: var(--warm); font-size: 0.8rem; letter-spacing: 0.08em; text-transform: {"none" if rtl else "uppercase"}; }}

    .section-divider {{ text-align: center; padding: 1.3rem 0 0.9rem 0; border-bottom: 1px solid var(--border); margin: 1.8rem 0 1.3rem 0; }}
    .section-divider h2 {{ font-family: {"'Noto Naskh Arabic', serif" if rtl else "'Playfair Display', serif"}; font-size: 1.45rem; font-weight: 400; color: var(--deep); margin-bottom: 0.2rem; }}
    .section-divider p {{ color: var(--warm); font-size: 0.76rem; letter-spacing: 0.06em; text-transform: {"none" if rtl else "uppercase"}; }}

    .instructions-box {{ background: #FBF4E8; border: 1px solid var(--accent); border-right: {"none" if rtl else "4px solid var(--accent)"};
        border-left: {"4px solid var(--accent)" if rtl else "none"}; border-radius: 4px;
        padding: 1.1rem 1.5rem; margin: 0 0 1.6rem 0; text-align: {text_align}; }}
    .instructions-title {{ font-family: {font_family}; font-weight: 600; font-size: 0.98rem; color: var(--deep); margin-bottom: 0.5rem; }}
    .instructions-box ul {{ margin: 0; padding-{"right" if rtl else "left"}: 1.2rem; }}
    .instructions-box li {{ font-size: 0.86rem; color: #4A3F2F; line-height: 1.75; margin-bottom: 0.45rem; }}

    .question-card {{ background: var(--white); border: 1px solid var(--border); border-radius: 6px;
        padding: 1.1rem 1.5rem; margin-bottom: 0.7rem; text-align: {text_align}; }}
    .q-number {{ font-size: 0.68rem; letter-spacing: 0.1em; text-transform: {"none" if rtl else "uppercase"}; color: var(--accent); margin-bottom: 0.25rem; font-weight: 500; }}
    .q-text {{ font-family: {font_family}; font-size: 1.02rem; color: var(--deep); line-height: 1.5; }}
    .q-example {{ font-size: 0.78rem; color: var(--warm); margin-top: 0.4rem; line-height: 1.5; font-style: italic; }}

    div[data-testid="stRadio"] > div {{ gap: 0.35rem !important; flex-direction: column !important; }}
    div[data-testid="stRadio"] > div > label {{ background: var(--bg) !important; border: 1px solid var(--border) !important;
        border-radius: 3px !important; padding: 0.55rem 0.9rem !important; font-size: 0.86rem !important;
        color: var(--deep) !important; font-family: {font_family} !important; }}
    div[data-testid="stRadio"] > div > label:hover {{ border-color: var(--accent) !important; background: #F0EBE3 !important; }}
    div[data-testid="stCheckbox"] label p {{ font-family: {font_family} !important; }}

    .progress-wrap {{ background: var(--border); border-radius: 2px; height: 3px; margin: 1.3rem 0 0.5rem 0; }}
    .progress-fill {{ height: 3px; border-radius: 2px; background: linear-gradient(90deg, var(--warm), var(--accent)); }}

    .stButton > button {{ background: var(--selected) !important; color: var(--bg) !important; border: none !important;
        padding: 0.75rem 2.4rem !important; font-family: {font_family} !important; font-size: 0.82rem !important;
        font-weight: 500 !important; letter-spacing: 0.08em !important; border-radius: 2px !important; }}
    .stButton > button:hover {{ background: var(--warm) !important; }}

    .thank-you {{ text-align: center; padding: 4.5rem 2rem; }}
    .thank-you h2 {{ font-family: {"'Noto Naskh Arabic', serif" if rtl else "'Playfair Display', serif"}; font-size: 2rem; font-weight: 400; margin-bottom: 1rem; }}
    .thank-you p {{ color: var(--warm); font-size: 0.95rem; max-width: 420px; margin: 0 auto; line-height: 1.8; }}

    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {{
        background: white !important; border: 1px solid var(--border) !important; border-radius: 3px !important;
        font-family: {font_family} !important; color: var(--deep) !important; text-align: {text_align} !important;
        direction: {direction} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Belt-and-braces: a couple of native behaviors (text cursor/caret start
    # position in inputs, and any Streamlit internals keyed off the HTML dir
    # attribute rather than the CSS direction property) only follow the
    # document's actual dir attribute, which plain CSS cannot set. This runs
    # in Streamlit's component iframe but reaches up to the real top-level
    # document (same-origin), which is where the visible app actually lives.
    components.html(f"""
    <script>
        const doc = window.parent.document;
        doc.documentElement.setAttribute('dir', '{direction}');
        doc.body.setAttribute('dir', '{direction}');
        const appRoot = doc.querySelector('.stApp');
        if (appRoot) appRoot.setAttribute('dir', '{direction}');
    </script>
    """, height=0, width=0)


# ---------------------------------------------------------------------------
# Admin / therapist portal
# ---------------------------------------------------------------------------
def render_admin():
    inject_css("en")
    st.markdown("""
    <div class="page-header"><p>Therapist Portal</p><h1>Y-BOCS Reports</h1></div>
    """, unsafe_allow_html=True)

    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pwd = st.text_input("Enter admin password", type="password", placeholder="Password")
        if st.button("Access Portal"):
            if pwd and pwd == st.secrets.get("ADMIN_PASSWORD", ""):
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        return

    os.makedirs(REPORTS_DIR, exist_ok=True)
    files = sorted([f for f in os.listdir(REPORTS_DIR) if f.endswith(".pdf")], reverse=True)
    if not files:
        st.info("No reports submitted yet.")
    else:
        st.markdown(f"**{len(files)} report(s) on file**")
        for fname in files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"\U0001F4C4 `{fname}`")
            with col2:
                with open(os.path.join(REPORTS_DIR, fname), "rb") as f:
                    st.download_button("Download", data=f, file_name=fname, mime="application/pdf", key=fname)
    if st.button("Log out"):
        st.session_state.admin_auth = False
        st.rerun()


# ---------------------------------------------------------------------------
# Language toggle (always visible, first thing on the page)
# ---------------------------------------------------------------------------
def render_lang_toggle():
    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        choice = st.radio(
            "lang_toggle", options=["en", "ar"],
            format_func=lambda x: "English" if x == "en" else "العربية",
            index=0 if st.session_state.lang == "en" else 1,
            horizontal=True, label_visibility="collapsed", key="lang_radio",
        )
    if choice != st.session_state.lang:
        st.session_state.lang = choice
        autosave()
        st.rerun()


# ---------------------------------------------------------------------------
# Intro
# ---------------------------------------------------------------------------
def render_intro(lang):
    st.markdown(f"""
    <div class="page-header">
        <p>{t(lang, 'kicker')}</p>
        <h1>{t(lang, 'title')}</h1>
        <p style="margin-top:0.4rem;">{t(lang, 'subtitle')}</p>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"<p style='font-size:0.92rem; line-height:1.8;'>{t(lang, 'intro_p1')}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.92rem; line-height:1.8;'>{t(lang, 'intro_p2')}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.92rem; line-height:1.8;'>{t(lang, 'intro_card_outro')}</p>", unsafe_allow_html=True)

    st.session_state.client_name = st.text_input(t(lang, "name_label"), value=st.session_state.client_name)
    st.session_state.client_notes = st.text_area(t(lang, "notes_label"), value=st.session_state.client_notes)
    consented = st.checkbox(t(lang, "consent_label"), value=st.session_state.consented)
    st.session_state.consented = consented

    if st.button(t(lang, "begin_button")):
        if not consented:
            st.error(t(lang, "consent_error"))
        else:
            st.session_state.stage = "checklist"
            autosave()
            st.rerun()


# ---------------------------------------------------------------------------
# Part 1: Symptom Checklist
# ---------------------------------------------------------------------------
def render_checklist(lang):
    categories = CHECKLIST_CATEGORIES_AR if lang == "ar" else CHECKLIST_CATEGORIES
    st.markdown(f"""
    <div class="section-divider">
        <p>{t(lang, 'part1_kicker')}</p>
        <h2>{t(lang, 'part1_title')}</h2>
    </div>
    <p style="font-size:0.88rem;color:#6B5B45;text-align:center;margin-bottom:1.3rem;line-height:1.8;">
    {t(lang, 'part1_sub')}</p>""", unsafe_allow_html=True)

    instructions_items = "".join(f"<li>{item}</li>" for item in t(lang, "part1_instructions_items"))
    st.markdown(f"""
    <div class="instructions-box">
        <div class="instructions-title">{t(lang, 'part1_instructions_title')}</div>
        <ul>{instructions_items}</ul>
    </div>""", unsafe_allow_html=True)

    for cat_key, cat_label, items in categories:
        st.markdown(f"#### {cat_label}")
        for item_id, text, example in items:
            ans = st.session_state.checklist_answers.get(item_id, {"past": False, "current": False})
            st.markdown(f"""
            <div class="question-card">
                <div class="q-number">#{item_id}</div>
                <div class="q-text">{text}</div>
                <div class="q-example">{example}</div>
            </div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                past = st.checkbox(t(lang, "past_label"), value=ans.get("past", False), key=f"chk_past_{item_id}")
            with c2:
                current = st.checkbox(t(lang, "current_label"), value=ans.get("current", False), key=f"chk_cur_{item_id}")
            st.session_state.checklist_answers[item_id] = {"past": past, "current": current}

    c1, c2 = st.columns(2)
    with c1:
        if st.button(t(lang, "back_button")):
            st.session_state.stage = "intro"
            autosave()
            st.rerun()
    with c2:
        if st.button(t(lang, "continue_part2")):
            st.session_state.stage = "severity"
            autosave()
            st.rerun()


# ---------------------------------------------------------------------------
# Part 2: Severity Scale
# ---------------------------------------------------------------------------
def render_severity(lang):
    items = SEVERITY_ITEMS_AR if lang == "ar" else SEVERITY_ITEMS
    st.markdown(f"""
    <div class="section-divider">
        <p>{t(lang, 'part2_kicker')}</p>
        <h2>{t(lang, 'part2_title')}</h2>
    </div>
    <p style="font-size:0.88rem;color:#6B5B45;text-align:center;margin-bottom:1.3rem;line-height:1.8;">
    {t(lang, 'part2_sub')}</p>""", unsafe_allow_html=True)

    all_answered = True
    for q in items:
        st.markdown(f"""
        <div class="question-card">
            <div class="q-number">{q['id']} {t(lang, 'of')} 11</div>
            <div class="q-text">{q['title']}</div>
            <div class="q-example">{q['question']}</div>
        </div>""", unsafe_allow_html=True)
        options = [f"{i} — {opt}" for i, opt in enumerate(q["options"])]
        existing = st.session_state.severity_answers.get(q["id"])
        choice = st.radio(
            label=f"sev_{q['id']}", options=options,
            index=existing if existing is not None else None,
            key=f"sev_{q['id']}", label_visibility="collapsed",
        )
        if choice is None:
            all_answered = False
        else:
            st.session_state.severity_answers[q["id"]] = options.index(choice)

    answered = len(st.session_state.severity_answers)
    pct = int((answered / 11) * 100)
    st.markdown(f"""
    <div style="text-align:center;font-size:0.78rem;color:#6B5B45;margin-top:1.3rem;">
        {answered} {t(lang, 'of')} 11
    </div>
    <div class="progress-wrap"><div class="progress-fill" style="width:{pct}%"></div></div>
    """, unsafe_allow_html=True)

    if not all_answered and answered > 0:
        st.warning(t(lang, "answer_all_caption"))

    c1, c2 = st.columns(2)
    with c1:
        if st.button(t(lang, "back_button")):
            st.session_state.stage = "checklist"
            autosave()
            st.rerun()
    with c2:
        if st.button(t(lang, "see_results_button"), disabled=not all_answered):
            if all_answered:
                submit_assessment(lang)


# ---------------------------------------------------------------------------
# Submission: score, generate both PDFs, email, save, thank-you
# ---------------------------------------------------------------------------
def submit_assessment(lang):
    with st.spinner(t(lang, "submitting")):
        scores = score_severity(st.session_state.severity_answers)

        # Both reports' charts are always rendered English (and the category
        # chart specifically goes through the matplotlib/English-only path -
        # see pdf_base.py notes on Arabic text there), so category counts are
        # always computed from the English category labels regardless of the
        # client's answer language.
        category_counts_en = checklist_category_counts(st.session_state.checklist_answers, CHECKLIST_CATEGORIES)

        # Context fed to the AI is always built from the English item bank -
        # both report narratives are always English per clinic policy, so
        # there's no reason to feed the model Arabic text just to have it
        # translate back.
        endorsed_current_en = {}
        for cat_key, cat_label, items in CHECKLIST_CATEGORIES:
            texts = [text for item_id, text, _ex in items
                     if st.session_state.checklist_answers.get(item_id, {}).get("current")]
            if texts:
                endorsed_current_en[cat_label] = texts

        client_name = st.session_state.client_name or ""
        client_info = {"name": client_name}

        groq_key = st.secrets.get("GROQ_API_KEY", "")
        narrative = None
        intervention = None
        try:
            narrative = groq_utils.generate_client_narrative(
                client_name, scores, endorsed_current_en, groq_key)
        except Exception as e:
            st.warning(f"Client narrative generation failed (report still saved): {e}")

        try:
            intervention = groq_utils.generate_therapist_intervention(
                client_name, scores, st.session_state.severity_answers, SCORED_SEVERITY_ITEMS,
                category_counts_en, endorsed_current_en, groq_key)
        except Exception as e:
            st.warning(f"Therapist intervention generation failed (report still saved): {e}")

        # Both reports are always English in narrative/structure; only the
        # Q&A appendix wording matches the client's own answer language, so
        # the clinician sees exactly what the client read and answered.
        severity_items_display = SCORED_SEVERITY_ITEMS_AR if lang == "ar" else SCORED_SEVERITY_ITEMS
        checklist_categories_lang = CHECKLIST_CATEGORIES_AR if lang == "ar" else CHECKLIST_CATEGORIES

        client_pdf = generate_client_pdf(
            client_info, scores, narrative, category_counts_en,
            severity_answers=st.session_state.severity_answers,
            severity_items_display=severity_items_display,
            checklist_categories_display=checklist_categories_lang,
            checklist_answers=st.session_state.checklist_answers,
            answer_language=lang,
        )
        therapist_pdf = generate_therapist_pdf(
            client_info, scores, st.session_state.severity_answers, SCORED_SEVERITY_ITEMS,
            category_counts_en, checklist_categories_lang, st.session_state.checklist_answers,
            intervention, answer_language=lang, severity_items_display=severity_items_display,
        )

        os.makedirs(REPORTS_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = (client_name or "anonymous").replace(" ", "_").lower()
        with open(os.path.join(REPORTS_DIR, f"YBOCS_Client_{safe_name}_{timestamp}.pdf"), "wb") as f:
            f.write(client_pdf)
        with open(os.path.join(REPORTS_DIR, f"YBOCS_Therapist_{safe_name}_{timestamp}.pdf"), "wb") as f:
            f.write(therapist_pdf)

        resend_key = st.secrets.get("RESEND_API_KEY", "")
        resend_from = st.secrets.get("RESEND_FROM_ADDRESS", "")
        if resend_key and resend_from:
            try:
                email_utils.send_ybocs_reports(
                    resend_key, resend_from, client_pdf, therapist_pdf,
                    client_name, scores["band"], scores["total"])
            except Exception as e:
                st.warning(f"Reports saved but email failed: {e}")

        st.session_state.submitted = True
        token = st.session_state.get("_session_token")
        if token:
            persistence.delete_session(token)
        st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if qp.get("page") == "admin":
    render_admin()
else:
    lang = st.session_state.lang
    inject_css(lang)
    render_lang_toggle()

    if st.session_state.submitted:
        st.markdown(f"""
        <div class="thank-you">
            <h2>{t(lang, 'thank_you_title')}</h2>
            <p>{t(lang, 'thank_you_body')}</p>
        </div>""", unsafe_allow_html=True)
    elif st.session_state.stage == "intro":
        render_intro(lang)
    elif st.session_state.stage == "checklist":
        render_checklist(lang)
    elif st.session_state.stage == "severity":
        render_severity(lang)

    st.markdown(f"<p style='text-align:center;font-size:0.72rem;color:#8A94A6;margin-top:3rem;'>{t(lang, 'footer_note')}</p>", unsafe_allow_html=True)
