#!/bin/bash
# Run Sudo directly on the Raspberry Pi (no Docker).
#
# Usage:
#   ./pi.sh
#
# Environment variables:
#   ANTHROPIC_API_KEY  — required, set in .env or export before running
#   GALLERY_ENABLED    — set to "true" to save SVGs to memory/gallery/
#   LOG_LEVEL          — set to "DEBUG" for verbose output (default: WARNING)
set -e

cd "$(dirname "$0")"

# Load .env if present
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY is not set."
    exit 1
fi

PYTHONPATH=src python src/main.py
