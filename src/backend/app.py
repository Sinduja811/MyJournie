# src/backend/app.py

from fastapi import FastAPI
from src.backend.routers.memory_router import router as memory_router
from src.backend.routers.chat_router import router as chat_router

from pydantic import BaseModel
from src.ai.sentiment_analyzer import analyze_sentiment
from src.ai.risk_score_engine import calculate_risk_score
from src.backend.storage import save_entry, get_history
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="MyJournie Backend")

# Register routers
app.include_router(memory_router)
app.include_router(chat_router)


class JournalEntry(BaseModel):
    text: str


@app.get("/")
def home():
    return {"message": "MyJournie API is running"}


@app.post("/analyze")
def analyze(entry: JournalEntry):
    sentiment = analyze_sentiment(entry.text)
    risk = calculate_risk_score(sentiment)

    return {
        "sentiment": sentiment,
        "risk_score": risk
    }


@app.post("/journal")
def journal(entry: JournalEntry):
    sentiment = analyze_sentiment(entry.text)
    risk = calculate_risk_score(sentiment)

    saved = save_entry({
        "type": "journal",
        "text": entry.text,
        "sentiment": sentiment,
        "risk": risk
    })

    history = get_history()

    return {
        "message": "Journal saved",
        "entry": saved,
        "history": history
    }
