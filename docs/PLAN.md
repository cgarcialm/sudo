# Sudo — Development Plan

Sudo is a Raspberry Pi 4 AI robot powered by Claude.

## Hardware
- Raspberry Pi 4
- Camera
- Microphone
- Speaker
- Screen
- LEDs
- Wheels + motors
- Body mount
- Ambient light sensor (e.g. BH1750)
- Temperature sensor (e.g. DHT22)

## Phases

### Phase 1: Foundation ✅
ARM64 Docker environment working on Mac, ready to deploy to Pi when it arrives.
- ARM64 Docker environment (mirrors Pi architecture) ✅
- Python + Anthropic SDK ✅
- Basic API call works from inside Docker ✅
- Deploy and verify on Pi (pending — Pi arriving soon)

### Phase 2: Chat ✅
Text-based conversation with Sudo via terminal.
- Terminal REPL (`chat.py`) ✅
- Conversation history maintained for the session ✅
- System prompt sets Sudo's personality ✅

### Phase 3: Persistence ✅
Sudo remembers past conversations and genuinely evolves over time.
- `memory/history.json` — rolling window of last 50 conversation turns, loaded at startup ✅
- `memory/identity.md` — Sudo's self-concept: personality, opinions, and observations written and updated by Sudo itself ✅
- At session end, Sudo reflects on the conversation and updates `identity.md` autonomously ✅
- Both files injected into the system prompt at startup so Sudo picks up where it left off ✅
- Files live on disk (Pi: `~/sudo/memory/`, dev: Docker volume mount via `-v ./memory:/app/memory`) ✅
- `identity.md` compressed by Sudo when it grows too large, keeping only what feels significant ✅

### Phase 4: Screen ✅
Sudo has a 16×16 pixel screen it can paint however it wants.
- Every reply includes a 16×16 grid of hex colors Sudo chooses to display ✅
- Sudo decides what to paint — patterns, symbols, abstract art, nothing — it's its own expression ✅
- pygame window renders the grid (each pixel = one colored square) ✅
- Screen persists between replies; Sudo repaints as part of every reply ✅
- `run.sh` is the canonical way to run Sudo (user and tests share it) ✅

### Phase 4b: SVG Screen + Autonomous Expression ✅
Replace the 16×16 pixel grid with SVG — fewer tokens, more expressive, scales to any resolution.
Sudo also gets two independent output channels and learns about both through its system prompt.

- **SVG rendering**: replace pixel grid with SVG output; render via `cairosvg` + pygame ✅
- **Eager display init**: pygame window opens immediately at startup, background event-pump thread keeps it alive ✅
- **Two output channels**: ✅
  - Conversation reply (text, optionally includes `<screen><svg>...</svg></screen>`)
  - Autonomous expression loop: background thread wakes every N seconds, asks Sudo "do you want to express something?", renders SVG if yes
- **System prompt update**: tell Sudo what it is (Pi robot), that it has a physical screen, and that it has both channels available — Sudo learns its own capabilities through context, not hardcoded behavior ✅
- Loops are independent — conversation never blocks expression and vice versa ✅

### Phase 5: Vision
Camera input sent to Claude.
- Capture and compress frames (320x240)
- Send frames to Claude with context
- Claude interprets what it sees

### Phase 6: Body
Sudo gets a sense of its environment through cheap local sensors. The Pi preprocesses everything and sends compressed text summaries — not raw data — to keep token cost low.
- **Audio**: local model classifies ambient sound (quiet/loud, voice present/absent, inside/outside) → one-line summary injected into context
- **Light**: ambient light sensor → time-of-day awareness (day/night/dim)
- **Temperature**: cheap sensor → hot/cold/comfortable
- **Time**: always available, always included
- Principle: process locally, send summaries. "It's quiet, midday, no one in the room." costs almost nothing and gives Sudo a real sense of presence.

### Phase 7: Autonomy
Sudo moves, reacts, and makes decisions on its own.
- High-level navigation: user gives a goal ("go to the door"), Claude uses camera frames to decide each movement step
- Uses `claude-haiku-4-5` for speed and cost efficiency
- Short structured prompts, max_tokens=50 (single direction per call)
- ~1 call per 2 seconds while navigating (~$2.70/hr)
- Hardware safety layer (ultrasonic sensor) as collision cutoff regardless of AI decision
- LED reactions tied to mood/state
- Proactive behavior and mood system
