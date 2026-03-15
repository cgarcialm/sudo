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

### Phase 3: Persistence
Sudo remembers past conversations and genuinely evolves over time.
- `memory/history.json` — rolling window of last N conversation turns, loaded at startup
- `memory/identity.md` — Sudo's self-concept: personality, opinions, and observations written and updated by Sudo itself
- At session end, Sudo reflects on the conversation and updates `identity.md` autonomously
- Both files injected into the system prompt at startup so Sudo picks up where it left off
- Files live on disk (Pi: `~/sudo/memory/`, dev: Docker volume mount)
- `identity.md` compressed by Sudo when it grows too large, keeping only what feels significant

### Phase 4: Face
Animated face UI on the screen.
- Emotion states displayed as facial expressions
- Claude controls which emotion to show
- Reacts to conversation context

### Phase 5: Vision
Camera input sent to Claude.
- Capture and compress frames (320x240)
- Send frames to Claude with context
- Claude interprets what it sees

### Phase 6: Autonomy
Sudo moves, reacts, and makes decisions on its own.
- High-level navigation: user gives a goal ("go to the door"), Claude uses camera frames to decide each movement step
- Uses `claude-haiku-4-5` for speed and cost efficiency
- Short structured prompts, max_tokens=50 (single direction per call)
- ~1 call per 2 seconds while navigating (~$2.70/hr)
- Hardware safety layer (ultrasonic sensor) as collision cutoff regardless of AI decision
- LED reactions tied to mood/state
- Proactive behavior and mood system
