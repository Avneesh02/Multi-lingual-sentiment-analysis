# Sentiment Analysis E-Consultation Module

A multilingual emotion classification system for analyzing public comments submitted through government e-consultation portals. Built as a Final Year Project.

---

## What it does

- Accepts a comment in **9 Indian languages + English**
- Detects the **language automatically**
- Classifies the **emotion**: `angry` · `neutral` · `happy` · `sad` · `fear`
- Shows **confidence score** and probability breakdown
- Supports **inline translation** between all 9 languages (no redirect)

**Supported Languages:** Hindi · Marathi · Bengali · Tamil · Telugu · Kannada · Malayalam · Gujarati · English

---

## Tech Stack

| Part | Technology |
|---|---|
| ML Model | `ai4bharat/indic-bert` (ALBERT, fine-tuned) |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + Vite + Recharts |
| Translation | Google Translate proxy (via backend) |

---

## Project Structure

```
project/
├── models/final/        ← Trained model weights (read-only)
├── backend/             ← FastAPI server
│   ├── main.py
│   ├── emotion.py
│   ├── predictor.py
│   └── requirements.txt
└── frontend/            ← React dashboard
    └── src/
```

---

## How to Run Locally

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Wait for: `Application startup complete.`

### 2. Frontend

Open a **second terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

> If port 5173 is taken, Vite will use 5174. Check the terminal output.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check if model is loaded |
| `POST` | `/emotion/predict` | Classify emotion in text |
| `GET` | `/translate` | Translate text (no API key needed) |

### Example Request

```bash
curl -X POST http://localhost:8000/emotion/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "रक्षाबंधन की शुभकामनाएँ"}'
```

### Example Response

```json
{
  "emotion": "happy",
  "confidence": 0.9809,
  "language": { "code": "hi", "name": "Hindi" },
  "probabilities": {
    "angry": 0.0451, "neutral": 0.0185,
    "happy": 0.9809, "sad": 0.0370, "fear": 0.0104
  }
}
```

---

## Model Info

- **Architecture:** `AlbertForSequenceClassification`
- **Base:** `ai4bharat/indic-bert`
- **Classes:** 5 (angry, neutral, happy, sad, fear)
- **Overall Accuracy:** 63.74%
- **Best Language:** Hindi (78.4%), Tamil (76.4%)

---

## Requirements

- Python 3.10+
- Node.js 18+
- ~1.5 GB RAM (for PyTorch model)

---

## Note

The `models/`, `data/`, and `scripts/` folders are **read-only** — they contain the trained weights and original dataset. Do not modify them.
