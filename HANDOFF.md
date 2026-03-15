# Handoff — Phase 3 Persistence

## Goal
Give Sudo memory across sessions: conversation history and an evolving self-concept that
survives container restarts.

## What was tried
- Straightforward: `memory.py` module for all disk I/O, wired into `chat.py` on startup/exit.

## What worked
- `memory/history.json` — last 50 turns loaded at startup, saved on exit
- `memory/identity.md` — Sudo rewrites this at the end of every session via a reflection
  call; injected into the system prompt so Sudo picks up where it left off
- Identity compressed by Sudo if it exceeds 4000 chars
- `Dockerfile` declares `VOLUME /app/memory`; mount with `-v ./memory:/app/memory` in dev
- Sudo correctly remembers users and facts across sessions when the volume is mounted
- Terminal output polished: blank line before replies, `> Sudo:` prefix, newline after Goodbye

## What failed
- Nothing structural failed. One discovery: Sudo initially told users it couldn't remember
  things — confidently wrong about its own capabilities. The reflection system will naturally
  correct this over sessions as Sudo learns what it can do.

## What's in place
- `memory.py` — `load_history`, `save_history`, `load_identity`, `save_identity`,
  `build_system_prompt`, `reflect_and_update_identity`, `_compress_identity`
- `chat.py` — loads memory on startup, saves + reflects on exit, polished terminal output
- `tests/test_memory.py` — 12 unit tests
- `tests/test_docker.py` — 3 Docker integration tests including persistence test
- `.gitignore` — `memory/` excluded from version control
- Skills updated: always rebuild Docker image before running Docker tests

## Transferring memory to the Pi
When the Pi arrives, copy the `memory/` folder with `scp`:
```bash
scp -r ./memory/ pi@<pi-ip>:~/sudo/memory/
```

## Next steps (Phase 4: Face)
Animated face UI on the screen — Claude controls which emotion to display.

1. Decide on rendering approach (pygame on the Pi's display, or a minimal HTML canvas served locally)
2. Define emotion states (e.g. neutral, happy, curious, thinking, surprised)
3. Change `send_message` to return both text and an emotion tag — Claude responds with
   structured output (JSON or a simple prefix) so the face can react
4. Render the face on the Pi's screen, updating on each reply
5. Test: mock the face renderer in unit tests; Docker test verifies emotion tag is present
   in the response

**Note:** Pi has arrived but SD card has not — all dev still on Mac via Docker.
