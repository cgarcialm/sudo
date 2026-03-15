# Handoff — Phase 4b SVG Screen (complete)

## Goal
Replace the 16×16 pixel grid with SVG output and give Sudo two independent output channels —
conversation replies and autonomous visual expression — both learned through the system prompt.

## What was implemented
- `src/screen.py` — `ScreenRenderer` opens the pygame window immediately at startup. `tick()` pumps pygame events from the main thread (required on macOS — background thread approach doesn't work with Cocoa). `render(svg_string)` uses `cairosvg` to convert SVG → PNG bytes → blit to pygame surface. cairosvg import catches `(ImportError, OSError)` to handle missing system library gracefully.
- `src/chat.py` — `parse_reply()` returns `(text, svg_string)`. System prompt tells Sudo about its two output channels. `_expression_loop()` daemon thread wakes every `EXPRESSION_INTERVAL_SECONDS`, sends quiet moment prompt, renders SVG if returned. `run_chat()` moves `input()` to a background thread so the main thread can run the pygame event loop via `renderer.tick()` every 50ms.
- `src/config.py` — `SCREEN_SIZE = 320`, `EXPRESSION_INTERVAL_SECONDS = 30`, `MAX_TOKENS_EXPRESSION = 512`
- `src/memory.py` — fixed `load_identity()` TOCTOU: `p.exists()` → `try/except FileNotFoundError`
- `requirements.txt` — added `cairosvg`
- `Dockerfile` — added `libcairo2` system package
- `dev.sh` — local dev script: `uv run python src/chat.py` with `PYTHONPATH=src`
- `tests/mock_anthropic_server.py` — updated to support streaming SSE and return SVG response
- `tests/test_chat.py`, `tests/test_screen.py` — updated for SVG format, eager init, tick()

## How to run locally (mock server, no API key)
```bash
# Terminal 1
uv run python tests/mock_anthropic_server.py

# Terminal 2
ANTHROPIC_API_KEY=test-key ANTHROPIC_BASE_URL=http://localhost:8765 ./dev.sh
```

## How to run on Pi
```bash
ssh sudo@raspberry.local
cd sudo && git pull
pip install cairosvg --break-system-packages  # first time only
DISPLAY=:0 python src/chat.py
```

## Next steps (Phase 5: Vision)
1. Add `src/camera.py` — capture and compress frames (320×240) using `picamera2` or `opencv`
2. Encode frame as base64, include in message as image content block
3. Update `_stream_reply` (or `send_message`) to optionally attach an image
4. Update system prompt to tell Sudo it can see
5. Test: mock camera in unit tests; Docker test skips camera (no device available)
6. Dev: test with a still image file before connecting real camera
