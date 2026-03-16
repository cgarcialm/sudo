# Sudo — Development Plan

Sudo is a Raspberry Pi 4 AI robot powered by Claude.

## Hardware
- Raspberry Pi 4
- Camera
- Microphone
- Speaker
- Screen
- LEDs
- Wheels + motors
- Body mount
- Ambient light sensor (e.g. BH1750)
- Temperature sensor (e.g. DHT22)

## Phases

### Phase 1: Foundation ✅
ARM64 Docker environment working on Mac, ready to deploy to Pi when it arrives.
Research: [phase-1-foundation.md](research/phase-1-foundation.md)
- ARM64 Docker environment (mirrors Pi architecture) ✅
- Python + Anthropic SDK ✅
- Basic API call works from inside Docker ✅
- Deploy and verify on Pi (pending — Pi arriving soon)

### Phase 2: Chat ✅
Text-based conversation with Sudo via terminal.
Research: [phase-2-chat.md](research/phase-2-chat.md)
- Terminal REPL (`chat.py`) ✅
- Conversation history maintained for the session ✅
- System prompt sets Sudo's personality ✅

### Phase 3: Persistence ✅
Sudo remembers past conversations and genuinely evolves over time.
Research: [phase-3-persistence.md](research/phase-3-persistence.md)
- `memory/history.json` — rolling window of last 20 conversation turns, loaded at startup ✅
- `memory/identity.md` — Sudo's self-concept: personality, opinions, and observations written and updated by Sudo itself ✅
- At session end, Sudo reflects on the conversation and updates `identity.md` autonomously ✅
- Both files injected into the system prompt at startup so Sudo picks up where it left off ✅
- Files live on disk (Pi: `~/sudo/memory/`, dev: Docker volume mount via `-v ./memory:/app/memory`) ✅
- `identity.md` compressed by Sudo when it grows too large, keeping only what feels significant ✅

### Phase 4: Screen ✅
Sudo has a pixel screen it can paint however it wants.
Research: [phase-4-screen.md](research/phase-4-screen.md)
- pygame window renders a 16×16 pixel grid — superseded by SVG in Phase 4b ✅
- `run.sh` is the canonical way to run Sudo (user and tests share it) ✅

### Phase 4b: SVG Screen + Autonomous Expression ✅
Research: [phase-4b-svg-expression.md](research/phase-4b-svg-expression.md)
Replace the 16×16 pixel grid with SVG — fewer tokens, more expressive, scales to any resolution.
Sudo also gets two independent output channels and learns about both through its system prompt.

- **SVG rendering**: replace pixel grid with SVG output; render via `cairosvg` + pygame ✅
- **Eager display init**: pygame window opens immediately at startup; main thread pumps events via `tick()` while waiting for input ✅
- **Two output channels**: ✅
  - Conversation reply (text, optionally includes `<screen><svg>...</svg></screen>`)
  - Autonomous expression loop: background thread wakes every 15s (default), asks Sudo "do you want to express something?", queues SVG for main thread to render
- **System prompt update**: tell Sudo what it is (Pi robot), that it has a physical screen (480×320), and that it has both channels available ✅
- Loops are independent — conversation never blocks expression and vice versa ✅
- **Screen context awareness**: `ScreenState` dataclass shared between threads; `_system_with_screen()` injects current SVG into system prompt per call so Sudo knows what it's showing ✅
- **Expression loop context**: expression loop snapshots last `EXPRESSION_HISTORY_WINDOW=6` history turns before each API call, so it draws with conversation awareness ✅
- **Fullscreen**: pygame uses `FULLSCREEN` flag at native resolution; `SCREEN_FULLSCREEN=false` env var enables windowed mode for dev/testing ✅

### Phase 5: Memory Redesign ✅
Fix three problems: fresh deploys start blank, history window is too large, no continuity between sessions.
Research: [phase-5-memory-redesign.md](research/phase-5-memory-redesign.md)

**Tiered memory:**
- Tier 1 — Recent turns (in-context): last 20 turns from `history.json`
- Tier 2 — Session summaries (warm): `summaries.json` — one short paragraph per past session, written by Sudo at session end, rolling window of 10
- Tier 3 — Identity (self-concept): `identity.md` — Sudo builds this itself; starts blank on fresh deploy (first session will create it)

**At startup:** all three tiers injected into system prompt as `[identity] + [last N summaries] + [recent turns]`.

**At session end:** Sudo writes a short session summary (appended to `summaries.json`) in addition to updating `identity.md`.

Files:
- `src/config.py` — `MAX_HISTORY_TURNS=20`, `MAX_SUMMARIES=10`, `SUMMARIES_PATH`
- `src/memory.py` — `load_summaries()`, `save_summary()`, updated `build_system_prompt()`, summary generation in `reflect_and_update_identity()` (runs in parallel with identity reflection)
- `tests/test_memory.py` — summaries load/save/trim, system prompt injection

### Phase 5b: SVG Gallery ✅
Research: [phase-5b-gallery-exit.md](research/phase-5b-gallery-exit.md)
Save every rendered SVG to `memory/gallery/YYYY-MM-DD/HH-MM-SS.svg` for later review.
- `GALLERY_ENABLED=true` env var enables saves (off by default) ✅
- `_save_to_gallery(svg)` called from `_render_and_save()` when enabled ✅
- Fix exit hang: `os._exit(0)` after `run_chat()` in `__main__` ✅

### Phase 5c: Tool System + Cross-Session Notes ✅
Research: [phase-5c-tool-system-notes.md](research/phase-5c-tool-system-notes.md)
Generalize `<screen>` into a tag-based tool registry. Add `<remember>` as the first new tool.

**Tool registry (`ToolDef`):**
- Each tool declares: name, description, handler, `main_thread`, `returns_result`
- `TOOLS` dict at module level drives system prompt generation and parse/dispatch
- `_build_tool_descriptions(tools)` generates the output-channels block in the system prompt automatically
- Adding a new output channel (LED, speaker, motor) = one dict entry, zero other changes

**Generalized parsing and stream suppression:**
- `parse_reply(raw, tool_names) -> (text, dict)` replaces the screen-specific version
- Stream suppression finds the earliest opener of any registered tag (not just `<screen>`)
- `_dispatch_tool_calls(calls, action_queue, tools)`: main-thread tools → queue, others → inline
- `action_queue` of `(ToolDef, content)` replaces the SVG-specific `render_queue`

**`<remember>` tool:**
- Sudo writes to `memory/notes.md` mid-conversation when something is worth keeping
- Notes loaded at startup, injected into system prompt between identity and summaries
- Compressed by Claude (same pattern as identity) when notes exceed `NOTES_MAX_CHARS=4000`

Files:
- `src/prompts.py` — all Claude prompts centralised (`REFLECT`, `COMPRESS_IDENTITY`, `SUMMARIZE`, `COMPRESS_NOTES`, `BASE`, `EXPRESSION`)
- `src/config.py` — `NOTES_PATH`, `NOTES_MAX_CHARS`, `MAX_TOKENS_NOTES`
- `src/memory.py` — `load_notes()`, `save_notes()`, `append_note()`, `_compress_text()`, updated `build_system_prompt()`
- `src/chat.py` — `ToolDef`, `TOOLS`, `_build_tool_descriptions()`, `parse_reply()`, `_dispatch_tool_calls()`, `_make_tools()`, rename `render_queue` → `action_queue`
- `tests/test_memory.py` — notes load/save/compress, system prompt ordering
- `tests/test_chat.py` — tool parsing, stream suppression, remember handler
- `tests/test_docker.py` — assert `notes.md` written after session; tool tags stripped
- `docs/research/phase-5c-tool-system-notes.md` — problem, research, options, decision

### Phase 6: Microphone
Push-to-talk voice input. Press Enter to start recording, Enter again to stop; transcription sent as user message.

- `src/audio.py` — `AudioCapture` class using `pyaudio`; `transcribe(audio_path) -> str` using `faster-whisper` (lighter than openai-whisper, runs on Pi)
- `src/chat.py` — `run_chat()` offers voice input mode; press Enter to record, Enter again to stop and transcribe
- `src/config.py` — audio config: `WHISPER_MODEL="base"`, `AUDIO_SAMPLE_RATE=16000`
- `requirements.txt` — add `faster-whisper`, `pyaudio`
- `Dockerfile` — add `portaudio19-dev` system package
- `tests/test_audio.py` — mocked audio device tests
- Use `tiny` or `base` whisper model for Pi speed

### Phase 7: Vision
Camera input sent to Claude.
- Capture and compress frames (320x240)
- Send frames to Claude with context
- Claude interprets what it sees

### Phase 8: Body
Sudo gets a sense of its environment through cheap local sensors. The Pi preprocesses everything and sends compressed text summaries — not raw data — to keep token cost low.
- **Audio**: local model classifies ambient sound (quiet/loud, voice present/absent, inside/outside) → one-line summary injected into context
- **Light**: ambient light sensor → time-of-day awareness (day/night/dim)
- **Temperature**: cheap sensor → hot/cold/comfortable
- **Time**: always available, always included
- Principle: process locally, send summaries. "It's quiet, midday, no one in the room." costs almost nothing and gives Sudo a real sense of presence.

### Phase 9: Autonomy
Sudo moves, reacts, and makes decisions on its own.
- High-level navigation: user gives a goal ("go to the door"), Claude uses camera frames to decide each movement step
- Uses `claude-haiku-4-5` for speed and cost efficiency
- Short structured prompts, max_tokens=50 (single direction per call)
- ~1 call per 2 seconds while navigating (~$2.70/hr)
- Hardware safety layer (ultrasonic sensor) as collision cutoff regardless of AI decision
- LED reactions tied to mood/state
- Proactive behavior and mood system
