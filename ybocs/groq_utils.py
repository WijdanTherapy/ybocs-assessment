"""Groq-powered report generation for the Y-BOCS assessment.

Two calls are made per submission:
  1. generate_client_narrative()  -> plain supportive text for the CLIENT report
     (psychoeducational, non-alarming, strengths-aware, never a diagnosis).
  2. generate_therapist_intervention() -> structured JSON for the THERAPIST
     confidential report (clinical formulation, differential considerations,
     symptom-dimension analysis, treatment planning, session material).

Both use Groq's OpenAI-compatible chat completions endpoint. Free key:
https://console.groq.com/keys
"""

import json
import re
import time
import urllib.request
import urllib.error

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"

CLIENT_SYSTEM_PROMPT = """You are a licensed clinical psychologist writing a brief, warm, plain-language \
summary directly for a client who just completed the Yale-Brown Obsessive-Compulsive Scale (Y-BOCS). \
This text will appear in a report the client may read themselves.

Hard rules:
- Never use the word "diagnosis" or state that the client "has OCD" - describe symptom levels and \
patterns, not a diagnostic conclusion. That determination belongs to their clinician.
- Be warm, validating, and free of jargon. Avoid clinical labels where a plain description works.
- Do not catastrophize a high score or dismiss a low one. Every score level gets a respectful, \
non-alarming, hope-forward tone.
- Keep it concrete and specific to this client's actual item patterns, not generic OCD text.
- Output ONLY valid JSON matching the schema below. No markdown fences, no commentary outside the JSON.
"""

CLIENT_JSON_SCHEMA = """
Return a single JSON object with exactly this shape:
{
  "overview": "string - 2-3 sentences summarizing what the assessment measured and this client's overall pattern, in plain language",
  "what_stood_out": "string - 1-2 paragraphs naming the specific themes/categories that showed up most for this client (from their checklist), described supportively",
  "strengths_noted": "string - 1 short paragraph noting any protective factors evident in the data (e.g. partial resistance, partial control, areas with no symptoms)",
  "next_steps": "string - 1 short paragraph, warm and practical, encouraging continued work with their therapist, without prescribing specific clinical techniques"
}
"""

THERAPIST_SYSTEM_PROMPT = """You are assisting a licensed psychotherapist by turning a client's Y-BOCS \
(Yale-Brown Obsessive-Compulsive Scale) results into practitioner-facing clinical material. You write \
ONLY for the practitioner's own confidential use - never content to hand directly to the client unedited.

Hard rules:
- You are not making a diagnosis. Use hedged, clinically appropriate language ("consistent with",
  "suggests", "warrants further assessment of") rather than declarative diagnostic statements.
- Ground every section in the specific item-level data given to you (which symptom categories were
  endorsed, which severity items scored highest, the obsession/compulsion balance, insight level).
  Avoid generic OCD-textbook filler that could apply to any client.
- Explicitly flag anything in the data that could indicate risk (e.g. aggressive/harm obsessions items
  1-2-3, checking that one might harm others/self items 42-43) as warranting direct clinical risk
  assessment - never assume risk, but never omit the flag when those categories are endorsed as current.
- Differential considerations should mention plausible alternative/co-occurring presentations that can
  mimic or accompany high Y-BOCS scores where relevant (e.g. GAD, BDD, hoarding disorder, autism-spectrum
  repetitive behaviors, psychotic-spectrum intrusive thoughts if insight is very poor) - framed as
  "consider ruling out" / "warrants differentiation from", not as conclusions.
- Treatment recommendations should be evidence-based (ERP/CBT first-line, SSRI augmentation at higher
  severity, consider higher level of care at extreme/incapacitating severity) and tailored to this
  client's specific symptom dimensions.
- Output ONLY valid JSON matching the exact schema given in the user message. No markdown fences, no
  commentary outside the JSON object.
"""

THERAPIST_JSON_SCHEMA = """
Return a single JSON object with exactly this shape:
{
  "clinical_formulation": {
    "symptom_pattern_summary": "string - 1-2 paragraphs describing the specific obsession/compulsion pattern evident in this client's data",
    "functional_impact": "string - 1 paragraph on likely functional impact based on the interference/distress items",
    "insight_level": "string - 1-2 sentences interpreting item 11 (insight) and its treatment implications",
    "maintaining_factors": "string - 1 paragraph hypothesizing what is likely maintaining the cycle (avoidance, reassurance-seeking, ritual reinforcement) based on the specific items endorsed",
    "risk_flags": "string - explicit, direct statement of any risk-relevant content in the data requiring direct clinical risk assessment, or 'No risk-relevant content flagged by the item data; standard risk screening still recommended.' if none"
  },
  "differential_considerations": ["string - 3-5 items, each a specific alternative/co-occurring consideration relevant to THIS profile, hedged appropriately"],
  "symptom_dimension_breakdown": [
    {"dimension": "string", "relevance": "string - how prominent this dimension is for this client and why", "clinical_note": "string"}
  ],
  "strengths_and_resources": ["string - 3-5 items grounded in the resistance/control item scores and checklist pattern"],
  "treatment_recommendations": [
    {"modality": "string e.g. ERP / CBT / SSRI consult / Family accommodation reduction", "rationale": "string", "priority": "string - High/Medium/Low", "implementation_note": "string"}
  ],
  "session_questions": ["string - 5-8 open-ended questions tailored to this client's specific endorsed items, for use in the next session"],
  "session_roadmap": [
    {"phase": "string", "focus": "string"}
  ]
}
Provide exactly 4-5 symptom_dimension_breakdown entries (one per dimension given, omit dimensions with
zero endorsed items), 3-6 treatment_recommendations ordered by priority, and 4-6 session_roadmap phases.
"""


def _build_client_context(client_name, scores, endorsed_current, lang_note):
    lines = [
        f"Client identifier: {client_name or 'Confidential Client'}",
        f"Obsessions subtotal (items 1-5, 0-20): {scores['obsession_subtotal']}",
        f"Compulsions subtotal (items 6-10, 0-20): {scores['compulsion_subtotal']}",
        f"Total severity score (0-40): {scores['total']} -- band: {scores['band']}",
        f"Insight (item 11, 0=good insight - 4=poor insight): {scores['insight']}",
        "Symptom categories currently endorsed (checklist):",
    ]
    if endorsed_current:
        for cat_label, texts in endorsed_current.items():
            lines.append(f"  {cat_label}: " + "; ".join(texts))
    else:
        lines.append("  (none marked as current)")
    lines.append(lang_note)
    return "\n".join(lines)


def _build_therapist_context(client_name, scores, severity_answers, severity_items,
                              category_counts, endorsed_current):
    lines = [
        f"Client identifier: {client_name or 'Confidential Client'}",
        f"Obsessions subtotal (items 1-5, 0-20): {scores['obsession_subtotal']}",
        f"Compulsions subtotal (items 6-10, 0-20): {scores['compulsion_subtotal']}",
        f"Total severity score (0-40): {scores['total']} -- band: {scores['band']}",
        f"Insight (item 11, 0=good insight - 4=poor/absent insight): {scores['insight']}",
        "",
        "Severity Scale item-by-item scores (0-4 each):",
    ]
    for q in severity_items:
        val = severity_answers.get(q["id"])
        lines.append(f"  {q['id']}. {q['title']}: {val}")

    lines.append("")
    lines.append("Symptom Checklist category counts (current / past-only / total items in category):")
    for cat_key, cat_label, current, past_only, total_items in category_counts:
        if current or past_only:
            lines.append(f"  {cat_label}: {current} current, {past_only} past-only, out of {total_items}")

    lines.append("")
    lines.append("Specific items currently endorsed:")
    if endorsed_current:
        for cat_label, texts in endorsed_current.items():
            lines.append(f"  {cat_label}: " + "; ".join(texts))
    else:
        lines.append("  (none marked as current)")
    return "\n".join(lines)


def _call_groq_once(payload, api_key, timeout):
    req = urllib.request.Request(
        GROQ_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; YBOCSClinicalTool/1.0)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        err = RuntimeError(f"Groq API error {e.code}: {detail[:500]}")
        err.retryable = (e.code == 400 and "json_validate_failed" in detail)
        if e.code == 429:
            m = re.search(r"try again in ([\d.]+)s", detail)
            err.retry_after = float(m.group(1)) + 1 if m else 5.0
            err.retryable = True
        raise err from e
    except urllib.error.URLError as e:
        err = RuntimeError(f"Could not reach Groq API: {e.reason}")
        err.retryable = True
        raise err from e

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        err = RuntimeError(f"Unexpected Groq response shape: {body}")
        err.retryable = False
        raise err from e

    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:]
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        err = RuntimeError(f"Groq did not return valid JSON: {e}\nRaw content: {content[:800]}")
        err.retryable = True
        raise err from e


def _call_with_retry(payload, api_key, timeout, max_attempts):
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Get a free key at https://console.groq.com/keys "
            "and add it to Streamlit secrets.")
    last_err = None
    for attempt in range(max_attempts):
        try:
            return _call_groq_once(payload, api_key, timeout)
        except RuntimeError as e:
            last_err = e
            if not getattr(e, "retryable", False) or attempt == max_attempts - 1:
                raise
            time.sleep(min(getattr(e, "retry_after", 1.0), 30.0))
    raise last_err


def generate_client_narrative(client_name, scores, endorsed_current, api_key,
                               model=None, timeout=60, max_attempts=2):
    # Report narrative is always English per clinic policy, regardless of
    # which language the client answered in - only the Q&A appendix (built
    # separately, see pdf_base.build_qa_appendix) reflects answer language.
    lang_note = "Write the JSON string values in English."
    context = _build_client_context(client_name, scores, endorsed_current, lang_note)
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": CLIENT_SYSTEM_PROMPT},
            {"role": "user", "content": "Client's Y-BOCS results:\n\n" + context + "\n\n" + CLIENT_JSON_SCHEMA},
        ],
        "temperature": 0.5,
        "response_format": {"type": "json_object"},
    }
    return _call_with_retry(payload, api_key, timeout, max_attempts)


def generate_therapist_intervention(client_name, scores, severity_answers, severity_items,
                                     category_counts, endorsed_current, api_key,
                                     model=None, timeout=60, max_attempts=2):
    context = _build_therapist_context(
        client_name, scores, severity_answers, severity_items, category_counts, endorsed_current)
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": THERAPIST_SYSTEM_PROMPT},
            {"role": "user", "content": "Client's Y-BOCS results:\n\n" + context + "\n\n" + THERAPIST_JSON_SCHEMA},
        ],
        "temperature": 0.55,
        "response_format": {"type": "json_object"},
    }
    return _call_with_retry(payload, api_key, timeout, max_attempts)
