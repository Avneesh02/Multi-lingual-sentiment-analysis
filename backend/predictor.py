"""
predictor.py
------------
Loads the AlbertForSequenceClassification model and tokenizer ONCE at import
time and exposes three functions consumed by emotion.py:

  preprocess(text) -> str          - whitespace normalization + validation
  detect_language(text) -> dict    - lightweight Unicode-block + langdetect
  predict(text) -> dict            - full inference result
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MODEL_DIR = _PROJECT_ROOT / "models" / "final"
_LABEL_ENCODER_PATH = _MODEL_DIR / "label_encoder.json"

# ---------------------------------------------------------------------------
# Label maps — loaded from label_encoder.json, never hardcoded
# ---------------------------------------------------------------------------
with open(_LABEL_ENCODER_PATH, "r", encoding="utf-8") as _f:
    _label_data = json.load(_f)

_ID2LABEL: Dict[int, str] = {int(k): v for k, v in _label_data["id2label"].items()}
_LABEL2ID: Dict[str, int] = _label_data["label2id"]
_NUM_LABELS = len(_ID2LABEL)

# ---------------------------------------------------------------------------
# Model & tokenizer — singletons, loaded once
# ---------------------------------------------------------------------------
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_tokenizer = AutoTokenizer.from_pretrained(str(_MODEL_DIR), local_files_only=True)

_model = AutoModelForSequenceClassification.from_pretrained(
    str(_MODEL_DIR), local_files_only=True
)
_model.to(_device)
_model.eval()

MODEL_LOADED: bool = True  # exposed to main.py /health endpoint

# ---------------------------------------------------------------------------
# Language detection — Unicode block ranges
# ---------------------------------------------------------------------------
# Script Unicode ranges  (half-open: start <= cp < end)
_SCRIPT_RANGES = {
    "devanagari": (0x0900, 0x097F + 1),   # Hindi & Marathi share this
    "bengali":    (0x0980, 0x09FF + 1),
    "tamil":      (0x0B80, 0x0BFF + 1),
    "telugu":     (0x0C00, 0x0C7F + 1),
    "kannada":    (0x0C80, 0x0CFF + 1),
    "malayalam":  (0x0D00, 0x0D7F + 1),
    "gujarati":   (0x0A80, 0x0AFF + 1),
    # Latin covers ASCII a-z / A-Z (Basic Latin) → English
    "latin":      (0x0041, 0x007A + 1),
}

_SCRIPT_TO_LANG = {
    # devanagari handled separately (needs Hindi/Marathi disambiguation)
    "bengali":   {"code": "bn", "name": "Bengali"},
    "tamil":     {"code": "ta", "name": "Tamil"},
    "telugu":    {"code": "te", "name": "Telugu"},
    "kannada":   {"code": "kn", "name": "Kannada"},
    "malayalam": {"code": "ml", "name": "Malayalam"},
    "gujarati":  {"code": "gu", "name": "Gujarati"},
    "latin":     {"code": "en", "name": "English"},
}

_HINDI_MARATHI_LANGDETECT_MAP = {
    "hi": {"code": "hi", "name": "Hindi"},
    "mr": {"code": "mr", "name": "Marathi"},
}


def _dominant_script(text: str) -> str | None:
    """Return the name of the script that contributes the most characters."""
    counts: Dict[str, int] = {s: 0 for s in _SCRIPT_RANGES}
    for ch in text:
        cp = ord(ch)
        for script, (lo, hi) in _SCRIPT_RANGES.items():
            if lo <= cp < hi:
                counts[script] += 1
                break
    best_script = max(counts, key=lambda s: counts[s])
    return best_script if counts[best_script] > 0 else None


def detect_language(text: str) -> Dict[str, str]:
    """
    Detect the language of *text* from the 9 supported languages.

    Strategy:
    1. Count characters by Unicode block.
    2. Map dominant script → language.
    3. For Devanagari (Hindi/Marathi), use langdetect as a secondary check.
    4. If unknown script, return {"code": "unknown", "name": "Unknown"}.
    """
    script = _dominant_script(text)

    if script is None or script not in _SCRIPT_RANGES:
        return {"code": "unknown", "name": "Unknown"}

    if script == "devanagari":
        # Disambiguate Hindi vs Marathi
        try:
            from langdetect import detect as _ld_detect  # lazy import
            lang_code = _ld_detect(text)
            if lang_code in _HINDI_MARATHI_LANGDETECT_MAP:
                return _HINDI_MARATHI_LANGDETECT_MAP[lang_code]
        except Exception:
            pass
        # Default to Hindi if langdetect is inconclusive
        return {"code": "hi", "name": "Hindi"}

    return _SCRIPT_TO_LANG.get(script, {"code": "unknown", "name": "Unknown"})


# ---------------------------------------------------------------------------
# Text preprocessing — mirrors training-time cleaning exactly
# ---------------------------------------------------------------------------
def preprocess(text: str) -> str:
    """
    Collapse whitespace and strip.  Raises ValueError if cleaned text is
    empty or contains no letter/digit — matching training-time rejection.
    """
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned or not any(c.isalpha() or c.isdigit() for c in cleaned):
        raise ValueError(
            "Text must contain at least one letter or digit after whitespace normalization."
        )
    return cleaned


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def predict(text: str) -> Dict:
    """
    Full prediction pipeline.

    Returns
    -------
    {
        "emotion": str,
        "confidence": float,          # 0-1, 4 decimal places
        "language": {"code": str, "name": str},
        "probabilities": {label: float, ...}   # all 5 classes
    }
    """
    cleaned = preprocess(text)
    language = detect_language(cleaned)

    inputs = _tokenizer(
        cleaned,
        truncation=True,
        padding="max_length",
        max_length=128,
        return_tensors="pt",
    )
    inputs = {k: v.to(_device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = _model(**inputs)

    logits = outputs.logits  # shape: (1, num_labels)
    probs = torch.softmax(logits, dim=-1).squeeze(0)  # shape: (num_labels,)

    pred_id = int(torch.argmax(probs).item())
    emotion = _ID2LABEL[pred_id]
    confidence = round(float(probs[pred_id].item()), 4)

    probabilities = {
        _ID2LABEL[i]: round(float(probs[i].item()), 4)
        for i in range(_NUM_LABELS)
    }

    return {
        "emotion": emotion,
        "confidence": confidence,
        "language": language,
        "probabilities": probabilities,
    }
