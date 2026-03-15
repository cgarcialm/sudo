# Handoff — Phase 1 Foundation

## Goal
Set up a working Docker environment on Mac (ARM64) that connects to the Claude API, proving the foundation before the Pi arrives.

## What was tried
- Used `--env-file .env` to pass the API key to Docker
- Attempted to use the API key immediately after adding credits — failed due to a $0 monthly spend limit
- Tested via Workbench to isolate whether the account or the key was the issue
- Created a new API key after the original showed "Never used"

## What worked
- ARM64 Docker container builds and runs correctly on Mac
- Claude API responds successfully from inside the container
- New API key fixed the auth issue once the monthly spend limit was set to $5
- `main.py` refactored into a function with proper error handling and entry point

## What failed
- Original API key never worked (spend limit was $0, blocking all calls)
- `.claude/skills/` path for custom skills didn't work until Claude Code was restarted

## What's in place
- `Dockerfile` — ARM64/Linux container targeting Pi architecture
- `main.py` — `ask_claude(prompt)` function, standards-compliant
- `requirements.txt` — `anthropic`, `black`, `flake8`
- `pyproject.toml` — black + flake8 config
- `docs/PLAN.md` — 5-phase plan, Phase 1 marked complete (Pi deploy pending)
- `docs/ARCHITECTURE.md` — Mermaid diagrams per phase
- `docs/CODING_STANDARDS.md` — Python standards for the project
- `.claude/skills/test/` — `/test` skill: writes and runs pytest tests with mocked API
- `.claude/skills/review/` — `/review` skill: lints and checks standards
- `.claude/skills/implement/` — `/implement` skill: full propose → build → review → test → commit → PR → handoff loop

## Next steps
1. **Pi arrives** — clone repo, run same Docker setup, verify API call works on Pi
2. **Phase 2: Chat** — build FastAPI server with conversation history, browser UI at `http://sudo.local`
3. Use `/implement` to drive Phase 2 — it will read the plan, propose, and execute
