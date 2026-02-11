# MyJournie — An AI Agent for Emotional Well‑Being

MyJournie is an AI‑powered emotional wellness companion that blends mindful journaling with intelligent, psychologically inspired support. It was created as part of the Kaggle × Google AI Agents Intensive Capstone Project under the “Agents for Good” track, focusing on mental health, emotional awareness, and supportive interventions.

## Overview

Many people, especially teenagers and young adults, turn to AI chatbots when they feel anxious or overwhelmed. While AI can feel safe and non‑judgmental, most chat systems cannot identify signs of distress, track emotional patterns, or respond with consistent empathy. MyJournie aims to bridge this gap.

It combines journaling, emotional signal detection, memory, and agentic reasoning to create a supportive AI experience that encourages reflection and well‑being.

## Key Features

### AI‑Powered Therapeutic Agent
The main agent uses the Gemini ADK to:
- Understand emotional tone
- Maintain context across sessions
- Trigger custom tools
- Use gentle CBT/REBT‑inspired support techniques
- Encourage reflective conversation rather than advice or diagnosis

### Journaling and Emotional Tracking
Users can write daily entries that:
- Are analyzed for sentiment
- Receive a risk score
- Are stored locally for the prototype
- Contribute to long‑term emotional trend tracking

### Safety‑Oriented Tooling
Tools include:
- analyze_sentiment
- calculate_risk_score
- store_journal
- fetch_memory
- save_memory

These demonstrate agent tool‑use, a core requirement for the Capstone.

### Memory System
MyJournie maintains:
- Short‑term conversational memory
- Long‑term journal history
- Extracted emotional trends over time

### System Architecture
- FastAPI backend
- Gemini ADK agent runtime
- Sentiment, risk, and memory tools
- Local JSON‑based storage
- Planned Flutter UI

## Running the Project (Backend Prototype)

1. Clone the repository
2. Create a virtual environment
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Start the backend server:
   ```
   uvicorn src.backend.app:app --reload
   ```

## Future Roadmap

If further time were available, enhancements would include:
- A complete Flutter interface with a calming therapeutic design
- Voice‑based journaling
- Finer‑grained emotional classification
- Embedding‑based retrieval for long‑term memory
- Secure cloud database
- Guardian dashboard for weekly emotional trends
- Guided journaling, reminders, and nudges
- Behavioral activation tools (e.g., task scheduling)

## License
This project is developed for educational and research purposes as part of the Kaggle × Google Agents Intensive.

## Acknowledgements
Grateful to the Kaggle and Google AI teams for enabling hands‑on agent development with Gemini and the ADK.
