from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return
    
    def do_POST(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                import google.generativeai as genai
            except ImportError as e:
                self.wfile.write(json.dumps({
                    "error": f"Import error: {str(e)}",
                    "isAI": False,
                    "confidence": 50,
                    "perplexity": 0,
                    "burstiness": 0
                }).encode())
                return
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                self.wfile.write(json.dumps({
                    "error": "API key not set",
                    "isAI": False,
                    "confidence": 50,
                    "perplexity": 0,
                    "burstiness": 0
                }).encode())
                return
            
            genai.configure(api_key=api_key)
            
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            text = data.get('text', '').strip()
            if len(text) < 50:
                self.wfile.write(json.dumps({
                    "error": "Text too short",
                    "isAI": False,
                    "confidence": 50,
                    "perplexity": 0,
                    "burstiness": 0
                }).encode())
                return
            
            model = genai.GenerativeModel('gemini-pro')
            prompt = f'Is this AI or human? Respond JSON only: {{"isAI": true, "confidence": 85, "reasoning": "why"}}\n\nText: "{text}"'
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            if '```' in result_text:
                result_text = result_text.split('```')[1].replace('json', '').strip()
            
            result = json.loads(result_text)
            result['perplexity'] = 0
            result['burstiness'] = 0
            
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.wfile.write(json.dumps({
                "error": str(e),
                "isAI": False,
                "confidence": 50,
                "perplexity": 0,
                "burstiness": 0
            }).encode())