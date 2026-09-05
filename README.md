# Multilingual E-Consultation Emotion Analysis

A full-stack dashboard for analyzing public consultation comments across Indian languages. The application detects the input language, predicts the comment's dominant emotion, and presents confidence and probability details for review.

## Features

- Automatic language detection for Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, and English
- Five-class emotion classification: `angry`, `happy`, `sad`, `fear`, and `neutral`
- Confidence score and per-emotion probability breakdown
- Bulk analysis for multiple comments, one comment per line
- Session history and emotion-distribution charts in the dashboard
- Inline translation through the backend proxy
- Local inference using the trained model in `models/final`

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, Vite, Recharts |
| Backend | FastAPI, Uvicorn, Pydantic |
| Model | Fine-tuned `ai4bharat/indic-bert` with Transformers and PyTorch |
| Language detection | Unicode script detection and `langdetect` |
| Translation | Google Translate endpoint with MyMemory fallback |

## Requirements

- Python 3.10 or newer
- Node.js 18 or newer and npm
- Approximately 1.5 GB of available RAM for loading the model
- The tracked model files in `models/final`

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/Avneesh02/Multi-lingual-sentiment-analysis.git
cd Multi-lingual-sentiment-analysis
```

### Backend

Create and activate a virtual environment, then install the Python dependencies:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

```bash
python -m pip install -r backend/requirements.txt
```

Start the API from the `backend` directory:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

### Frontend

Open a second terminal at the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

The frontend uses `http://localhost:8000` by default. To point it at another backend, update `API_BASE_URL` in `frontend/src/config.js`.

## API

### Health check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "model_loaded": true
}
```

### Predict emotion

```http
POST /emotion/predict
Content-Type: application/json
```

Request:

```json
{
  "text": "The service has improved a lot."
}
```

Response:

```json
{
  "emotion": "happy",
  "confidence": 0.9809,
  "language": {
    "code": "en",
    "name": "English"
  },
  "probabilities": {
    "angry": 0.0041,
    "happy": 0.9809,
    "sad": 0.0032,
    "fear": 0.0028,
    "neutral": 0.0089
  }
}
```

### Translate text

```http
GET /translate?text=Hello&tl=hi
```

The backend detects the source language and returns the translated text. Translation depends on the external Google Translate or MyMemory service being reachable.

## Project Structure

```text
.
├── backend/
│   ├── main.py              FastAPI application and translation proxy
│   ├── emotion.py           Emotion prediction endpoint and schemas
│   ├── predictor.py         Model loading, language detection, inference
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx          Dashboard shell
│   │   └── components/      Dashboard panels and charts
│   ├── package.json
│   └── vite.config.js
├── models/
│   └── final/               Trained model, tokenizer, and label encoder
├── data/                    Source, standardized, and split datasets
├── scripts/                 Data preparation and training scripts
└── README.md
```

## Model Details

- Architecture: `AlbertForSequenceClassification`
- Base model: `ai4bharat/indic-bert`
- Classes: 5 emotions
- Reported overall accuracy: 63.74%
- Reported best language results: Hindi 78.4%, Tamil 76.4%

The model is loaded locally by the backend with `local_files_only=True`; no model download is required at startup when `models/final` is present.

## Development Commands

From `frontend/`:

```bash
npm run dev       # Start the development server
npm run build     # Create a production build
npm run preview   # Preview the production build
```

From the repository root, the backend can be started with:

```bash
uvicorn backend.main:app --reload --port 8000
```

If that import form is not supported by the local environment, run Uvicorn from inside `backend/` as shown in the installation section.

## Limitations

- Predictions are model outputs and should be reviewed before being used for policy or operational decisions.
- Language detection is script-based for most languages and may be uncertain for short or mixed-script text.
- Translation uses public external endpoints and may be rate-limited or temporarily unavailable.
- The included model is intended for this project and has not been presented as a production-safe or bias-free classifier.

## License

No license has been specified for this repository yet. Add a license before distributing or reusing the project publicly.
