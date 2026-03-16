# Handoff — Screen fixes + context awareness (complete)

## What was implemented (PR #8, branch `fix/fullscreen-screen`)

### Fullscreen display
- `pygame.FULLSCREEN` flag at native resolution (480×320 OSOYOO 3.5" display)
- `pygame.transform.scale` after cairosvg render so image fills the screen regardless of SVG aspect ratio
- System prompt tells Claude to author SVGs at 480×320 (landscape)
- `SCREEN_FULLSCREEN=false` env var for windowed dev mode (set automatically by `dev.sh`)

### Screen context awareness
- `ScreenState` dataclass in `chat.py` shared between main thread and expression loop
  - `get_svg()` / `set_svg()` — thread-safe via internal lock
- `_system_with_screen(system_prompt, screen_state)` — appends current SVG to system prompt so Sudo always knows what it's showing
- Expression loop snapshots `history[-EXPRESSION_HISTORY_WINDOW:]` (last 6 history turns) before each API call so it draws with conversation context
- `EXPRESSION_HISTORY_WINDOW = 6` added to `config.py`

### History trimming
- History is now trimmed in-memory after each reply (`del history[:len-MAX_HISTORY_TURNS]`)
- Prevents unbounded context being sent to Claude in long sessions

### Dev tooling
- `dev.sh` always uses mock server + 5s expression interval + windowed mode
- `dev.sh` loads `.env` automatically
- `EXPRESSION_INTERVAL_SECONDS` overridable via env var
- Mock server returns distinct SVGs: red circle for chat (streaming), green rectangle for expression loop (non-streaming)

### Debug logging
- `LOG_LEVEL` env var controls log verbosity (default `WARNING`, set to `DEBUG` for expression loop visibility)
- `dev.sh` sets `LOG_LEVEL=DEBUG` automatically
- On Pi: `LOG_LEVEL=DEBUG ./run.sh` shows when expression loop fires, what Claude replies, and whether SVGs are queued
- `_setup_logging()` called from `run_chat()` — no module-level side effects

### Tests
- New Docker integration test: `test_expression_loop_fires_without_crashing` — runs Sudo with 2s interval, verifies no crashes
- `_render_and_save()` helper extracted to remove copy-paste
- `_base_url()` / `_network_args()` helpers in test_docker.py

## Current state
- All changes on branch `fix/fullscreen-screen`, PR #8 open
- 52 unit tests + 5 Docker integration tests all passing
- Pi verified: expression loop is working
- Expression interval: 15s (default; overridable via `EXPRESSION_INTERVAL_SECONDS`)

## Next steps (Phase 6: Microphone)
1. Create `src/audio.py` — `AudioCapture` class using `pyaudio`; `transcribe(audio_path) -> str` using `faster-whisper`
2. Add push-to-talk to `run_chat()` in `src/chat.py`: press Enter to start recording, Enter again to stop and transcribe, then send transcription as user message
3. `src/config.py`: `WHISPER_MODEL = "base"`, `AUDIO_SAMPLE_RATE = 16000`
4. `requirements.txt`: add `faster-whisper`, `pyaudio`
5. `Dockerfile`: add `portaudio19-dev` system package
6. `tests/test_audio.py`: mocked audio device tests (no real mic in CI)
7. Use `tiny` or `base` whisper model — `tiny` is faster on Pi, `base` is more accurate

## Transferring memory to Pi
```bash
scp memory/history.json memory/identity.md memory/summaries.json sudo@raspberry.local:~/sudo/memory/
```
