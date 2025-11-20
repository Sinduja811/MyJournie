# MyJournie – AI-Enabled Interactive Journal with Psychological Guidance

**MyJournie** is an intelligent journaling and mental well-being platform designed to help users reflect, record emotions, and gain AI-driven psychological insights.  
It combines natural language processing, behavioral cues, and mental health frameworks to detect negative thought patterns and guide users toward emotional balance and constructive thinking.

---

## Project Overview

MyJournie acts as an AI-assisted digital companion that encourages self-reflection and mindfulness.  
By analyzing journal entries in real time, the system detects early signs of stress, anxiety, or negativity and provides tailored psychological guidance.  
It blends artificial intelligence with principles of cognitive behavioral therapy (CBT) to make journaling more interactive and emotionally supportive.

---

## Key Features

### AI and Psychological Insights
- Emotion and sentiment analysis on journal entries.  
- AI-based detection of negative or harmful thought patterns.  
- Personalized feedback and guidance aligned with CBT principles.  
- Contextual journaling prompts for deeper reflection.  
- Alerts for recurring negative emotion trends.

### Journaling and Planner
- Structured daily journal with guided sections.  
- Habit and mood tracking over time.  
- Integration with personal or school/work schedules.  
- Goal planner with visual progress insights.

### Insights Dashboard
- Weekly and monthly emotion summaries.  
- AI-generated wellness trends and visualization.  
- Comparison of mood vs. productivity patterns.

### Future Scope
- Optional counselor or parental dashboard for guided review.  
- Speech-to-text journaling with tone detection.  
- Secure offline journaling with local inference.  

---

## Technical Architecture

**Frontend:** React Native (Expo)  
**Backend:** FastAPI (Python)  
**Database:** PostgreSQL / SQLite  
**AI Engine:** NLP microservice with PyTorch and transformer-based models  

---

## Technology Stack

### Frontend
- React Native 0.74+  
- Expo SDK 51+  
- React Navigation, Redux Toolkit  
- Victory Charts or Recharts for data visualization  

### Backend
- FastAPI 0.115+  
- SQLAlchemy ORM  
- JWT-based authentication  
- Uvicorn ASGI server  

### AI Layer
- Transformers (Hugging Face)  
- PyTorch or TensorFlow  
- scikit-learn, spaCy, NLTK  
- Custom trained model for emotion and cognition detection  

---

## AI Functional Flow

1. **Input Processing:** Text entries are securely passed to the AI microservice.  
2. **Preprocessing:** Tokenization, lemmatization, and normalization.  
3. **Emotion Detection:** Transformer-based model identifies dominant emotion(s).  
4. **Cognitive Pattern Analysis:** Recognizes negative or repetitive thought patterns.  
5. **Guidance Generation:** AI produces reflective prompts and CBT-based suggestions.  
6. **User Feedback:** Model adapts insights over time using reinforcement feedback.

---

## Setup Instructions

### Backend
```bash
cd src/backend
python -m venv venv
venv\Scripts\activate  # for Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### AI Microservice
```bash
cd src/ai_service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python ai_server.py
```

### Frontend
```bash
cd src/frontend
npm install --legacy-peer-deps
npx expo start
```

---

## Future Enhancements

- Integration of multimodal inputs (voice, text, and image-based journaling).  
- Continuous mood prediction using LSTM or transformer hybrid models.  
- Smart chatbot layer for cognitive dialogue.  
- Expanded counselor dashboard with anonymized trend analytics.  
- AI ethics and explainability module for transparency of insights.  

---

## Author

**Developed by:** Sinduja S  
**Focus Areas:** AI for Psychology, NLP Applications, Mental Health Technology   

---

## Version & License

Version: 1.0.0  
© 2025 Sinduja S. All rights reserved.
