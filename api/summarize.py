from .gemini_client import summarize_text
from .serverless import build_handler


def _process(payload):
    text = (payload.get("text") or "").strip()
    try:
        ratio = float(payload.get("ratio", 0.3))
    except (TypeError, ValueError):
        raise ValueError("ratio must be a number.")

    fmt = (payload.get("format") or "paragraph").strip().lower()

    return summarize_text(text, ratio, fmt)


handler = build_handler(_process)

