import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)


def _write_json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    """Send a JSON response with common headers."""
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(json.dumps(payload).encode("utf-8"))


def _send_error(handler: BaseHTTPRequestHandler, status: HTTPStatus, message: str) -> None:
    _write_json_response(handler, status.value, {"error": message})


def build_handler(process_payload: Callable[[Dict[str, Any]], Dict[str, Any]]):
    """
    Create a serverless HTTP handler that parses JSON input, forwards it to `process_payload`
    and returns its JSON output. Exceptions that stem from bad requests should raise ValueError.
    """

    class Handler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):  # noqa: N802 (Vercel requires exact method names)
            """Support CORS pre-flight."""
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.end_headers()

        def do_POST(self):  # noqa: N802
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"

            try:
                payload = json.loads(raw_body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                _send_error(self, HTTPStatus.BAD_REQUEST, "Invalid JSON payload")
                return

            try:
                response_body = process_payload(payload)
            except ValueError as exc:
                _send_error(self, HTTPStatus.BAD_REQUEST, str(exc))
                return
            except Exception:  # pragma: no cover - defensive logging
                logger.exception("Unexpected error while processing payload")
                _send_error(self, HTTPStatus.INTERNAL_SERVER_ERROR, "Internal server error")
                return

            _write_json_response(self, HTTPStatus.OK.value, response_body)

    return Handler

