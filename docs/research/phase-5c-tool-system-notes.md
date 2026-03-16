# Research: Tool System + Cross-Session Notes (Phase 5c)

## Problem

Sudo has two gaps:

**1. No cross-session memory beyond identity and summaries**
Anything Sudo encounters during a conversation — an idea, something it found curious,
something worth holding onto — disappears once it falls outside the 20-turn history window.
`identity.md` is Sudo's self-concept (inward, compressed). `summaries.json` is narrative
(what happened). Neither is the right place for Sudo to keep observations about the world
or things it noticed. There is no mechanism for Sudo to write a note mid-conversation and
have it available in a future session.

**2. Output channels are hardcoded**
The only way Sudo can affect the world right now is `<screen>`. Sudo is a physical robot
that will gain LEDs, a speaker, and motors. Every new output channel currently requires
touching the regex, the stream suppression logic, the system prompt, and the execution
path in `chat.py` — all separately, all by hand.

---

## Research

### Current architecture

`chat.py` handles screen output through:
- `_SCREEN_RE = re.compile(r"<screen>(.*?)</screen>", re.DOTALL)` — extraction regex
- `_SCREEN_TAG = "<screen>"` / `_SCREEN_TAG_LEN` — stream suppression constants
- Hardcoded screen instructions in `SYSTEM_PROMPT`
- Direct `if svg is not None: _render_and_save(...)` in the main loop
- `render_queue` for bridging background threads to the main (pygame) thread

Adding a second output channel (`<remember>`, `<led>`, etc.) today would require:
1. A new regex constant
2. A new stream suppression branch
3. A manual addition to `SYSTEM_PROMPT`
4. A new if-branch in the main loop and expression loop
5. A new queue if the handler needs the main thread

This is O(N) code changes per new tool. The pattern is obvious and mechanical — it should
be data, not code.

### Why tags over native Claude tool use (`tools=[]`)

The Anthropic API `tools=[]` feature requires a round-trip:
`user → Sudo → tool_call → tool_result → Sudo → final reply`

That's +1–3s latency per tool call and blocks the streaming reply. On a Pi over WiFi,
that's noticeable and disruptive to Sudo's conversational flow. Tags are parsed from the
stream that's already happening — zero overhead and no round-trip.

Limitation: tags can't return data to Sudo in the same turn. Acceptable for all
write-only tools (draw, remember, light up LEDs, speak). Read tools are a future concern.

### Prior art: expression loop queue

The existing `render_queue` pattern already solves the main-thread problem for screen:
background threads can't call pygame, so they put SVGs on a queue and the main loop
drains it. This pattern generalizes cleanly: an `action_queue` of `(tool, content)` pairs
replaces the SVG-specific `render_queue`.

---

## Options

### Option A: Keep screen-specific code, add remember as a one-off

Add `<remember>` handling alongside the existing `<screen>` handling:
- New regex, new stream suppression branch, manual system prompt update
- Pro: minimal change surface
- Con: doesn't solve the underlying O(N) problem; third tool requires same surgery again

### Option B: Tag-based tool registry

Generalize `<screen>` into a registry of `ToolDef` objects. Each tool declares its name,
description (injected into the system prompt automatically), handler, and threading model.
Adding a new tool means adding one dict entry.

- `parse_reply(raw, tool_names)` replaces `parse_reply(raw)` — extracts all registered tags
- Stream suppression finds the earliest opener of any registered tag
- System prompt tool block is generated from the registry
- `action_queue` of `(ToolDef, content)` replaces `render_queue` (SVG-specific)
- `_dispatch_tool_calls(calls, action_queue, tools)` routes: main_thread → queue, else → inline

- Pro: scales to N tools with zero additional plumbing
- Con: slightly more initial complexity; changes `parse_reply` signature (tests need updating)

### Option C: Native Claude tool use for `<remember>`

Use `tools=[{"name": "remember", ...}]` in the API call. Claude returns a structured
`tool_use` block instead of a tag.

- Pro: structured, validated, idiomatic Anthropic API usage
- Con: +1–3s round-trip latency per remember call; blocks streaming; heavier API contract

---

## Decision

**Option B: tag-based tool registry.**

The tag pattern is already working for `<screen>` and costs nothing. Generalizing it
eliminates the O(N)-per-tool maintenance burden and prepares the codebase for LEDs,
speaker, and other hardware outputs without architectural surgery.

`<remember>` is the first new tool. It appends notes to `memory/notes.md`, which is
loaded at startup and injected into the system prompt between identity and summaries.
Sudo writes in the moment — not in a batch at session end.

Key design choices:
- `ToolDef.main_thread=True` tools go on `action_queue`; others run inline. This preserves
  the existing threading model while extending it.
- `ToolDef.returns_result=False` placeholder field anticipates future async read tools
  (e.g. `<recall>`) without implementing them now.
- `TOOLS` is module-level for description generation; live handlers are injected via
  `_make_tools(renderer, screen_state, client)` closures in `run_chat()`. This avoids
  module-level mutable state and keeps tests clean.
- Notes are compressed by Claude (same pattern as identity) when they exceed
  `NOTES_MAX_CHARS=4000`.
