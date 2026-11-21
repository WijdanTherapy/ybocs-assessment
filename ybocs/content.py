# -*- coding: utf-8 -*-
"""Static clinical content: severity-band descriptions and OCD symptom-dimension
summaries, in English and Arabic. Band cut-points follow Goodman, Rasmussen,
Mazure et al. (1989) and the widely used clinical interpretation grid
reproduced in the Arabic Y-BOCS adaptation (CBTarabia.com)."""

BAND_DESCRIPTIONS = {
    "en": {
        "Subclinical": "Symptoms are minimal and generally do not require treatment unless they are concentrated in a narrow, high-impact area (e.g. significant avoidance despite a low total).",
        "Mild": "Mild symptoms that are nonetheless likely to interfere with daily life in noticeable ways; monitoring and early intervention are reasonable.",
        "Moderate": "Moderate symptoms. A score of 16 is the threshold typically used as a minimum entry criterion for OCD treatment trials.",
        "Severe": "Marked symptoms likely to meaningfully impair quality of life, relationships, and occupational or academic functioning.",
        "Extreme": "Severe, often incapacitating symptoms; specialist OCD treatment (e.g. ERP, and/or pharmacotherapy) is typically indicated.",
    },
    "ar": {
        "Subclinical": "أعراض ضئيلة جدًا ولا تتطلب عادة علاجًا إلا إذا كانت مركزة في مجال ضيق ذي تأثير كبير (مثل تجنب واضح رغم انخفاض المجموع الكلي).",
        "Mild": "أعراض خفيفة ولكنها قد تتعارض مع الحياة اليومية بشكل ملحوظ؛ المتابعة والتدخل المبكر خيار مناسب.",
        "Moderate": "أعراض متوسطة. تعتبر الدرجة 16 الحد الأدنى المعتمد غالبًا للدخول في دراسات علاج اضطراب الوسواس القهري.",
        "Severe": "أعراض ملحوظة من المرجح أن تؤثر بشكل كبير على جودة الحياة والعلاقات والأداء الوظيفي أو الدراسي.",
        "Extreme": "أعراض شديدة وغالبًا ما تكون مُعجزة؛ يُعد العلاج المتخصص للوسواس القهري (مثل التعرض ومنع الاستجابة و/أو العلاج الدوائي) مؤشرًا في هذه الحالة.",
    },
}

BAND_LABEL_AR = {
    "Subclinical": "خفيف جدًا",
    "Mild": "خفيف",
    "Moderate": "متوسط",
    "Severe": "ملحوظ",
    "Extreme": "شديد",
}

BAND_COLOR_HEX = {
    "Subclinical": "#3F7D5B",
    "Mild": "#5B8A3F",
    "Moderate": "#C98A3E",
    "Severe": "#B8622E",
    "Extreme": "#9B3B3B",
}

# Mapping of Y-BOCS Symptom Checklist categories onto the 4-5 empirically
# derived OCD symptom dimensions (Mataix-Cols et al., meta-analytic factor
# structure; Bloch et al. 2008 meta-analysis of Y-BOCS checklist factor studies).
SYMPTOM_DIMENSIONS = {
    "harm_checking": {
        "label_en": "Harm / Checking",
        "label_ar": "الأذى والتحقق",
        "categories": ["aggressive", "checking"],
    },
    "contamination_cleaning": {
        "label_en": "Contamination / Cleaning",
        "label_ar": "التلوث والتنظيف",
        "categories": ["contamination", "cleaning"],
    },
    "symmetry_ordering": {
        "label_en": "Symmetry / Ordering / Repeating / Counting",
        "label_ar": "التناظر والترتيب والتكرار والعد",
        "categories": ["symmetry", "ordering", "repeating", "counting"],
    },
    "hoarding": {
        "label_en": "Hoarding",
        "label_ar": "الادخار",
        "categories": ["hoarding_obs", "hoarding_comp"],
    },
    "taboo": {
        "label_en": "Taboo Thoughts (Sexual / Religious / Somatic) & Mental Rituals",
        "label_ar": "الأفكار المحرمة (جنسية/دينية/جسد\064aة) والطقوس الذهنية",
        "categories": ["sexual", "religious", "somatic", "misc_obsessions", "misc_compulsions"],
    },
}
