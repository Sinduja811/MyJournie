# src/ai/chatbot_engine.py

"""
JOURNIE AGENT ENGINE — Gemini-Compliant, Risk Engine Integrated
------------------------------------------------------------------

A production-grade, psychology-informed journaling companion.

Supports:
- CBT / REBT / ACT / SFBT / DBT-lite micro-interventions
- Conversational memory
- Risk Engine (multi-signal + contextual)
- Sentiment analysis
- Gemini 2.0 Flash compliant message formatting
- Crisis-sensitive but non-clinical guidance
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

from google.generativeai import configure, GenerativeModel

from src.backend.memory import create_prod_memory_store
from src.ai.sentiment_analyzer import analyze_sentiment
from src.ai.risk_score_engine import calculate_risk_score


# -------------------------------------------------------------------
# Load environment variables & configure Gemini
# -------------------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY missing.")

configure(api_key=API_KEY)
model = GenerativeModel("gemini-2.0-flash")


# -------------------------------------------------------------------
# Gemini wrapper — ALWAYS use parts[] (no system role)
# -------------------------------------------------------------------
def to_msg(role: str, text: str) -> Dict[str, Any]:
    return {
        "role": role,
        "parts": [{"text": text}]
    }


# -------------------------------------------------------------------
# Psychology Micro-Prompt Library
# -------------------------------------------------------------------
THERAPY_TECHNIQUES = {
    "cbt_restructure": """
Use a CBT approach:
- Identify automatic thoughts.
- Check evidence for & against them.
- Suggest a balanced alternative.
- Ask one reflective follow-up.
""",

    "rebt_dispute": """
Use REBT:
- Identify rigid “must/should/never” beliefs.
- Check if they are helpful.
- Offer a flexible alternative belief.
""",

    "act_acceptance": """
Use ACT:
- Encourage acceptance rather than suppression of emotions.
- Treat thoughts as temporary events.
- Identify meaningful values.
- Suggest one tiny values-based step.
""",

    "sfbt_scaling": """
Use SFBT:
- Ask a 0–10 scaling question.
- Explore strengths keeping the number from being lower.
- Ask for one small +1 step.
""",

    "dbt_grounding": """
Use DBT grounding:
- Offer 5-4-3-2-1 or simple breathing.
- Keep instructions gentle & present-focused.
""",

    "reflective_support": """
Use reflective listening:
- Validate emotions.
- Mirror their feelings.
- Ask an open, warm clarifying question.
"""
}


# -------------------------------------------------------------------
# Crisis Safety Logic
# -------------------------------------------------------------------
def crisis_check(user_message: str, risk: int) -> str:
    msg = user_message.lower()

    severe_terms = [
        "suicide", "kill myself", "end my life",
        "can't go on", "want to disappear",
        "self harm", "harm myself"
    ]

    if any(term in msg for term in severe_terms) or risk >= 8:
        return (
            "IMPORTANT NOTE:\n"
            "You deserve safety and support. If you're feeling overwhelmed, "
            "consider reaching out to someone you trust or a trained professional. "
            "I’m here to support you emotionally, but I cannot provide emergency help."
        )

    return ""


# -------------------------------------------------------------------
# Therapy Strategy Selector
# -------------------------------------------------------------------
def pick_therapy_strategy(sentiment_label: str, risk: int, user_message: str) -> str:
    msg = user_message.lower()

    if any(k in msg for k in ["stupid", "worthless", "failure"]):
        return "cbt_restructure"

    if any(k in msg for k in ["must", "should", "never", "always"]):
        return "rebt_dispute"

    if any(k in msg for k in ["anxious", "worried", "panic"]):
        return "act_acceptance"

    if "stuck" in msg or "don't know" in msg:
        return "sfbt_scaling"

    if sentiment_label == "NEGATIVE":
        return "dbt_grounding"

    return "reflective_support"


# -------------------------------------------------------------------
# Journie Agent
# -------------------------------------------------------------------
class JournieAgent:
    def __init__(self, memory_store=None):
        self.memory = memory_store or create_prod_memory_store()

    # Memory context loader
    def build_context(self, user_id: str, limit: int = 6):
        mem = self.memory.get_relevant_memory(user_id, limit)
        return [{"role": m["role"], "content": m["content"]} for m in mem]

    # ----------------------------------------------------------------
    # Main Response Method
    # ----------------------------------------------------------------
    def generate_response(self, user_id: str, user_message: str):

        # ------------------------------------------------------------
        # 1. Sentiment + Risk
        # ------------------------------------------------------------
        sentiment_obj = analyze_sentiment(user_message)
        sentiment_label = sentiment_obj["label"]

        context_list = self.build_context(user_id)
        context_text = "\n".join([c["content"] for c in context_list])

        risk = calculate_risk_score(
            user_message=user_message,
            sentiment=sentiment_obj,
            context=context_text
        )

        # Save user message memory
        self.memory.add_memory(
            user_id=user_id,
            role="user",
            content=user_message,
            tags=[
                "chat_message",
                f"sentiment:{sentiment_label}",
                f"risk:{risk}"
            ]
        )

        # ------------------------------------------------------------
        # 2. Technique selection + crisis note
        # ------------------------------------------------------------
        strategy = pick_therapy_strategy(sentiment_label, risk, user_message)
        strategy_prompt = THERAPY_TECHNIQUES[strategy]
        crisis_note = crisis_check(user_message, risk)

        # ------------------------------------------------------------
        # 3. Build instructions (NO SYSTEM ROLE)
        # ------------------------------------------------------------
        instructions = f"""
You are Journie — an emotional well-being companion.

Rules:
- Be warm, validating, supportive.
- Do NOT diagnose or use clinical terms.
- Keep responses short but meaningful.
- Use the selected psychological technique.
- Encourage grounding or small steps.
- Use the crisis note if needed.

SELECTED TECHNIQUE:
{strategy_prompt}

CRISIS NOTE:
{crisis_note}
"""

        messages = [
            to_msg("assistant", "INSTRUCTIONS:\n" + instructions)
        ]

        # ------------------------------------------------------------
        # 4. Add memory context
        # ------------------------------------------------------------
        for m in context_list:
            messages.append(to_msg(m["role"], m["content"]))

        # ------------------------------------------------------------
        # 5. Add user message
        # ------------------------------------------------------------
        messages.append(to_msg("user", user_message))

        # ------------------------------------------------------------
        # 6. Gemini API Call
        # ------------------------------------------------------------
        response = model.generate_content(
            messages,
            generation_config={"temperature": 0.55}
        )

        reply_text = response.text.strip()

        # Save assistant reply to memory
        self.memory.add_memory(
            user_id=user_id,
            role="assistant",
            content=reply_text,
            tags=[f"strategy:{strategy}", "assistant_response"]
        )

        # ------------------------------------------------------------
        # Structured API response
        # ------------------------------------------------------------
        return {
            "response": reply_text,
            "sentiment": sentiment_label,
            "sentiment_score": sentiment_obj["score"],
            "risk": risk
        }


# Singleton instance
journie_agent = JournieAgent()
