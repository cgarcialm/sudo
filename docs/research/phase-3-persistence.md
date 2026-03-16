# Research: Persistence (Phase 3)

## Problem

Each Sudo session starts completely blank. Sudo has no memory of previous conversations,
no accumulated personality, and no continuity. Every session is effectively a first meeting.
This makes Sudo feel shallow — it can't grow, can't reference shared history, can't evolve.

## Research

Two kinds of persistence matter here:
1. **Conversational continuity**: remembering what was said in past sessions
2. **Identity continuity**: Sudo's personality, opinions, and self-concept persisting and evolving

**History alone isn't enough.** Even if we stored every message, replaying thousands of
turns at the start of each session would be expensive and dilute the signal. What Sudo
needs is a compressed, curated self-model — not a transcript.

**The key insight**: let Sudo write its own identity. At session end, ask Claude to reflect
on the conversation and rewrite `identity.md` in first person. Claude writes it, Claude
reads it. This means the identity is always in a format Claude understands and values.

**`history.json`** handles the short-term: recent turns available for in-context recall.
**`identity.md`** handles the long-term: Sudo's evolving self-concept.

Both files live on disk (`memory/`), mounted as a Docker volume so they persist across
container restarts. On the Pi this is `~/sudo/memory/`.

## Options

### Option A: Store raw history only, inject last N turns
- Pro: simple, no extra API calls at session end
- Con: no long-term identity; Sudo resets personality every session

### Option B: Store identity file, written by Sudo at session end
- Pro: Sudo genuinely accumulates a self over time; identity stays concise
- Con: requires an API call at session end; identity can drift or grow too large

### Option C: Fine-tune a model on past conversations
- Pro: deep personality embedding
- Con: expensive, slow, impractical for a Pi project

## Decision

**Option B: identity file written by Sudo at session end.**

The end-of-session reflection call is cheap (one API call, sub-second on a fast connection)
and produces exactly what we want: a concise, Sudo-authored self-concept. The `_compress_identity()`
fallback handles unbounded growth by asking Claude to condense when it exceeds `IDENTITY_MAX_CHARS`.

History is capped at `MAX_HISTORY_TURNS=20` — enough for in-context recall without sending
the full transcript every turn. Both files are injected into the system prompt at startup
so Sudo picks up exactly where it left off.
