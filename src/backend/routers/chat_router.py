# src/backend/routers/chat_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.ai.chatbot_engine import journie_agent

router = APIRouter(prefix="/chat", tags=["chat"])


# ---------------------------
# Request / Response Models
# ---------------------------
class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    text: str = Field(..., min_length=1, description="User message")


class ChatResponse(BaseModel):
    response: str
    sentiment: str
    sentiment_score: float
    risk: int


# ---------------------------
# Chat Endpoint
# ---------------------------
@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest):
    """
    Main chat endpoint.
    Routes user messages → JournieAgent → Gemini → MemoryStore.
    ALWAYS returns a safe, structured response.
    """

    try:
        result = journie_agent.generate_response(
            user_id=payload.user_id,
            user_message=payload.text
        )

        # Ensure the response is ALWAYS compatible with Pydantic
        return ChatResponse(
            response=str(result.get("response", "")),
            sentiment=str(result.get("sentiment", "NEUTRAL")),
            sentiment_score=float(result.get("sentiment_score", 0.0)),
            risk=int(result.get("risk", 0))
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat engine error: {str(e)}"
        )
