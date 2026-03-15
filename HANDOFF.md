# Handoff — Phase 2 Terminal Chat

## Goal
Build Phase 2: text-based conversation with Sudo via terminal with persistent session history.

## What was tried
- Originally proposed a web UI (FastAPI + HTML) — user preferred terminal
- Switched to a simple terminal REPL in `chat.py`

## What worked
- `chat.py` — interactive loop with `send_message()` passing full history each turn
- 5 tests in `tests/test_chat.py` covering reply, history mutation, multi-turn, system prompt, and API errors
- 2 Docker integration tests in `tests/test_docker.py` — single-turn and multi-turn inside ARM64 container with mock API
- Added `.flake8` config file — flake8 doesn't read `pyproject.toml`
- Sudo has its own evolving personality (not an assistant) — system prompt lets Claude define it
- Manual multi-turn test confirmed history works across turns in the same session

## What failed
- Original system prompt said "friendly assistant" — Claude kept defaulting to assistant behaviour until prompt was rewritten
- Docker test was initially missing for `chat.py` — caught during review loop

## Skills improved this session
- `implement` — test before review, loop back on any gap including user feedback, wait for PR merge
- `review` — check docs consistency and Docker test coverage
- `test` — Docker test must cover what the system actually does on the Pi, not just "exits cleanly"

## What's in place
- `chat.py` — `send_message()` + `run_chat()` REPL, Sudo's own personality
- `tests/test_chat.py` — 5 unit tests
- `tests/test_docker.py` — 2 Docker integration tests (single + multi-turn)
- `.flake8` — flake8 config
- `docs/PLAN.md` — Phase 2 complete, Phase 3 (Persistence) added, Phases 4–6 renumbered
- `docs/ARCHITECTURE.md` — all phases updated

## Next steps (Phase 3: Persistence)
Sudo remembers past conversations and genuinely evolves over time. Two files on disk:

1. **`memory/history.json`** — rolling window of last N conversation turns, loaded at startup and appended each session
2. **`memory/identity.md`** — Sudo's self-concept: personality traits, opinions, observations — written and updated by Sudo itself at the end of each session via a reflection call to Claude

Implementation order:
1. Load/save `history.json` on startup/exit — rolling window (last 50 messages)
2. Create `identity.md` on first run via a Claude call ("who are you?"), inject into system prompt
3. On `exit`, Sudo reflects on the session and updates `identity.md` autonomously
4. Add Docker volume mount in dev so memory survives container restarts
5. Compress `identity.md` when it exceeds a size threshold (Sudo decides what to keep)

**Note:** SD card not yet arrived — Pi deploy still pending. All dev on Mac via Docker.
