# NLP-based emotion detection using HuggingFace

from transformers import pipeline

# Load Hugging Face Sentiment Pipeline
sentiment_model = pipeline("sentiment-analysis")

def analyze_sentiment(text: str) -> dict:
    text = text.strip()

    if not text:
        return {"label": "NEUTRAL", "score": 0.0}

    result = sentiment_model(text[:512])[0]  # limit length for safety
    return {
        "label": result["label"],
        "score": round(result["score"], 2)
    }

if __name__ == "__main__":
    sample = "I feel very excited about the upcoming field trip, at the same time sad because my close friend is not coming"
    print(analyze_sentiment(sample))
