"""
emotion.py
----------
APIRouter that exposes  POST /emotion/predict.

Request  : {"text": str}
Response : predictor.predict() result dict
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

import predictor

router = APIRouter(prefix="/emotion", tags=["emotion"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be blank or whitespace-only.")
        return v


class LanguageInfo(BaseModel):
    code: str
    name: str


class PredictResponse(BaseModel):
    emotion: str
    confidence: float
    language: LanguageInfo
    probabilities: dict[str, float]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("/predict", response_model=PredictResponse)
async def predict_emotion(body: PredictRequest):
    """
    Classify the emotion of a text comment.

    - **422** – empty / whitespace-only text, or text with no letters/digits.
    - **500** – unexpected internal error (stack trace is not leaked).
    """
    try:
        result = predictor.predict(body.text)
        return result
    except ValueError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please try again."},
        )
