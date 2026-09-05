# Sentiment Analysis E-Consultation Module
### Final Year Project — Simple Documentation Guide

---

## What is this project?

This project is a **web-based system** that reads public comments written in Indian languages and tells us **how people are feeling** — whether they are happy, angry, sad, scared, or neutral.

Think of it like this:
> "Someone posts a comment in Hindi, Marathi, or Tamil on a government portal. Our system automatically reads it and says — this person is **angry** with **89% confidence**."

---

## Why was this built?

Government e-consultation portals receive thousands of comments from citizens. Reading each one manually is impossible. This system:

- Automatically detects **which language** the comment is in
- Classifies the **emotion** of the comment
- Shows results on a **live dashboard**
- Supports **bulk analysis** for many comments at once

---

## Supported Languages (9 Indian Languages + English)

| Language | Script |
|---|---|
| Hindi | हिंदी |
| Marathi | मराठी |
| Bengali | বাংলা |
| Tamil | தமிழ் |
| Telugu | తెలుగు |
| Kannada | ಕನ್ನಡ |
| Malayalam | മലയാളം |
| Gujarati | ગુજરાતી |
| English | Latin |

---

## 5 Emotion Categories

| Emotion | Meaning |
|---|---|
| 😠 Angry | Person is frustrated or outraged |
| 😊 Happy | Person is satisfied or celebrating |
| 😢 Sad | Person is disappointed or grieving |
| 😨 Fear | Person is worried or anxious |
| 😐 Neutral | Factual comment, no clear feeling |

---

## How the System Works (Simple Flow)

```
User types a comment
        ↓
System detects the language automatically
        ↓
AI Model reads the comment
        ↓
Gives back: Emotion + Confidence % + Probability of all 5 emotions
        ↓
Dashboard shows the result with charts
```

---

## Three Main Parts

### 1. The AI Model (Brain)
- Uses a pre-trained model called **indic-bert** made by AI4Bharat (IIT Madras)
- Fine-tuned (trained further) on real Indian social media comments
- Understands all 9 languages with **one single model** — not 9 separate models
- Overall accuracy: **63.74%**
- Best performance: Hindi (78.4%), Tamil (76.4%)

### 2. The Backend (Server)
- Built with **FastAPI** (Python)
- Receives the comment from the website
- Runs it through the AI model
- Sends back the result
- Also has a **Translation feature** — translates comments between languages

**Three API endpoints:**
| Endpoint | What it does |
|---|---|
| `GET /health` | Checks if the server is running |
| `POST /emotion/predict` | Analyzes the emotion of a comment |
| `GET /translate` | Translates text to any of the 9 languages |

### 3. The Frontend (Website/Dashboard)
- Built with **React** (JavaScript)
- Clean government-style design (navy blue + saffron theme)
- Shows: emotion result, confidence bar, probability chart, session history
- Has **glass effect cards** and smooth animations
- Works in the browser — no installation needed for users

---

## Key Features

### ✅ Single Comment Analysis
Type or paste one comment → click **Analyze Emotion** → see result instantly

### ✅ Inline Translation
- Select a target language from dropdown (e.g. Gujarati)
- Click **Translate Via Google Translate**
- Translation appears on the same page — no redirect
- You can then analyze the translated text

### ✅ Bulk Comment Analysis
- Paste 10, 20, 50 comments (one per line)
- Click **Analyze All Comments**
- See a bar chart: how many are happy, angry, sad, etc.
- Shows: *"Overall Sentiment: Most comments express 😊 Happy (62% of 15 comments)"*

### ✅ Session History
- Every prediction you make in the session is saved in a list
- Shows: emotion, language, confidence, time

### ✅ Live Emotion Donut Chart
- Updates automatically after each prediction
- Shows the emotion distribution of the current session

---

## Language Detection (How it finds the language)

The system uses a **2-step method** — no separate ML model needed:

**Step 1:** Count which Unicode script has the most characters
- Devanagari → Hindi or Marathi
- Bengali script → Bengali
- Tamil script → Tamil
- And so on...

**Step 2:** For Hindi vs Marathi (both use Devanagari)
- Use Google's `langdetect` library to distinguish them

This is fast (< 1ms) and works for all 9 languages.

---

## Technology Used

| Part | Tool | Purpose |
|---|---|---|
| AI Model | indic-bert (ALBERT) | Understand Indian languages |
| Backend | FastAPI + Python | Handle API requests |
| Server | Uvicorn | Run the backend |
| Frontend | React + Vite | Build the dashboard |
| Charts | Recharts | Draw graphs |
| Translation | Google GTX API | Translate text |
| Fonts | Google Fonts | Inter + Merriweather |

---

## How to Run the Project

**Terminal 1 — Start the Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 — Start the Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Then open:** `http://localhost:5173` in your browser

> First startup takes ~15 seconds (AI model loading into memory)

---

## Model Performance

| Language | Accuracy |
|---|---|
| Hindi | 78.4% |
| Tamil | 76.4% |
| Telugu | 72.2% |
| Bengali | 69.6% |
| Kannada | 68.4% |
| Marathi | 64.4% |
| Malayalam | 56.5% |
| English | 52.5% |
| Gujarati | 47.0% |
| **Overall** | **63.74%** |

> Gujarati has lower accuracy due to fewer training samples (only 100 test samples).

---

## What Makes This Project Unique

1. **One model for 9 languages** — most systems use separate models per language
2. **No login required** — open the site and start using immediately
3. **Inline translation** — no redirect to another website
4. **Bulk analysis with graph** — analyze many comments at once
5. **Real dataset** — trained on actual Indian social media comments, not synthetic data
6. **Glassmorphism UI** — modern, professional design

---

## Limitations

- Gujarati and English accuracy is lower (less training data)
- Romanized text (e.g. "mujhe gussa aata hai" in English letters) may be misdetected as English
- Session history is lost on page refresh (no database)
- Requires internet for translation feature

---

## Future Improvements

1. Add more training data for Gujarati and English
2. Support Romanized (transliterated) text detection
3. Save history to a database
4. Deploy on cloud (Render + Vercel)
5. Add a PDF/CSV export for bulk analysis results
6. Support more regional languages (Punjabi, Odia, etc.)
