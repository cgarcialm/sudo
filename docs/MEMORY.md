# Sudo — Memory Design

Sudo's memory is split across four files on disk. Each tier serves a different purpose and has a different lifecycle.

---

## Memory files

| File | Contents | Written | Max size |
|---|---|---|---|
| `memory/history.json` | Last N conversation turns (raw messages) | On exit | `MAX_HISTORY_TURNS = 20` turns |
| `memory/identity.md` | Sudo's self-concept — personality, opinions, observations | On exit | `IDENTITY_MAX_CHARS = 4000` chars (compressed if exceeded) |
| `memory/notes.md` | Cross-session observations Sudo chose to keep | Mid-conversation, via `<remember>` | `NOTES_MAX_CHARS = 4000` chars (compressed if exceeded) |
| `memory/summaries.json` | Short narrative summaries of past sessions | On exit | `MAX_SUMMARIES = 10` entries (rolling window) |

---

## System prompt construction

At startup, all four tiers are injected into the system prompt in this order:

```
BASE prompt (prompts.BASE + tool descriptions)
    ↓
Your current self-concept: [identity.md]       ← omitted if file missing
    ↓
Your notes: [notes.md]                         ← omitted if file missing
    ↓
Your recent session summaries: [summaries.json] ← omitted if empty
    ↓
[history.json turns loaded into messages list]
```

History turns are not part of the system prompt — they go into the `messages` array passed to the API.

---

## Read / write lifecycle

```
Startup
  load_history()       → messages list (in-memory, mutated during session)
  load_identity()      → injected into system prompt
  load_notes()         → injected into system prompt
  load_summaries()     → injected into system prompt

Mid-conversation
  <remember> tool      → append_note() → notes.md written immediately to disk
                         (compressed via Claude if len > NOTES_MAX_CHARS)

On exit (parallel API calls)
  reflect_and_update_identity()
    ├── Claude rewrites identity.md
    └── Claude writes a session summary → appended to summaries.json
  save_history()       → history.json trimmed to MAX_HISTORY_TURNS
```

---

## Compression

Identity and notes are compressed by Claude when they exceed their size limits. The same helper handles both:

```
_compress_text(client, text, prompt, max_tokens, label)
    └── used by _compress_identity()  (triggered in reflect_and_update_identity)
    └── used by append_note()         (triggered inline when notes exceed limit)
```

Compression is lossy by design — Sudo decides what to keep based on what feels most significant. This is intentional: memory should evolve, not accumulate forever.

---

## Fresh deploy behaviour

On first boot, none of the memory files exist. `load_identity()`, `load_notes()`, and `load_summaries()` all return `None`/`[]`, so nothing is injected — only the BASE prompt and tool descriptions are sent. Sudo starts blank and builds its identity from scratch in that first session.

---

## Module

All memory I/O lives in `src/memory.py`. `src/chat.py` calls it at startup and exit; the `<remember>` handler in `_make_tools()` calls `append_note()` mid-session.

Key functions:

| Function | Purpose |
|---|---|
| `build_system_prompt(base, identity, notes, summaries)` | Assembles the full system prompt string |
| `load_history / save_history` | JSON read/write with turn trimming |
| `load_identity / save_identity` | Plain text read/write |
| `load_notes / save_notes` | Plain text read/write |
| `append_note(client, content)` | Append + compress notes mid-session |
| `load_summaries / save_summary` | JSON array with rolling window trim |
| `reflect_and_update_identity(client, history)` | Parallel Claude calls at session end |
