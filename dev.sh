#!/bin/bash
# Run Sudo locally using uv (with screen support).
#
# Real API:
#   ANTHROPIC_API_KEY=your-key ./dev.sh
#
# Mock server (no API key needed):
#   Terminal 1: uv run python tests/mock_anthropic_server.py
#   Terminal 2: ANTHROPIC_API_KEY=test-key ANTHROPIC_BASE_URL=http://localhost:8765 ./dev.sh
#
# Test expression loop quickly (fires every 5s instead of 30s):
#   ANTHROPIC_API_KEY=test-key ANTHROPIC_BASE_URL=http://localhost:8765 EXPRESSION_INTERVAL_SECONDS=5 ./dev.sh
#
# Environment variables:
#   ANTHROPIC_API_KEY              — required
#   ANTHROPIC_BASE_URL             — optional, override API endpoint (e.g. mock server)
#   EXPRESSION_INTERVAL_SECONDS    — optional, override expression loop interval (default 30)
set -e

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

PYTHONPATH=src uv run python src/chat.py
