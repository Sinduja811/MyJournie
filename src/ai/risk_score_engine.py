# Weighted scoring logic (RALE formula)

"""
Basic Risk Score Engine (RALE v0.1)
Maps sentiment label + confidence → numerical mental wellness risk score (0–100)
"""

def calculate_risk_score(sentiment: dict) -> int:
    label = sentiment.get("label", "NEUTRAL")
    score = sentiment.get("score", 0)

    # NEGATIVE sentiment → higher risk
    if label == "NEGATIVE":
        base = 70  # baseline concern for negative mood
        return min(100, int(base + (score * 30)))  # scale severity

    # POSITIVE sentiment → low risk
    elif label == "POSITIVE":
        base = 10
        return max(0, int(base - (score * 10)))  # lower risk with positivity

    # NEUTRAL or unknown sentiment
    return 50  # neutral state, unknown mood


if __name__ == "__main__":
    test_cases = [
        {"label": "NEGATIVE", "score": 0.77},
        {"label": "NEGATIVE", "score": 0.40},
        {"label": "POSITIVE", "score": 0.80},
        {"label": "NEUTRAL", "score": 0.00},
    ]
    
    for case in test_cases:
        print(case, "-> Risk:", calculate_risk_score(case))
