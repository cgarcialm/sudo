# Handoff — Phase 4 Screen (complete)

## Goal
Give Sudo a 16×16 pixel screen it owns and paints however it wants as part of every reply.

## What was tried
- `screen.py` module with a `ScreenRenderer`, wired into `chat.py`
- `run.sh` script so user and tests share the same Docker run command
- Docker build automated as a pytest session fixture
- Streaming added so text appears immediately; `<screen>` block moved to end of reply
- Image save: `memory/screen.png` written after every render

## What worked
- `screen.py` — `ScreenRenderer` lazy-inits pygame; silently skips if no display (Docker/headless); `pygame.event.pump()` required on macOS or window never appears
- `chat.py` — `_stream_reply()` streams text to terminal, suppresses `<screen>` block; `parse_reply()` extracts grid after full response; stores only text in history; `_MODEL` and `_MAX_TOKENS` are module-level constants shared by both API call sites
- `run.sh` — canonical run script; `MEMORY_DIR` env var overrides memory mount; tests set it to a temp dir
- `tests/conftest.py` — `docker_image` session fixture auto-builds before Docker tests; surfaces stderr on failure
- `.flake8` — `.venv` excluded so flake8 doesn't lint installed packages
- `memory/screen.png` — saved after each render; open with `open memory/screen.png`
- `.venv/` — local venv via `uv venv && uv pip install -r requirements.txt`

## What failed
- pygame window on macOS didn't appear without `pygame.event.pump()` — added after `pygame.display.flip()`
- `<screen>` block was leaking to terminal — fixed by moving it to end of reply and suppressing it in the streaming loop
- `max_tokens=1024` too low for grid JSON + reply — raised to 2048 (now `_MAX_TOKENS`)

## What's in place
- `screen.py` — `ScreenRenderer`: `render(grid)`, `save(path)`, `stop()`
- `chat.py` — `parse_reply()`, `SCREEN_PROMPT`, `_stream_reply()`, `_MODEL`, `_MAX_TOKENS`
- `run.sh` — `./run.sh` to run interactively; `ANTHROPIC_API_KEY` required
- `memory/screen.png` — latest screen state, saved each reply
- `docs/ARCHITECTURE.md` — updated with Phase 4 screen diagram, Phase 6 Body, Phase 7 Autonomy
- `docs/PLAN.md` — Phase 4 ✅, Phase 6 Body added, Phase 7 Autonomy

## Plan update
Phase ordering updated based on conversation with Cecilia:
- Phase 5: Vision (camera)
- Phase 6: Body (cheap local sensors — audio, light, temperature, time — preprocessed on Pi, sent as text summaries to keep token cost low)
- Phase 7: Autonomy (movement)

Principle for Phase 6: process locally, send summaries not raw data.
Sensors to add: BH1750 (ambient light), DHT22 (temperature), microphone with local audio classifier.

## Next steps (Phase 5: Vision)
1. Add `camera.py` — capture and compress frames (320×240) using `picamera2` or `opencv`
2. Encode frame as base64, include in message as image content block
3. Update `_stream_reply` (or `send_message`) to optionally attach an image
4. Update system prompt to tell Sudo it can see
5. Test: mock camera in unit tests; Docker test skips camera (no device available)
6. Dev: test with a still image file before connecting real camera
