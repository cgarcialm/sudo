# Research: Chat (Phase 2)

## Problem

Sudo needs a working conversational interface: send a message, get a reply, repeat.
This is the foundation everything else builds on. It must:
1. Maintain conversation history within a session
2. Give Sudo a stable personality via a system prompt
3. Be testable without real API calls

## Research

The Anthropic SDK's `client.messages.create()` takes a `messages` list representing the
full conversation history. To maintain context, we append each turn (user + assistant)
and pass the growing list on each call. The system prompt is a separate `system=` param
— not part of the messages array — which keeps it clean and easy to extend later.

The REPL pattern (read → send → print → repeat) is the simplest possible interface.
No framework, no async runtime, no UI library. Just `input()` + `print()`.

## Options

### Option A: Stateless — send only the latest message each turn
- Pro: simple, minimal token usage
- Con: Claude has no memory of previous turns within a session; Sudo forgets immediately

### Option B: Stateful — accumulate full history each turn
- Pro: coherent multi-turn conversation; Claude remembers what was said
- Con: token cost grows with conversation length (addressed in Phase 5 with a window)

### Option C: Use a higher-level framework (LangChain, etc.)
- Pro: batteries included
- Con: heavy dependency; abstracts away things we'll want to control directly

## Decision

**Option B: stateful history, no framework.**

Full history is required for a coherent conversation. Token cost is manageable at this
scale (Pi + occasional human interaction, not high-volume). A rolling window cap is added
in Phase 5 when it becomes relevant.

`send_message(client, history, user_message)` is the core abstraction: it mutates
`history` in place, keeps the call site simple, and is easy to test with a mocked client.
