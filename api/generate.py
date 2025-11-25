from .gemini_client import GenerateParams, generate_completion
from .serverless import build_handler


def _process(payload):
    prompt = (payload.get("prompt") or "").strip()
    tone = (payload.get("tone") or "neutral").strip().lower()

    try:
        max_length = int(payload.get("maxLength", 250))
    except (TypeError, ValueError):
        raise ValueError("maxLength must be a number.")

    try:
        temperature = float(payload.get("temperature", 0.8))
    except (TypeError, ValueError):
        raise ValueError("temperature must be a number.")

    params = GenerateParams(
        prompt=prompt,
        tone=tone or "neutral",
        max_length=max(50, min(1000, max_length)),
        temperature=max(0.0, min(1.0, temperature)),
    )

    return generate_completion(params)


handler = build_handler(_process)

