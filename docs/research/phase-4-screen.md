# Research: Screen (Phase 4)

## Problem

Sudo is a physical robot with a screen. The screen should be Sudo's own expressive canvas —
not a UI panel, not a status display. Sudo decides what to show. The question is how to
encode that expression: what format does Sudo author, and how does the Pi render it?

## Research

The screen is a 3.5" OSOYOO display running over SPI, driven by pygame on the Pi.
At this phase it was treated as a 16×16 pixel grid — coarse enough to be low-token but
expressive enough for patterns, symbols, and abstract art.

**Encoding options** for what Claude produces:
- **Hex color grid** (e.g. `#ff0000,#000000,...` × 256 values): explicit, low-ambiguity,
  but verbose and brittle to parse
- **JSON array of arrays**: structured, easy to parse, similar token cost
- **Description in natural language**: not renderable without a second interpretation step
- **SVG**: rich, vector, scales to any resolution, well-understood by Claude (later phase)

At Phase 4, the pixel grid approach was chosen for simplicity. SVG came in Phase 4b.

**Rendering stack**: `cairosvg` wasn't yet in scope; `pygame` draws colored rectangles
directly from the parsed grid. Each cell in the 16×16 grid is a fixed-size pygame rect.

## Options

### Option A: 16×16 hex color grid, rendered by pygame
- Pro: simple, deterministic, no additional libraries
- Con: limited expressiveness; verbose token format; doesn't scale to larger displays

### Option B: SVG authored by Claude, rendered by cairosvg → pygame
- Pro: expressive, resolution-independent, concise for complex images
- Con: requires cairosvg (native library, ARM64 build); more complex rendering pipeline

### Option C: ASCII art or text-based display
- Pro: trivial to render
- Con: doesn't use the physical screen's color capabilities; not Sudo's aesthetic

## Decision

**Option A: 16×16 hex color grid, for Phase 4.**

The simplest thing that gives Sudo a real physical screen to express itself on. The pixel
grid is intentionally constrained — Sudo has to work with limits, which is itself
expressive. SVG replaces it in Phase 4b once the rendering pipeline is proven and the
desire for more expressive output is confirmed.
