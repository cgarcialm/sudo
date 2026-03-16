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

### Tests
- 71 unit tests passing
- 5 Docker integration tests passing
- `notes.md` existence asserted in `test_memory_written_after_session`
- `<remember>` tag stripped from output asserted in `test_screen_tag_stripped_from_output`

## Current state
- PR #10 open, branch `feat/tool-system-notes`
- All tests passing (71 unit + 5 Docker)

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
