from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .gemini_client import GenerateParams, detect_ai_text, generate_completion, summarize_text

app = FastAPI(title="Lexiflow Gemini API", version="1.0.0")


class GenerateBody(BaseModel):
    prompt: str = Field(..., min_length=10)
    tone: str | None = "neutral"
    maxLength: int | None = Field(default=250, ge=50, le=1000)
    temperature: float | None = Field(default=0.8, ge=0, le=1)


class SummarizeBody(BaseModel):
    text: str = Field(..., min_length=50)
    ratio: float | None = Field(default=0.3, ge=0.1, le=0.9)
    format: str | None = "paragraph"


class DetectBody(BaseModel):
    text: str = Field(..., min_length=50)


@app.post("/generate")
def generate_text(body: GenerateBody):
    params = GenerateParams(
        prompt=body.prompt,
        tone=(body.tone or "neutral").lower(),
        max_length=body.maxLength or 250,
        temperature=body.temperature or 0.8,
    )
    try:
        return generate_completion(params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/summarize")
def summarize(body: SummarizeBody):
    try:
        return summarize_text(body.text, body.ratio or 0.3, (body.format or "paragraph").lower())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/detect")
def detect(body: DetectBody):
    try:
        return detect_ai_text(body.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

