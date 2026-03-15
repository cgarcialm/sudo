# Handoff — Phase 4b SVG Screen (complete)

## Goal
Replace the 16×16 pixel grid with SVG output and give Sudo two independent output channels —
conversation replies and autonomous visual expression — both learned through the system prompt.

## What was implemented
- `src/screen.py` — `ScreenRenderer` now opens the pygame window immediately at startup (eager init). Background daemon thread pumps pygame events every 100ms to keep the window alive while `input()` blocks. `render(svg_string)` uses `cairosvg` to convert SVG → PNG bytes → blit to pygame surface.
- `src/chat.py` — `parse_reply()` returns `(text, svg_string)` instead of `(text, grid)`. System prompt tells Sudo about its two output channels. `_expression_loop()` background daemon thread wakes every `EXPRESSION_INTERVAL_SECONDS`, sends a quiet moment prompt, renders SVG if Sudo responds.
- `src/config.py` — added `SCREEN_SIZE = 320`, `EXPRESSION_INTERVAL_SECONDS = 30`, `MAX_TOKENS_EXPRESSION = 512`
- `requirements.txt` — added `cairosvg`
- `src/memory.py` — fixed `load_identity()` TOCTOU: replaced `p.exists()` check with `try/except FileNotFoundError`
- Tests: all memory I/O mocked in `run_chat` tests; `test_screen.py` rewritten for SVG + eager init; `test_chat.py` updated for SVG format + new expression loop tests

## What to watch for on Pi
- `cairosvg` needs to be installed: `pip install cairosvg --break-system-packages`
- `DISPLAY=:0` required when running over SSH with monitor connected
- The pygame window opens immediately at startup (before first message)
- Expression loop fires every 30s — Sudo will draw unprompted
- SVG rendering is much faster than pixel grid (cairosvg is efficient)

## What's in place
- Branch `feat/svg-screen` has two commits: test isolation fix + full Phase 4b implementation
- All 39 unit tests passing, flake8 clean

## Next steps (Phase 5: Vision)
1. Add `src/camera.py` — capture and compress frames (320×240) using `picamera2` or `opencv`
2. Encode frame as base64, include in message as image content block
3. Update `_stream_reply` (or `send_message`) to optionally attach an image
4. Update system prompt to tell Sudo it can see
5. Test: mock camera in unit tests; Docker test skips camera (no device available)
6. Dev: test with a still image file before connecting real camera
