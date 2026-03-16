# Research: SVG Screen + Autonomous Expression (Phase 4b)

## Problem

Two separate problems addressed together:

**1. The pixel grid is too limited**
16×16 with hex colors requires 256 color tokens per frame. Claude finds it awkward to
author and the output lacks nuance — gradients, text, and complex shapes are impossible.
SVG is natively understood by Claude, scales to 480×320, and can express far more with
far fewer tokens.

**2. Sudo only reacts — it never initiates**
Sudo's screen only changes in response to a user message. Between messages, it's frozen.
A robot that just waits for instructions isn't very alive. Sudo should be able to express
something unprompted — not because it was asked to, but because it wants to.

## Research

### SVG rendering pipeline

`cairosvg` converts SVG → PNG in memory. `pygame` blits the PNG surface to the display.
This adds a native dependency (`libcairo2`, `libpango*`) but produces clean renders at
any resolution. The PNG is also saved to `memory/screen.png` so the current screen state
can be inspected externally and injected back into the system prompt.

### Autonomous expression architecture

The core challenge is threading: pygame is not thread-safe and must only be called from
the main thread. But the expression loop needs to run periodically in the background
without blocking user input.

Solution: a background daemon thread (`_expression_loop`) wakes every
`EXPRESSION_INTERVAL_SECONDS` (default 15), calls the API with a "quiet moment" prompt,
and if Claude returns an SVG, puts it on a `queue.Queue`. The main loop drains the queue
on every tick before waiting for user input — this is the standard producer/consumer
pattern for pygame threading.

**Screen context awareness**: to avoid Sudo drawing something that conflicts with what's
already on screen, `ScreenState` (a thread-safe dataclass) tracks the current SVG. Before
each expression call, `_system_with_screen()` appends the current SVG to the system
prompt so Claude knows what it's showing.

## Options

### SVG rendering: Option A — client-side JS canvas (web UI)
- Pro: rich SVG support natively
- Con: requires a web server; not a terminal app; overkill for a Pi robot

### SVG rendering: Option B — cairosvg → pygame
- Pro: stays in Python, integrates with existing pygame display, ARM64 compatible
- Con: adds native library dependency; build complexity

### Expression loop: Option A — poll on a timer in the main loop
- Pro: single-threaded, no locking
- Con: blocked while waiting for user input (`input()` blocks); expression fires only
  after user interaction

### Expression loop: Option B — background daemon thread + queue
- Pro: truly independent; fires even when user is idle; matches pygame threading model
- Con: requires thread-safe data sharing (`ScreenState` lock, `queue.Queue`)

## Decision

**SVG via cairosvg → pygame.** The rendering fidelity is worth the library dependency.
The ARM64 build is verified in CI via Docker.

**Expression loop as background daemon thread + queue.** The timer-in-main-loop approach
fundamentally can't work because `input()` blocks the main thread. The queue pattern
already proven by pygame's own threading requirements is the right model. Daemon threads
ensure they don't prevent process exit.
