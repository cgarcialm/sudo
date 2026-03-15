"""
Minimal HTTP server that mimics the Anthropic Messages API.
Used for local testing and Docker integration tests — no real API calls made.

Usage:
    python tests/mock_anthropic_server.py [port]

Then run the chat pointing at it:
    ANTHROPIC_API_KEY=test-key ANTHROPIC_BASE_URL=http://localhost:8765 \\
        PYTHONPATH=src python src/chat.py
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

_MOCK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="320">'
    '<rect width="320" height="320" fill="#1a1a2e"/>'
    '<circle cx="160" cy="160" r="80" fill="#e94560" opacity="0.8"/>'
    '<circle cx="160" cy="160" r="40" fill="#0f3460"/>'
    "</svg>"
)
_MOCK_REPLY = f"Hello from mock!\n<screen>{_MOCK_SVG}</screen>"


def _sse_event(event_type, data):
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode()


def _streaming_body(reply_text):
    chunks = [
        _sse_event(
            "message_start",
            {
                "type": "message_start",
                "message": {
                    "id": "msg_mock",
                    "type": "message",
                    "role": "assistant",
                    "content": [],
                    "model": "claude-sonnet-4-6",
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 10, "output_tokens": 0},
                },
            },
        ),
        _sse_event(
            "content_block_start",
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        ),
        _sse_event(
            "content_block_delta",
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": reply_text},
            },
        ),
        _sse_event("content_block_stop", {"type": "content_block_stop", "index": 0}),
        _sse_event(
            "message_delta",
            {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": 20},
            },
        ),
        _sse_event("message_stop", {"type": "message_stop"}),
    ]
    return b"".join(chunks)


class MockAnthropicHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        streaming = body.get("stream", False)

        if streaming:
            payload = _streaming_body(_MOCK_REPLY)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            response = {
                "id": "msg_mock123",
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": _MOCK_REPLY}],
                "model": "claude-sonnet-4-6",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 8},
            }
            payload = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def log_message(self, format, *args):
        pass  # suppress request logs


def run(port=8765):
    server = HTTPServer(("0.0.0.0", port), MockAnthropicHandler)
    print(f"Mock Anthropic server running on port {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run(port)
