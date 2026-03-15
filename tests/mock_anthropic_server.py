"""
Minimal HTTP server that mimics the Anthropic Messages API.
Used for Docker integration tests in CI — no real API calls made.

Usage:
    python tests/mock_anthropic_server.py [port]
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class MockAnthropicHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response = {
            "id": "msg_mock123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello from mock!"}],
            "model": "claude-sonnet-4-6",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 8},
        }
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        pass  # suppress request logs


def run(port=8765):
    server = HTTPServer(("0.0.0.0", port), MockAnthropicHandler)
    print(f"Mock Anthropic server running on port {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run(port)
