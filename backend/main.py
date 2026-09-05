"""
main.py
-------
FastAPI application entry point.

Run from the backend/ directory:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import urllib.request, urllib.parse, json as _json
import httpx

import predictor          # triggers singleton load at startup
from emotion import router as emotion_router

app = FastAPI(
    title="e-Consultation Sentiment Analysis API",
    description=(
        "Multilingual emotion classification (angry, neutral, happy, sad, fear) "
        "over 9 Indian languages + English, powered by ai4bharat/indic-bert."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(emotion_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["meta"])
async def health():
    """Returns ok once the model singleton is loaded."""
    return {"status": "ok", "model_loaded": predictor.MODEL_LOADED}


# ---------------------------------------------------------------------------
# Inline translation proxy — uses free Google Translate endpoint
# No API key required. Backend proxies to avoid browser CORS restrictions.
# ---------------------------------------------------------------------------
@app.get("/translate", tags=["meta"])
async def translate(
    text: str = Query(..., max_length=1000),
    tl:   str = Query(default="en"),
):
    """Translate using Google GTX (via httpx). Falls back to MyMemory on rate-limit."""
    t = text.strip()
    lang_info = predictor.detect_language(t)
    sl = lang_info.get("code", "en")
    if sl == "unknown":
        sl = "en"

    gtx_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://translate.google.com/",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # --- Primary: Google GTX (accurate, free, no key) ---
    try:
        params = {"client": "gtx", "sl": sl, "tl": tl, "dt": "t", "q": t}
        with httpx.Client(timeout=10) as client:
            r = client.get("https://translate.googleapis.com/translate_a/single",
                           params=params, headers=gtx_headers)
        if r.status_code == 200:
            data = r.json()
            translated = "".join(seg[0] for seg in data[0] if seg[0])
            if translated:
                return {"translated": translated}
    except Exception:
        pass

    # --- Fallback: MyMemory ---
    try:
        params2 = urllib.parse.urlencode({"q": t, "langpair": f"{sl}|{tl}"})
        req2 = urllib.request.Request(
            f"https://api.mymemory.translated.net/get?{params2}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req2, timeout=10) as r2:
            data2 = _json.loads(r2.read().decode("utf-8"))
        translated = data2.get("responseData", {}).get("translatedText", "")
        if translated:
            return {"translated": translated}
    except Exception:
        pass

    return JSONResponse(status_code=502, content={"detail": "Translation service unavailable."})





