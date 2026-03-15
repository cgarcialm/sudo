# Handoff — Phase 4b SVG Screen (ready to implement)

## Goal
Replace the 16×16 pixel grid with SVG output and give Sudo two independent output channels —
conversation replies and autonomous visual expression — both learned through the system prompt.

## Context from previous sessions
- Phase 4 (pixel screen) is complete and working on the Pi
- The pixel grid is slow to render and token-heavy (~800 tokens per reply just for the grid)
- Pi is set up and running: `ssh sudo@raspberry.local`, repo at `~/sudo/`
- `DISPLAY=:0` required when running over SSH with a monitor connected
- Branch: `feat/svg-screen` (already created, branched from main)

## What to implement

### 1. System prompt update
Tell Sudo:
- It is a robot running on a Raspberry Pi with a physical screen
- It has two output channels:
  1. Conversation reply — text, optionally includes `<screen><svg>...</svg></screen>`
  2. Autonomous expression — a background loop periodically invites Sudo to express something visually
- Sudo decides when and what to draw — it owns the screen

### 2. SVG rendering (`src/screen.py`)
- Replace `render(grid)` with `render(svg_string)`
- Use `cairosvg` to convert SVG → PNG bytes → pygame surface
- Add `cairosvg` to `requirements.txt`

### 3. Autonomous expression loop (`src/chat.py`)
- Background thread, wakes every N seconds (configurable in `src/config.py`)
- Sends a short prompt: "You have a moment. Do you want to express something on your screen? If yes, respond with only an SVG. If no, respond with nothing."
- If Sudo responds with SVG, render it
- Loop runs independently — never blocks conversation

### 4. Config (`src/config.py`)
- Add `EXPRESSION_INTERVAL_SECONDS = 30` (or similar)

## Files to change
- `src/chat.py` — system prompt, stream reply, autonomous loop
- `src/screen.py` — SVG rendering replacing pixel grid
- `src/config.py` — expression interval constant
- `requirements.txt` — add `cairosvg`
- `tests/test_chat.py` — update tests for SVG format
- `tests/test_screen.py` — update tests for new render method

## What worked in Phase 4 (keep)
- `_SCREEN_TAG` sentinel + streaming suppression pattern — reuse for SVG tag
- `parse_reply()` — same structure, just different content inside `<screen>`
- `ScreenRenderer` lazy-init and headless skip — keep both
- `DISPLAY=:0` needed on Pi over SSH

## Next steps in order
1. Update system prompt in `src/chat.py`
2. Swap SVG rendering in `src/screen.py`
3. Add autonomous expression loop
4. Update tests
5. Test on Pi (`ssh sudo@raspberry.local`, `cd sudo && DISPLAY=:0 python src/chat.py`)
