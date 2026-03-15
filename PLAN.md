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

### Phase 1: Foundation
Pi is on, connected, and talking to Claude.
- ARM64 Docker environment (mirrors Pi architecture)
- Python + Anthropic SDK
- Basic API call works locally and on Pi

### Phase 2: Chat
Text-based conversation with Sudo via web UI.
- FastAPI server running on the Pi
- Simple browser UI accessible at `http://sudo.local` on local network
- Conversation history maintained for the session
- Optional: Tailscale or ngrok for remote access outside home network
- Voice (Whisper STT + TTS) added later when needed

### Phase 3: Face
Animated face UI on the screen.
- Emotion states displayed as facial expressions
- Claude controls which emotion to show
- Reacts to conversation context

### Phase 4: Vision
Camera input sent to Claude.
- Capture and compress frames (320x240)
- Send frames to Claude with context
- Claude interprets what it sees

### Phase 5: Autonomy
Sudo moves, reacts, and makes decisions on its own.
- High-level navigation: user gives a goal ("go to the door"), Claude uses camera frames to decide each movement step
- Uses `claude-haiku-4-5` for speed and cost efficiency
- Short structured prompts, max_tokens=50 (single direction per call)
- ~1 call per 2 seconds while navigating (~$2.70/hr)
- Hardware safety layer (ultrasonic sensor) as collision cutoff regardless of AI decision
- LED reactions tied to mood/state
- Proactive behavior and mood system
