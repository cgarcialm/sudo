# Research: SVG Gallery + Exit Fix (Phase 5b)

## Problem

Two small but real issues:

**1. Sudo's expressions are ephemeral.**
Every SVG Sudo draws is rendered to the screen and immediately overwritten by the next
one. `memory/screen.png` captures the latest state but nothing before it. There's no way
to look back at what Sudo drew over a session or across sessions. For a robot with a
visual personality, this felt like a loss.

**2. Sudo hangs on exit.**
After "Saving memories... done." the process wouldn't terminate. Users had to Ctrl+C.
This made the exit experience feel broken, especially on the Pi where sessions often end
with the keyboard shortcut.

## Research

### Gallery

The natural approach is to save each rendered SVG to disk as it's produced. A
date-organized directory structure (`memory/gallery/YYYY-MM-DD/HH-MM-SS.svg`) makes it
easy to browse by day and preserves chronological order. SVG files are tiny, so storage
is not a concern for typical usage.

The feature should be opt-in (`GALLERY_ENABLED=true` env var) — off by default so the Pi
doesn't accumulate files without the user knowing.

### Exit hang

The root cause: `_read_input()` and `_expression_loop()` are daemon threads. Daemon
threads are supposed to be killed automatically when the main thread exits. However,
`_read_input()` is blocked on `input()`, which holds a reference to `sys.stdin`. Python's
shutdown sequence tries to clean up `sys.stdin` but the daemon thread's reference prevents
it, causing a hang.

**Options for the exit hang:**
- `sys.exit()` — triggers normal shutdown; same hang
- `threading.Event` to signal threads to stop — requires polling in `_read_input()`, which
  is blocked on `input()` and can't poll
- `os._exit(0)` — bypasses Python's cleanup entirely; terminates immediately after the
  last line of `run_chat()` completes
- `signal.alarm()` timeout — Unix-only, not portable

`os._exit(0)` is the right choice here. It's placed only in `__main__`, not in
`run_chat()` itself, so tests that call `run_chat()` directly are unaffected.

## Options

### Gallery: Option A — save on every render, always-on
- Pro: no configuration needed
- Con: accumulates files silently; unexpected for users who don't know about it

### Gallery: Option B — opt-in via env var
- Pro: explicit; users who want it enable it; zero impact when disabled
- Con: slightly more code (`if GALLERY_ENABLED:`)

### Exit: Option A — `os._exit(0)` in `__main__`
- Pro: clean, immediate, no residual state; tests unaffected
- Con: skips Python's atexit handlers (none registered; acceptable)

### Exit: Option B — signal threads to stop and join
- Pro: clean shutdown with thread coordination
- Con: `input()` blocks — there's no way to interrupt it portably without `os._exit()`
  or killing the process

## Decision

**Gallery: Option B** — opt-in via `GALLERY_ENABLED=true`. The env var is consistent with
how `SCREEN_FULLSCREEN` and `EXPRESSION_INTERVAL_SECONDS` are configured.

**Exit: Option A** — `os._exit(0)` in `__main__` only. The hang is caused by an
unkillable daemon thread; the only reliable fix is to bypass Python's cleanup. Since no
atexit handlers are registered and all memory is flushed before this line, there's no
data-loss risk.
