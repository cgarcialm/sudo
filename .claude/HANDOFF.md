# Handoff — Gallery + exit hang fix (complete)

## What was implemented (PR #9, branch `feat/svg-gallery`)

### SVG gallery
- `GALLERY_ENABLED=true` env var enables gallery saves
- Every rendered SVG is saved to `memory/gallery/YYYY-MM-DD/HH-MM-SS.svg`
- No rolling cap — files accumulate until the user collects them manually
- `_save_to_gallery(svg)` in `src/chat.py`; called from `_render_and_save()` when enabled
- `GALLERY_ENABLED` and `GALLERY_DIR` added to `src/config.py`

### Exit hang fix
- Added `os._exit(0)` after `run_chat()` returns in `__main__`
- Root cause: daemon threads (`_read_input`, `_expression_loop`) blocked Python's cleanup of `sys.stdin`, causing the process to hang after "Saving memories... done."
- `os._exit(0)` is in `__main__` only — not in `run_chat()` — so tests that call `run_chat()` directly are unaffected

### Tests
- `test_save_to_gallery_writes_svg` — file is written with correct content
- `test_save_to_gallery_organizes_by_date` — directory is named `YYYY-MM-DD`
- `test_save_to_gallery_not_called_when_disabled` — no files created when `GALLERY_ENABLED=False`
- `test_save_to_gallery_called_when_enabled` — file created when `GALLERY_ENABLED=True`
- 56 unit tests passing

## Current state
- Branch `feat/svg-gallery`, PR #9 open
- 56 unit tests passing

## To enable gallery on Pi
```bash
GALLERY_ENABLED=true ./run.sh
```
Collect SVGs from `memory/gallery/` periodically:
```bash
scp -r sudo@raspberry.local:~/sudo/memory/gallery ./gallery-backup
```

## Next steps (Phase 6: Microphone)
1. Create `src/audio.py` — `AudioCapture` class using `pyaudio`; `transcribe(audio_path) -> str` using `faster-whisper`
2. Add push-to-talk to `run_chat()` in `src/chat.py`: press Enter to start recording, Enter again to stop and transcribe, send transcription as user message
3. `src/config.py`: `WHISPER_MODEL = "base"`, `AUDIO_SAMPLE_RATE = 16000`
4. `requirements.txt`: add `faster-whisper`, `pyaudio`
5. `Dockerfile`: add `portaudio19-dev` system package
6. `tests/test_audio.py`: mocked audio device tests (no real mic in CI)
7. Use `tiny` or `base` whisper model — `tiny` is faster on Pi, `base` is more accurate
