# Sudo — Architecture

## Phase 1: Foundation

Docker on Mac proves the setup works before the Pi arrives.

```
Your Mac
└── Docker container (ARM64/Linux)
    └── Python (main.py)
        └── HTTPS ──► Anthropic API ──► Claude
                                         │
                  response (text) ◄──────┘
```

## Phase 2: Chat

Pi runs a web server. You chat with Sudo from a browser.

```
Your Phone / Mac
└── Browser ──► http://sudo.local
                      │
               ┌──────▼──────────────┐
               │   Raspberry Pi      │
               │   FastAPI server    │──── HTTPS ───► Anthropic API
               │   conversation      │◄─── response ──    │
               │   history           │                  Claude
               └─────────────────────┘

Remote access (outside home): TBD
```

## Phase 3: Face

Pi drives an animated face on its screen. Claude decides the emotion.

```
Your Phone / Mac
└── Browser ──► http://sudo.local
                      │
               ┌──────▼──────────────┐
               │   Raspberry Pi      │
               │   FastAPI server    │──── HTTPS ───► Anthropic API
               │                     │◄─── text + emotion ──  │
               │   face renderer     │                      Claude
               └──────┬──────────────┘
                      │
                   Screen
               (animated face)
```

## Phase 4: Vision

Camera frames are sent to Claude. Claude can now see.

```
Camera
  │
  ▼
               ┌─────────────────────┐
               │   Raspberry Pi      │
               │                     │──── HTTPS ───► Anthropic API
               │   captures frame    │  (text + image)      │
               │   compresses it     │◄─── response ──    Claude
               │                     │                  (sees + thinks)
               └─────────────────────┘
```

## Phase 5: Autonomy

You give Sudo a goal. Claude uses the camera to navigate, motor by motor.

```
You: "go to the door"
        │
        ▼
               ┌─────────────────────┐
               │   Raspberry Pi      │
  Camera ─────►│                     │──── HTTPS ───► Anthropic API
               │   capture frame     │  (goal + image)      │
               │   send to Claude    │◄─── command ──     Claude
               │   execute command   │    (forward /     (decides
               │   repeat            │    left / right /  next move)
               │                     │     stop)
               └──────┬──────────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
        Motors      LEDs       Speaker
      (movement)  (reaction)  (optional)

Hardware safety: ultrasonic sensor cuts motors if obstacle < threshold,
regardless of what Claude says.
```

---

The Pi is the hub — everything physical connects to it, and it talks to Claude over the internet.
Claude never touches the hardware directly; it sends back instructions that Python executes locally.
