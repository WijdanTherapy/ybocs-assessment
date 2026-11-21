# Y-BOCS Clinical Assessment

A self-hosted Streamlit tool for a therapist to administer the Yale-Brown
Obsessive-Compulsive Scale (Y-BOCS) — the 58-item Symptom Checklist plus the
10-item Severity Scale (+ insight item) — in **English or Arabic**, with a
language toggle at the start of the assessment. Scoring, charts, and two
separate AI-assisted PDF reports (a supportive client-facing report and a
confidential practitioner report) are generated automatically and emailed
only to the therapist's inbox.

**This is a clinical support tool for use alongside a licensed therapist,
not a stand-alone diagnostic instrument.**

## Features
- Full Y-BOCS Symptom Checklist (58 items, 15 categories) and Severity Scale
  (10 scored items + insight item), independently worded in English and
  Arabic (not a literal back-translation — natural clinical phrasing in each)
- Language toggle at the very top of the assessment; the Arabic experience
  is fully right-to-left (UI, PDF text direction, and chart labels)
- Automatic scoring: obsession/compulsion subtotals, total (0–40), severity
  band (Subclinical → Extreme), insight level
- **Client Report (PDF)** — plain-language, non-alarming, AI-written summary
  with charts, meant to be reviewed with or handed to the client
- **Therapist Confidential Report (PDF)** — full item-level data, AI-written
  clinical formulation, differential considerations, symptom-dimension
  breakdown, risk-screening flags, treatment recommendations, session
  questions/roadmap, and a complete item-by-item appendix in the client's
  answer language
- Both reports emailed via [Resend](https://resend.com) to the therapist's
  inbox only — never to the client
- Autosave: progress survives a refresh or dropped connection (same link/tab)
- Password-protected therapist portal (`?page=admin`) to re-download past
  reports saved locally

## Local setup
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # then fill in real values
streamlit run app.py
```

## Deploying on Streamlit Community Cloud
1. Push this folder to a GitHub repo (`.streamlit/secrets.toml`, `.sessions/`,
   and `reports/` are gitignored — never commit real secrets).
2. On [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at the repo / `app.py`.
3. In the app's **Settings → Secrets**, paste:
   ```toml
   GROQ_API_KEY = "gsk_..."
   RESEND_API_KEY = "re_..."
   RESEND_FROM_ADDRESS = "Yale Brown Report <onboarding@resend.dev>"
   ADMIN_PASSWORD = "choose-a-password"
   ```
4. Reports are emailed to `THERAPIST_EMAIL` in `ybocs/email_utils.py`
   (currently `Wijdan.psyc@gmail.com`, matching the other assessment apps in
   this workspace) — update that constant if it should be a different inbox.

## Project structure
```
app.py                       Streamlit UI / flow, language toggle, admin portal
ybocs/
  questions.py / questions_ar.py   Symptom Checklist + Severity Scale item banks
  scoring.py                        Scoring logic (subtotals, bands, checklist counts)
  content.py                        Severity-band descriptions, OCD symptom dimensions
  i18n.py                           UI chrome strings (English/Arabic)
  groq_utils.py                     Groq LLM calls for both report narratives
  pdf_base.py                       Shared PDF palette, fonts (incl. Arabic RTL), charts
  report_client.py                  Client-facing PDF (bilingual)
  report_therapist.py               Therapist confidential PDF (bilingual appendix)
  email_utils.py                    Resend email delivery (therapist only)
  persistence.py                    File-backed autosave for in-progress sessions
fonts/                        Noto Naskh Arabic (static instances) for PDF rendering
.streamlit/
  config.toml                 Theme
  secrets.toml.example        Template for required secrets
```

## Source material
Item wording follows Goodman, Rasmussen, Mazure, et al. (1989), *The
Yale-Brown Obsessive Compulsive Scale*, Archives of General Psychiatry,
46, 1006–1011, as reproduced in the clinic's Y-BOCS packet; self-report
adaptation by Lee Baer (1991); severity-band cut-points as commonly used in
clinical practice (0–7 Subclinical, 8–15 Mild, 16–23 Moderate, 24–31 Severe,
32–40 Extreme). The Arabic Severity Scale wording follows the structure of
the widely used CBTarabia.com Arabic Y-BOCS adaptation.
