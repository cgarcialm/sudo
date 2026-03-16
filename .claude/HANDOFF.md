# Handoff — Tool System + Cross-Session Notes (Phase 5c, complete)

## What was implemented (PR #10, branch `feat/tool-system-notes`)

### Tool registry
- `ToolDef` dataclass: `name`, `description`, `handler`, `main_thread`, `returns_result`
- `TOOLS` module-level dict drives system prompt generation and parse/dispatch
- `_build_tool_descriptions(tools)` generates the output-channels block automatically
- `_make_tools(renderer, screen_state, client)` creates live handlers as closures in `run_chat()`
- Adding a new output channel = one dict entry, zero other changes

### Generalised parsing and stream suppression
- `parse_reply(raw, tool_names) -> (text, dict)` replaces screen-specific version
- `_first_tool_tag_pos(buffer, tool_names, start)` finds earliest tag opener for stream suppression
- `_dispatch_tool_calls(calls, action_queue, tools)`: `main_thread=True` → queue, else → inline
- `action_queue` of `(ToolDef, content)` replaces SVG-specific `render_queue`
- `send_message` now returns `(text, calls)` dict instead of `(text, svg)`

### `<remember>` tool
- Sudo writes mid-conversation to `memory/notes.md`
- Notes loaded at startup, injected into system prompt between identity and summaries
- Compressed by Claude when `len > NOTES_MAX_CHARS=4000`

### Prompts centralised
- `src/prompts.py`: `REFLECT`, `COMPRESS_IDENTITY`, `SUMMARIZE`, `COMPRESS_NOTES`, `BASE`, `EXPRESSION`

### Research docs
- `docs/research/` — new directory with retrospective docs for phases 1–5b and prospective doc for 5c
- `docs/CODING_STANDARDS.md` — Research Docs section added (format, naming, process)
- `docs/PLAN.md` — research links on every phase entry

### Pi deployment script
- `pi.sh` — runs Sudo directly on Pi (no Docker); loads `.env` via `set -a`/`source`/`set +a`
- `.env.example` — updated with all configurable vars: `DISPLAY`, `SCREEN_FULLSCREEN`, `EXPRESSION_INTERVAL_SECONDS`, `GALLERY_ENABLED`, `LOG_LEVEL`
- `dev.sh` — `.env` loading aligned to use same `set -a`/`source`/`set +a` pattern

### Memory module refactor
- `_load_text_file(path)` / `_save_text_file(text, path)` — shared helpers used by identity and notes I/O
- `_compress_text(client, text, prompt, max_tokens, label)` — shared helper replacing duplicate compress functions
- `append_note(client, content)` — public function; encapsulates read-append-compress-save so `chat.py` never touches private memory internals

### Prompts fixes
- `BASE`: removed "robot" (avoids limiting Sudo's self-concept); fixed wording
- `EXPRESSION`: was hardcoded to `<screen><svg>` — now tool-agnostic
- `COMPRESS_IDENTITY` / `COMPRESS_NOTES`: removed hardcoded character limits (threshold enforced by config constants, not the prompt)

### Docs
- `docs/MEMORY.md` — new design doc covering memory tiers, system prompt construction, read/write lifecycle, compression, and fresh deploy behaviour
- `docs/ARCHITECTURE.md` — rewritten as current-state doc: communication flow diagrams, threading model, tool system, screen, memory, deployment. Removed phase changelog and unimplemented phases (mic, vision, body, autonomy).
- `docs/PLAN.md` — Phase 4 description updated to note pixel grid was superseded by Phase 4b

### Tests
- 75 unit tests passing
- 5 Docker integration tests passing
- `notes.md` existence asserted in `test_memory_written_after_session`
- `<remember>` tag stripped from output asserted in `test_screen_tag_stripped_from_output`
- `test_reflect_and_update_identity_saves_file` fixed to use content-based mock dispatch (was order-dependent, non-deterministic with ThreadPoolExecutor)
- `test_expression_loop_fires_without_crashing` assertion fixed to check actual log message

## Current state
- PR #10 open, branch `feat/tool-system-notes`
- All tests passing (75 unit + 5 Docker)

## Next steps (Phase 6: Microphone)
1. Create `src/audio.py` — `AudioCapture` class using `pyaudio`; `transcribe(audio_path) -> str` using `faster-whisper`
2. Add push-to-talk to `run_chat()` in `src/chat.py`: press Enter to start recording, Enter again to stop and transcribe, send transcription as user message
3. `src/config.py`: `WHISPER_MODEL = "base"`, `AUDIO_SAMPLE_RATE = 16000`
4. `requirements.txt`: add `faster-whisper`, `pyaudio`
5. `Dockerfile`: add `portaudio19-dev` system package
6. `tests/test_audio.py`: mocked audio device tests (no real mic in CI)
7. Use `tiny` or `base` whisper model — `tiny` is faster on Pi, `base` is more accurate

## Transferring memory to Pi
```bash
scp memory/history.json memory/identity.md memory/summaries.json memory/notes.md sudo@raspberry.local:~/sudo/memory/
```
