from .gemini_client import detect_ai_text
from .serverless import build_handler


def _process(payload):
    text = (payload.get("text") or "").strip()
    return detect_ai_text(text)


handler = build_handler(_process)

