#!/bin/bash
# Run Sudo locally using uv (with screen support).
# Usage: ./dev.sh
#
# Environment variables:
#   ANTHROPIC_API_KEY  — required (or set ANTHROPIC_BASE_URL for mock server)
#   ANTHROPIC_BASE_URL — optional, override API endpoint (e.g. mock server)
set -e

PYTHONPATH=src uv run python src/chat.py
