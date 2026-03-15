#!/bin/bash
# Run Sudo. Any extra arguments are passed through to docker run.
# Usage: ./run.sh [extra docker run args...]
#
# Environment variables:
#   ANTHROPIC_API_KEY  — required, your Anthropic API key
#   MEMORY_DIR         — directory to mount as /app/memory (default: ./memory)
set -e

TTY_FLAGS=""
if [ -t 0 ]; then
    TTY_FLAGS="-t"
fi

MEMORY_DIR="${MEMORY_DIR:-$(pwd)/memory}"

docker run --rm -i $TTY_FLAGS \
    -e "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" \
    -v "${MEMORY_DIR}:/app/memory" \
    "$@" \
    sudo
