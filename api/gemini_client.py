import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict

from google import generativeai as genai

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

api_key = os.getenv("AIzaSyAZuEShA5Go2EIAQN2_4V8lf8t6waJPEKs")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Define it in your environment or Vercel project settings."
    )

genai.configure(api_key=api_key)


@dataclass
class GenerateParams:
    prompt: str
    tone: str = "neutral"
    max_length: int = 250
    temperature: float = 0.8


def _make_model(model_name: str | None = None):
    return genai.GenerativeModel(model_name or DEFAULT_MODEL)


def generate_completion(params: GenerateParams) -> Dict[str, Any]:
    if not params.prompt.strip():
        raise ValueError("Prompt is required.")

    tone_instruction = (
        f"Write with a {params.tone} tone." if params.tone and params.tone != "default" else ""
    )

    directive = (
        "You are an expert copywriter. Craft a clear, engaging response that aligns with the details below."
    )

    constrained_prompt = (
        f"{directive}\n"
        f"{tone_instruction}\n"
        f"Cap the output at roughly {params.max_length} words.\n"
        f"Prompt:\n{params.prompt.strip()}"
    )

    generation_config = {
        "temperature": max(0.0, min(1.0, params.temperature)),
        "top_p": 0.95,
        "max_output_tokens": min(params.max_length * 4, 2048),
    }

    response = _make_model().generate_content(
        constrained_prompt,
        generation_config=generation_config,
    )

    text = (response.text or "").strip()
    usage = getattr(response, "usage_metadata", None)
    token_count = getattr(usage, "total_token_count", None)

    words = len(re.findall(r"\w+", text))

    return {
        "generatedText": text,
        "wordCount": words,
        "tokensUsed": token_count or "unknown",
    }


def summarize_text(text: str, ratio: float, fmt: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Text is required.")

    ratio = ratio or 0.3
    ratio = max(0.1, min(0.9, ratio))

    format_hint = {
        "paragraph": "Write in 1-2 cohesive paragraphs.",
        "bullets": "Return a concise bulleted list.",
        "key_points": "List 3-5 key insights.",
    }.get(fmt, "Write in paragraphs.")

    prompt = (
        "You are an expert technical editor. Summarize the user's text.\n"
        f"{format_hint}\n"
        f"Target a compression ratio of about {int(ratio * 100)}% of the original length.\n"
        "Avoid introducing new facts.\n"
        "Text to summarize:\n"
        f"{cleaned}"
    )

    response = _make_model().generate_content(
        prompt,
        generation_config={
            "temperature": 0.4,
            "top_p": 0.9,
            "max_output_tokens": 1024,
        },
    )

    summary = (response.text or "").strip()

    original_words = len(re.findall(r"\w+", cleaned))
    summary_words = len(re.findall(r"\w+", summary))
    compression_ratio = (
        f"{(summary_words / original_words * 100):.1f}%"
        if original_words
        else "N/A"
    )

    return {
        "summary": summary,
        "originalWords": original_words,
        "summaryWords": summary_words,
        "compressionRatio": compression_ratio,
    }


def detect_ai_text(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Text is required.")

    prompt = (
        "You are an AI writing detector. Evaluate the text and respond ONLY with valid JSON that matches "
        "this schema:\n"
        "{\n"
        '  "ai_probability": number (0-100),\n'
        '  "confidence": "short sentence explaining confidence",\n'
        '  "indicators": ["bullet", "..."],\n'
        '  "style_analysis": "paragraph analysis"\n'
        "}\n"
        "Do not wrap the JSON in markdown code fences.\n"
        f"Text:\n{cleaned}"
    )

    response = _make_model().generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "top_p": 0.9,
            "max_output_tokens": 768,
        },
    )

    analysis = (response.text or "").strip()
    parsed = _extract_first_json_object(analysis)

    ai_prob = float(parsed.get("ai_probability", 50))
    ai_prob = max(0.0, min(100.0, ai_prob))

    return {
        "isAI": ai_prob >= 60,
        "aiProbability": round(ai_prob, 1),
        "confidence": parsed.get("confidence", "Unknown"),
        "indicators": parsed.get("indicators") or [],
        "styleAnalysis": parsed.get("style_analysis", ""),
    }


def _extract_first_json_object(raw: str) -> Dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}

