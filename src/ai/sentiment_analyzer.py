"""
Sentiment Analyzer for MyJournie
--------------------------------

Uses HuggingFace DistilBERT sentiment pipeline.

This module returns a **standardized structured sentiment object**:

    {
        "label": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
        "score": float
    }

Why structured?
- Compatible with Risk Engine v3 (multi-signal)
- Compatible with chatbot_engine.py
- Works cleanly with Pydantic
- Future-proof for emotion models

"""

from transformers import pipeline
from typing import Dict

# -----------------------------------------------------------
# Load model once at startup
# -----------------------------------------------------------
_sentiment = pipeline("sentiment-analysis")


# -----------------------------------------------------------
# Analyze Sentiment
# -----------------------------------------------------------
def analyze_sentiment(text: str) -> Dict[str, float]:
    """
    Returns:
        {
            "label": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
            "score": float
        }
    """

    if not text or not text.strip():
        return {"label": "NEUTRAL", "score": 0.0}

    text = text.strip()[:512]  # safety limit

    try:
        result = _sentiment(text)[0]  # {'label': 'POSITIVE', 'score': 0.99}
        raw_label = str(result.get("label", "")).upper().strip()
        score = float(result.get("score", 0.0))
    except Exception:
        # Fail-safe output
        return {"label": "NEUTRAL", "score": 0.0}

    # Normalize label
    if raw_label == "POSITIVE":
        label = "POSITIVE"
    elif raw_label == "NEGATIVE":
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    return {
        "label": label,
        "score": round(score, 4)
    }


# -----------------------------------------------------------
# Manual tester
# -----------------------------------------------------------
if __name__ == "__main__":
    sample = "I feel happy about the achievement, but also sad it took so long."
    print(analyze_sentiment(sample))
