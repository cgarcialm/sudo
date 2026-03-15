# Handoff — Phase 5: Memory Redesign (complete)

## Goal
Add tiered memory so Sudo has continuity across sessions, reduce history window, and redesign the phase order.

## What was implemented

**Tiered memory system:**
- `memory/history.json` — last 20 turns (down from 50). Trimmed on save.
- `memory/summaries.json` — session summaries, one short paragraph per session written by Sudo at session end. Rolling window of 10. Loaded and injected into the system prompt.
- `memory/identity.md` — unchanged. Starts blank on fresh deploy; Sudo builds it after first session.

**`src/config.py`**
- `MAX_HISTORY_TURNS = 20` (was 50)
- `MAX_SUMMARIES = 10`
- `SUMMARIES_PATH = "memory/summaries.json"`

**`src/memory.py`**
- `_load_json(path)` — shared helper used by `load_history` and `load_summaries`
- `load_summaries()` / `save_summary()` — load/append/trim session summaries
- `build_system_prompt(base, identity, summaries)` — now injects all three tiers
- `reflect_and_update_identity()` — runs identity reflection and summary generation in **parallel** via `ThreadPoolExecutor(max_workers=2)`

**`src/chat.py`** — `run_chat()` loads summaries and passes them to `build_system_prompt`

**Phase order in docs:**
- Phase 5: Memory Redesign ✅
- Phase 6: Microphone (next)
- Phase 7: Vision
- Phase 8: Body
- Phase 9: Autonomy

## Fresh deploy behaviour
`memory/` is git-ignored. On first run Sudo starts with no identity and no summaries. After the first session it will write both. No seed file — Sudo defines itself from scratch.

## Transferring memory to Pi
If you want the Pi to have your existing history and identity, just copy the files:
```bash
scp memory/history.json memory/identity.md memory/summaries.json sudo@raspberry.local:~/sudo/memory/
```
The Pi will load them at next startup.

## Next steps (Phase 6: Microphone)
1. Create `src/audio.py` — `AudioCapture` class using `pyaudio`; `transcribe(audio_path) -> str` using `faster-whisper`
2. Add push-to-talk to `run_chat()` in `src/chat.py`: press Enter to start recording, Enter again to stop and transcribe, then send transcription as user message
3. `src/config.py`: `WHISPER_MODEL = "base"`, `AUDIO_SAMPLE_RATE = 16000`
4. `requirements.txt`: add `faster-whisper`, `pyaudio`
5. `Dockerfile`: add `portaudio19-dev` system package
6. `tests/test_audio.py`: mocked audio device tests (no real mic in CI)
7. Use `tiny` or `base` whisper model — `tiny` is faster on Pi, `base` is more accurate
