"""
Risk Score Engine v4 (Adaptive & Extensible)
-------------------------------------------

A future-ready distress estimation engine for MyJournie.

Inputs:
- user_message (str)
- sentiment: {"label": "...", "score": float}
- context: str (recent conversation history)

Output:
- risk (0–10)

Features:
- Auto-expanding keyword detection
- Emotion + sentiment weighted scoring
- Catastrophizing/rumination detection
- Negative pattern recognition
- Message structure heuristics
- Multi-turn context sensitivity
"""

import re
from typing import Dict, List


# -----------------------------------------------------------
# 1. Master lexical lists (human-curated + expandable)
# -----------------------------------------------------------

BASE_SEVERE = [
    "suicide", "kill myself", "end my life", "want to die",
    "can't go on", "self harm", "harm myself",
    "cut myself", "no point living", "want to disappear"
]

BASE_MODERATE = [
    "worthless", "failure", "hate myself",
    "don't care anymore", "nothing matters",
    "i give up", "i'm done", "no hope"
]

# The engine will auto-expand these using simple NLP rules


# -----------------------------------------------------------
# 2. Helper → Auto-expand variations
# -----------------------------------------------------------

def expand_keywords(words: List[str]) -> List[str]:
    """Generate variants like plural, tense changes, spacing, hyphens."""
    expanded = set(words)

    for w in words:
        base = w.lower()

        # remove punctuation spacing variations
        expanded.add(base.replace(" ", ""))
        expanded.add(base.replace(" ", "-"))

        # plural/suffix
        if base.endswith("s"):
            expanded.add(base.rstrip("s"))
        else:
            expanded.add(base + "s")

        # basic tense variants
        if base.endswith("ing"):
            expanded.add(base[:-3])
        if base.endswith("ed"):
            expanded.add(base[:-2])

    return list(expanded)


SEVERE_KEYWORDS = expand_keywords(BASE_SEVERE)
MODERATE_KEYWORDS = expand_keywords(BASE_MODERATE)


# -----------------------------------------------------------
# 3. Linguistic distress signals
# -----------------------------------------------------------

CATASTROPHIZING_PATTERNS = [
    r"\b(always|never|everyone|no one)\b.*(hate|fail|leave|hurt|abandon)",
    r"everything.*(ruined|broken|terrible|falling apart)"
]

RUMINATION_PATTERNS = [
    r"i keep thinking",
    r"i can't stop thinking",
    r"over and over",
    r"my mind won't stop",
]

NEGATION_EMOTION_PATTERNS = [
    r"not good", r"not okay", r"not fine",
    r"don't feel right", r"don't feel good"
]


# -----------------------------------------------------------
# Main: Risk Score Engine V4
# -----------------------------------------------------------

def calculate_risk_score(
    user_message: str,
    sentiment: Dict,
    context: str = ""
) -> int:

    # -------------------------------------------------------
    # Extract normalized sentiment
    # -------------------------------------------------------
    if not isinstance(sentiment, dict):
        sentiment = {"label": "NEUTRAL", "score": 0.0}

    label = sentiment.get("label", "NEUTRAL")
    score = float(sentiment.get("score", 0.0))

    text = user_message.lower()
    ctx = context.lower() if context else ""

    risk = 0

    # -------------------------------------------------------
    # 1. Sentiment weighting
    # -------------------------------------------------------
    if label == "NEGATIVE":
        risk += int(score * 4)
    elif label == "NEUTRAL":
        risk += 0
    else:
        risk -= 1  # slight reduction for positive mood

    # -------------------------------------------------------
    # 2. Severe keyword hits
    # -------------------------------------------------------
    for word in SEVERE_KEYWORDS:
        if word in text:
            risk += 6

    # Context echoes severe terms
    if any(word in ctx for word in SEVERE_KEYWORDS):
        risk += 2

    # -------------------------------------------------------
    # 3. Moderate keyword hits
    # -------------------------------------------------------
    for word in MODERATE_KEYWORDS:
        if word in text:
            risk += 3

    if any(word in ctx for word in MODERATE_KEYWORDS):
        risk += 1

    # -------------------------------------------------------
    # 4. Linguistic pattern detectors
    # -------------------------------------------------------

    # Catastrophizing
    for pattern in CATASTROPHIZING_PATTERNS:
        if re.search(pattern, text):
            risk += 2

    # Rumination loops
    for pattern in RUMINATION_PATTERNS:
        if re.search(pattern, text):
            risk += 2

    # Negative emotional negation patterns
    for pattern in NEGATION_EMOTION_PATTERNS:
        if pattern in text:
            risk += 1

    # -------------------------------------------------------
    # 5. Behavioral text signals
    # -------------------------------------------------------

    # Excessive exclamation marks
    if text.count("!") >= 3:
        risk += 1

    # ALL CAPS emotional words
    if len(re.findall(r"\b[A-Z]{3,}\b", user_message)) >= 2:
        risk += 1

    # Very short or very long messages
    if len(user_message) < 5:
        risk += 1
    if len(user_message) > 500:
        risk += 1

    # Repetition of distress words
    repeated = len(re.findall(r"(sad|tired|hate|alone)", text))
    if repeated >= 3:
        risk += 1

    # -------------------------------------------------------
    # 6. Clamp score to 0–10
    # -------------------------------------------------------
    risk = max(0, min(10, risk))

    return risk
