#!/bin/bash
# Run Sudo locally against the mock server (no real API calls).
#
# Usage:
#   Terminal 1: uv run python tests/mock_anthropic_server.py
#   Terminal 2: ./dev.sh
#
# Uses ANTHROPIC_API_KEY from .env if present, otherwise falls back to "test-key".
# Always overrides ANTHROPIC_BASE_URL and EXPRESSION_INTERVAL_SECONDS for mock mode.
set -e

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Always use mock server and short expression interval in dev mode
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-test-key}"
export ANTHROPIC_BASE_URL="http://localhost:8765"
export EXPRESSION_INTERVAL_SECONDS=5

PYTHONPATH=src uv run python src/chat.py
