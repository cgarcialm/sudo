# Research: Memory Redesign (Phase 5)

## Problem

Phase 3 added `history.json` (recent turns) and `identity.md` (self-concept). Two gaps
emerged in practice:

**1. Fresh deploys still feel blank.** `identity.md` accumulates Sudo's self-concept, but
there's no narrative thread — no sense of "last time we talked about X." Sudo knows who
it is but not what it's been doing lately.

**2. The history window is too blunt.** A rolling 20-turn window either keeps too much
(stale context from hours ago) or too little (a long session loses its beginning before
it ends). What we want is a compressed, narrative summary of each session — not raw turns.

## Research

The problem is a classic tiered memory architecture:
- **Hot** (in-context): current session turns, verbatim
- **Warm** (summarized): recent past sessions, compressed to key points
- **Cold** (identity): long-term self-concept, written and maintained by Sudo

**Session summaries** are the missing tier. At session end, ask Claude to write a 2–4
sentence first-person summary of what happened. Store up to 10 of these in `summaries.json`.
Inject them into the system prompt at startup (oldest first) so Sudo has a narrative
sense of recent history without token-bloating with raw turns.

This pairs with the existing identity reflection: one parallel API call for identity
rewrite, one for session summary. Both happen at session end, both use the same history
as input. `ThreadPoolExecutor` runs them concurrently to avoid doubling the shutdown delay.

## Options

### Option A: Extend raw history window (e.g. 50 turns)
- Pro: no extra API calls; no new files
- Con: large context on every call; most content is redundant noise; doesn't solve the
  "what happened last session" problem

### Option B: Session summaries in `summaries.json`
- Pro: concise narrative continuity; scales to many sessions; cheap (one API call/session)
- Con: one extra API call at session end; quality depends on Claude's summarization

### Option C: Vector database of past turns (semantic search)
- Pro: fine-grained retrieval; scales to arbitrarily long history
- Con: massively over-engineered for a Pi robot; requires embedding model + vector DB

## Decision

**Option B: session summaries as a second memory tier.**

The three-tier model (recent turns + session summaries + identity) gives Sudo exactly
the memory architecture it needs without over-engineering. The parallel `ThreadPoolExecutor`
approach keeps shutdown fast. The 10-summary rolling window keeps token cost bounded.

`build_system_prompt()` assembles all three tiers in order: identity → summaries → recent
turns. Each tier is injected only if present (fresh deploys start with nothing and build
up naturally).
