"""Y-BOCS scoring logic.

Severity items 1-5 = obsessions subtotal (0-20), items 6-10 = compulsions
subtotal (0-20), total = 0-40. Item 11 (insight) is reported separately and
is NOT part of the total, per the original Goodman et al. (1989) scale.
"""

SEVERITY_BANDS = [
    (0, 8, "Subclinical"),
    (8, 16, "Mild"),
    (16, 24, "Moderate"),
    (24, 32, "Severe"),
    (32, 41, "Extreme"),
]


def band_for_total(total):
    for low, high, label in SEVERITY_BANDS:
        if low <= total < high:
            return label
    return SEVERITY_BANDS[-1][2]


def score_severity(severity_answers):
    """severity_answers: dict {item_id (1-11): 0-4}."""
    obsession_total = sum(severity_answers.get(i, 0) for i in range(1, 6))
    compulsion_total = sum(severity_answers.get(i, 0) for i in range(6, 11))
    total = obsession_total + compulsion_total
    insight = severity_answers.get(11)
    return {
        "obsession_subtotal": obsession_total,
        "compulsion_subtotal": compulsion_total,
        "total": total,
        "band": band_for_total(total),
        "insight": insight,
    }


def checklist_category_counts(checklist_answers, categories):
    """checklist_answers: dict {item_id: {"past": bool, "current": bool}}.
    categories: CHECKLIST_CATEGORIES (or _AR) structure.
    Returns list of (cat_key, cat_label, current_count, past_only_count, total_items)."""
    out = []
    for cat_key, cat_label, items in categories:
        current = 0
        past_only = 0
        for item_id, _text, _ex in items:
            ans = checklist_answers.get(item_id, {})
            if ans.get("current"):
                current += 1
            elif ans.get("past"):
                past_only += 1
        out.append((cat_key, cat_label, current, past_only, len(items)))
    return out


def endorsed_items(checklist_answers, categories, only_current=False):
    """Returns list of (item_id, cat_label, text) for endorsed items."""
    out = []
    for cat_key, cat_label, items in categories:
        for item_id, text, _ex in items:
            ans = checklist_answers.get(item_id, {})
            if ans.get("current") or (not only_current and ans.get("past")):
                out.append((item_id, cat_label, text, ans.get("current", False)))
    return out
