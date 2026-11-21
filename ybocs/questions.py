"""Y-BOCS item bank: Symptom Checklist (58 items, English) and the 10-item
+ insight-item Severity Scale (English). Arabic equivalents live in
questions_ar.py. Source: Goodman, Rasmussen, Mazure et al. (1989), self-report
adaptation by Lee Baer (1991), as reproduced in the clinic's Y-BOCS packet.
"""

# ---------------------------------------------------------------------------
# Symptom Checklist — categories in canonical publication order.
# Each category: (category_key, category_label, [(item_id, text, example), ...])
# ---------------------------------------------------------------------------

CHECKLIST_CATEGORIES = [
    ("aggressive", "Aggressive Obsessions", [
        (1, "I fear I might harm myself", "Fear of eating with a knife or fork, fear of handling sharp objects, fear of walking near glass windows"),
        (2, "I fear I might harm other people", "Fear of poisoning other people's food, fear of harming babies, fear of pushing someone in front of a train"),
        (3, "I have violent or horrific images in my mind", "Images of murder, dismembered bodies, or other disgusting scenes"),
        (4, "I fear I will blurt out obscenities", "Fear of shouting obscenities in public situations like church or class"),
        (5, "I fear doing something embarrassing", "Fear of appearing foolish in social situations"),
        (6, "I fear I will act on an unwanted impulse", "Fear of driving a car into a tree, fear of running someone over, fear of stabbing a friend"),
        (7, "I fear I will steal things", "Fear of “cheating” a cashier, fear of shoplifting inexpensive items"),
        (8, "I fear that I'll harm others because I'm not careful enough", "Fear of causing an accident without being aware of it (such as a hit-and-run accident)"),
        (9, "I fear I'll be responsible for something else terrible happening", "Fear of causing a fire or burglary because of not being careful enough in checking the house"),
    ]),
    ("contamination", "Contamination Obsessions", [
        (10, "I am concerned or disgusted with bodily waste or secretions", "Fear of contracting AIDS, cancer, or other diseases from public rest rooms"),
        (11, "I am concerned with dirt or germs", "Fear of picking up germs from sitting in certain chairs, shaking hands, or touching door handles"),
        (12, "I am excessively concerned with environmental contaminants", "Fear of being contaminated by asbestos or radon, radioactive substances, toxic waste sites"),
        (13, "I am excessively concerned with certain household cleansers", "Fear of poisonous kitchen or bathroom cleansers, solvents, insect spray or turpentine"),
        (14, "I am excessively concerned with animals", "Fear of being contaminated by touching an insect, dog, cat, or other animal"),
        (15, "I am bothered by sticky substances or residues", "Fear of adhesive tape or other sticky substances that may trap contaminants"),
        (16, "I am concerned that I will get ill because of contamination", "Fear of getting ill as a direct result of being contaminated"),
        (17, "I am concerned that I will contaminate others", "Fear of touching other people or preparing their food after touching a poisonous substance"),
    ]),
    ("sexual", "Sexual Obsessions", [
        (18, "I have forbidden or perverse sexual thoughts, images, or impulses", "Unwanted sexual thoughts about strangers, family, or friends"),
        (19, "I have sexual obsessions that involve children or incest", "Unwanted thoughts about sexually molesting either your own children or other children"),
        (20, "I have obsessions about homosexuality", "Worries like “Am I a homosexual?” when there is no basis for these thoughts"),
        (21, "I have obsessions about aggressive sexual behavior toward other people", "Unwanted images of violent sexual behavior toward adult strangers, friends, or family"),
    ]),
    ("hoarding_obs", "Hoarding / Saving Obsessions", [
        (22, "I have obsessions about hoarding or saving things", "Worries about throwing away seemingly unimportant things that you might need in the future"),
    ]),
    ("religious", "Religious Obsessions", [
        (23, "I am concerned with sacrilege and blasphemy", "Worries about having blasphemous thoughts, saying blasphemous things, or being punished for such things"),
        (24, "I am excessively concerned with morality", "Worries about always doing “the right thing,” having told a lie, or having cheated someone"),
    ]),
    ("symmetry", "Need for Symmetry or Exactness", [
        (25, "I have obsessions about symmetry or exactness", "Worries about papers and books being properly aligned, calculations or handwriting being perfect"),
    ]),
    ("misc_obsessions", "Miscellaneous Obsessions", [
        (26, "I feel that I need to know or remember certain things", "Belief that you need to remember insignificant things like license plate numbers"),
        (27, "I fear saying certain things", "Fear of saying certain words (such as “thirteen”) because of superstitions"),
        (28, "I fear not saying just the right thing", "Fear of having said the wrong thing, fear of not using the “perfect” word"),
        (29, "I fear losing things", "Worries about losing a wallet or other unimportant objects, like a scrap of note paper"),
        (30, "I am bothered by intrusive (neutral) mental images", "Random, unwanted images in your mind"),
        (31, "I am bothered by intrusive mental nonsense sounds, words or music", "Words, songs, or music in your mind that you can't stop"),
        (32, "I am bothered by certain sounds or noises", "Worries about the sounds of clocks ticking loudly or voices in another room"),
        (33, "I have lucky and unlucky numbers", "Worries about common numbers (like thirteen) that may cause you to perform activities a certain number of times"),
        (34, "Certain colors have special significance to me", "Fear of using objects of certain colors (e.g. black may be associated with death)"),
        (35, "I have superstitious fears", "Fear of passing a cemetery, hearse, or black cat; fear of omens associated with death"),
    ]),
    ("somatic", "Somatic Obsessions", [
        (36, "I am concerned with illness or disease", "Worries that you have an illness like cancer, heart disease or AIDS, despite reassurance"),
        (37, "I am excessively concerned with a part of my body or an aspect of my appearance", "Worries that your face, ears, nose, eyes, or another part of your body is hideous, ugly"),
    ]),
    ("cleaning", "Cleaning / Washing Compulsions", [
        (38, "I wash my hands excessively or in a ritualized way", "Washing your hands many times a day or for long periods of time"),
        (39, "I have excessive or ritualized showering, bathing, tooth brushing, grooming, or toilet routines", "Taking showers or baths or performing other bathroom routines that may last for several hours"),
        (40, "I have compulsions that involve cleaning household items or other inanimate objects", "Excessive cleaning of faucets, toilets, floors, kitchen counters, or kitchen utensils"),
        (41, "I do other things to prevent or remove contact with contaminants", "Asking family members to handle or remove insecticides, garbage, gasoline cans, raw meat"),
    ]),
    ("checking", "Checking Compulsions", [
        (42, "I check that I did not harm others", "Checking that you haven't hurt someone without knowing it"),
        (43, "I check that I did not harm myself", "Looking for injuries or bleeding after handling sharp or breakable objects"),
        (44, "I check that nothing terrible happened", "Searching the newspaper or listening to the radio for news about some catastrophe"),
        (45, "I check that I did not make a mistake", "Repeated checking of door locks, stoves, electrical outlets, before leaving home"),
        (46, "I check some aspect of my physical condition tied to my obsessions about my body", "Seeking reassurance from friends or doctors that you aren't having a heart attack"),
    ]),
    ("repeating", "Repeating Rituals", [
        (47, "I reread or rewrite things", "Taking hours to read a few pages in a book or to write a short letter"),
        (48, "I need to repeat routine activities", "Repeating activities like turning appliances on and off, combing your hair, going in and out of a doorway"),
    ]),
    ("counting", "Counting Compulsions", [
        (49, "I have counting compulsions", "Counting objects like ceiling or floor tiles, books in a bookcase, nails in a wall"),
    ]),
    ("ordering", "Ordering / Arranging Compulsions", [
        (50, "I have ordering or arranging compulsions", "Straightening paper and pens on a desktop or books in a bookcase"),
    ]),
    ("hoarding_comp", "Hoarding / Collecting Compulsions", [
        (51, "I have compulsions to hoard or collect things", "Saving old newspapers, notes, cans, paper towels, wrappers and empty bottles"),
    ]),
    ("misc_compulsions", "Miscellaneous Compulsions", [
        (52, "I have mental rituals (other than checking/counting)", "Performing rituals in your head, like saying prayers or thinking a “good” thought to undo a “bad” one"),
        (53, "I need to tell, ask, or confess", "Asking other people to reassure you, confessing to wrong behaviors you never even did"),
        (54, "I need to touch, tap, or rub things", "Giving in to the urge to touch rough surfaces, like wood, or hot surfaces, like a stove top"),
        (55, "I take measures (other than checking) to prevent harm or terrible consequences to myself or family", "Staying away from sharp or breakable objects, such as knives, scissors, and fragile glass"),
        (56, "I have ritualized eating behaviors", "Arranging your food, knife, and fork in a particular order before being able to eat"),
        (57, "I have superstitious behaviors", "Not taking a bus or train if its number contains an “unlucky” number, staying in your house on the thirteenth"),
        (58, "I pull my hair out (trichotillomania)", "Pulling hair from your scalp, eyelids, eyelashes, or pubic areas, using your fingers or tweezers"),
    ]),
]

# Flat lookup helpers
CHECKLIST_ITEM_BY_ID = {
    item_id: (cat_key, cat_label, text, example)
    for cat_key, cat_label, items in CHECKLIST_CATEGORIES
    for item_id, text, example in items
}

OBSESSION_CATEGORY_KEYS = [
    "aggressive", "contamination", "sexual", "hoarding_obs", "religious",
    "symmetry", "misc_obsessions", "somatic",
]
COMPULSION_CATEGORY_KEYS = [
    "cleaning", "checking", "repeating", "counting", "ordering",
    "hoarding_comp", "misc_compulsions",
]

# ---------------------------------------------------------------------------
# Severity Scale — 10 scored items (0-4) + 1 unscored insight item.
# Each: id, kind ("obsession"/"compulsion"/"insight"), title, question, options[5]
# ---------------------------------------------------------------------------

SEVERITY_ITEMS = [
    {
        "id": 1, "kind": "obsession",
        "title": "Time Occupied by Obsessive Thoughts",
        "question": "How much of your time was occupied by obsessive thoughts? How frequently did these thoughts occur?",
        "options": [
            "None",
            "Less than 1 hour per day, or occasional intrusions (no more than 8 times a day)",
            "1–3 hours per day, or frequent intrusions (most hours of the day are free of obsessions)",
            "More than 3 and up to 8 hours per day, or very frequent intrusions",
            "More than 8 hours per day, or near-constant intrusions",
        ],
    },
    {
        "id": 2, "kind": "obsession",
        "title": "Interference Due to Obsessive Thoughts",
        "question": "How much did these thoughts interfere with your social or work functioning? Is there anything you didn't do because of them?",
        "options": [
            "No interference",
            "Mild, slight interference with social or occupational performance, but overall performance not impaired",
            "Moderate, definite interference with social or occupational performance, but still manageable",
            "Severe interference, causes substantial impairment in social or occupational performance",
            "Extreme, incapacitating interference",
        ],
    },
    {
        "id": 3, "kind": "obsession",
        "title": "Distress Associated with Obsessive Thoughts",
        "question": "How much distress did your obsessive thoughts cause you?",
        "options": [
            "None",
            "Mild, infrequent, and not too disturbing distress",
            "Moderate, frequent, and disturbing distress, but still manageable",
            "Severe, very frequent, and very disturbing distress",
            "Extreme, near-constant, and disabling distress",
        ],
    },
    {
        "id": 4, "kind": "obsession",
        "title": "Resistance Against Obsessions",
        "question": "How much effort did you make to resist the obsessive thoughts? How often did you try to disregard or turn your attention away from them?",
        "options": [
            "I made an effort to always resist (or the obsessions are so minimal there is no need to actively resist)",
            "I tried to resist most of the time",
            "I made some effort to resist",
            "I allowed all obsessions to fill my mind without attempting to control them, but with some reluctance",
            "I completely and willingly gave in to all obsessions",
        ],
    },
    {
        "id": 5, "kind": "obsession",
        "title": "Degree of Control Over Obsessive Thoughts",
        "question": "How much control did you have over your obsessive thoughts? How successful were you in stopping or diverting them?",
        "options": [
            "Complete control",
            "Much control; usually I could stop or divert obsessions with some effort and concentration",
            "Moderate control; sometimes I could stop or divert obsessions",
            "Little control; rarely successful in stopping obsessions, could only divert attention with great difficulty",
            "No control; rarely able to even momentarily ignore the obsessions",
        ],
    },
    {
        "id": 6, "kind": "compulsion",
        "title": "Time Spent Performing Compulsive Behaviors",
        "question": "How much time did you spend performing compulsive behaviors? How frequently did you perform compulsions?",
        "options": [
            "None",
            "Less than 1 hour per day, or occasional performance of compulsions (no more than 8 times per day)",
            "1–3 hours per day, or frequent performance of compulsions (most hours free of compulsions)",
            "More than 3 and up to 8 hours per day, or very frequent performance of compulsions",
            "More than 8 hours per day, or near-constant performance of compulsions",
        ],
    },
    {
        "id": 7, "kind": "compulsion",
        "title": "Interference Due to Compulsive Behaviors",
        "question": "How much did your compulsive behaviors interfere with your social or work functioning?",
        "options": [
            "No interference",
            "Mild, slight interference with social or occupational activities, but overall performance not impaired",
            "Moderate, definite interference with social or occupational performance, but still manageable",
            "Severe interference, substantial impairment in social or occupational performance",
            "Extreme, incapacitating interference",
        ],
    },
    {
        "id": 8, "kind": "compulsion",
        "title": "Distress Associated with Compulsive Behaviors",
        "question": "How would you have felt if prevented from performing your compulsions? How anxious would you have become?",
        "options": [
            "Not at all anxious",
            "Only slightly anxious if compulsions prevented",
            "Anxiety would mount but remain manageable if compulsions prevented",
            "Prominent and very disturbing increase in anxiety if compulsions interrupted",
            "Extreme, incapacitating anxiety from any intervention aimed at reducing the compulsions",
        ],
    },
    {
        "id": 9, "kind": "compulsion",
        "title": "Resistance Against Compulsions",
        "question": "How much effort did you make to resist the compulsions? How often did you try to stop the compulsions?",
        "options": [
            "I made an effort to always resist (or symptoms were so minimal there was no need to actively resist)",
            "I tried to resist most of the time",
            "I made some effort to resist",
            "I yielded to almost all compulsions without attempting to control them, but with some reluctance",
            "I completely and willingly yielded to all compulsions",
        ],
    },
    {
        "id": 10, "kind": "compulsion",
        "title": "Degree of Control Over Compulsive Behaviors",
        "question": "How much control did you have over the compulsive behaviors? How successful were you in stopping the ritual(s)?",
        "options": [
            "Complete control",
            "Usually I could stop compulsions or rituals with some effort and willpower",
            "Sometimes I could stop compulsive behaviors, but only with difficulty",
            "I could only delay the compulsive behaviors, but eventually had to carry them out to completion",
            "Rarely able to even momentarily delay performing the compulsive behaviors",
        ],
    },
    {
        "id": 11, "kind": "insight",
        "title": "Insight into Obsessions and Compulsions",
        "question": "Do you think your obsessions or compulsions are reasonable or rational? Do you think something would really happen if you resisted them?",
        "options": [
            "I think my obsessions or compulsions are unreasonable or excessive",
            "I think they are unreasonable or excessive, but I'm not completely convinced that they aren't necessary",
            "I think my obsessions or compulsions may be unreasonable or excessive",
            "I don't think my obsessions or compulsions are unreasonable or excessive",
            "I am sure my obsessions or compulsions are reasonable, no matter what anyone says",
        ],
    },
]

SCORED_SEVERITY_ITEMS = [q for q in SEVERITY_ITEMS if q["kind"] != "insight"]
OBSESSION_SEVERITY_ITEMS = [q for q in SEVERITY_ITEMS if q["kind"] == "obsession"]
COMPULSION_SEVERITY_ITEMS = [q for q in SEVERITY_ITEMS if q["kind"] == "compulsion"]
INSIGHT_ITEM = next(q for q in SEVERITY_ITEMS if q["kind"] == "insight")
