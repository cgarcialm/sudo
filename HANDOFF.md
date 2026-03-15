# Handoff — Phase 4 Screen

## Goal
Give Sudo a 16×16 pixel screen it owns and paints however it wants as part of every reply.

## What was tried
- Straightforward: `screen.py` module with a `ScreenRenderer`, wired into `chat.py`.
- `run.sh` script so user and tests share the same Docker run command.
- Docker build automated as a pytest session fixture.

## What worked
- `screen.py` — `ScreenRenderer` lazy-inits pygame; silently skips if no display (Docker/headless)
- `chat.py` — `parse_reply()` extracts `<screen>JSON</screen>` block in a single pass; stores only text in history (no screen data bloat); system prompt tells Sudo to paint whatever it wants
- `run.sh` — canonical run script; `MEMORY_DIR` env var overrides memory mount; tests set it to a temp dir
- `tests/conftest.py` — `docker_image` session fixture auto-builds before Docker tests; `mock_anthropic_server` depends on it
- `tests/test_docker.py` — calls `./run.sh` directly; `test_screen_tag_stripped_from_output` verifies `<screen>` never leaks to terminal
- `/simplify` caught: double regex scan in `parse_reply`, 256 `Rect` allocations per render, `platform.system()` called twice — all fixed

## What failed
- Nothing structural. Docker tests failed initially because `run.sh` mounted `./memory` and the test also passed `-v /tmp/...:/app/memory` — duplicate mount. Fixed with `MEMORY_DIR` env var.

## What's in place
- `screen.py` — `ScreenRenderer` class, `GRID_SIZE=16`, `PIXEL_SIZE=20`
- `chat.py` — `parse_reply()`, `SCREEN_PROMPT`, updated `send_message()` returns `(text, grid)`, `run_chat()` renders grid
- `run.sh` — `./run.sh [extra docker args]`; user sets `ANTHROPIC_API_KEY`
- `tests/test_screen.py` — 8 unit tests
- `tests/test_docker.py` — 4 integration tests via `run.sh`
- Implement skill updated: compact step restored, simplify step added before commit, docker build removed as manual step

## Transferring to the Pi
When the Pi arrives and SD card is set up:
```bash
scp -r ./memory/ pi@<pi-ip>:~/sudo/memory/
# On Pi, install system deps if needed and run:
./run.sh
```

## Next steps (Phase 5: Vision)
Camera input sent to Claude.

1. Add camera capture module (`camera.py`) — capture and compress frames (320×240)
2. Modify `send_message` to optionally include a base64 image in the message
3. Update `chat.py` to capture a frame on each turn and include it
4. Update system prompt to tell Sudo it can see
5. Test: mock camera in unit tests; Docker test skips camera (no device)
