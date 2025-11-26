from google.generativeai import GenerativeModel, configure
import os

def handler(request):
    try:
        data = request.get_json()
        prompt = data.get("prompt", "").strip()

        if not prompt:
            return { "error": "Prompt is required" }, 400

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return { "error": "Missing GEMINI_API_KEY" }, 500

        configure(api_key=api_key)

        model = GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        text = response.text.strip()

        return {
            "generatedText": text,
            "wordCount": len(text.split())
        }, 200

    except Exception as e:
        return { "error": str(e) }, 500
