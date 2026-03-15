# Sudo — Architecture

## Phase 1: Foundation

Docker on Mac proves the setup works before the Pi arrives.

```mermaid
flowchart LR
    subgraph Mac
        Docker["Docker Container\nARM64/Linux"]
        Python["Python\nmain.py"]
        Docker --> Python
    end

    Python -->|HTTPS| API["Anthropic API"]
    API --> Claude
    Claude -->|response| Python
```

## Phase 2: Chat

You chat with Sudo from a terminal. Conversation history persists for the session.

```mermaid
flowchart LR
    User["Terminal\n(chat.py)"]

    subgraph Pi["Raspberry Pi"]
        Chat["chat.py\nREPL loop"]
        History["Conversation History\n(in-memory)"]
        Chat <--> History
    end

    User -->|input| Chat
    Chat -->|HTTPS| API["Anthropic API"]
    API --> Claude
    Claude -->|text response| Chat
    Chat -->|reply| User
```

## Phase 3: Persistence

Sudo's memory and identity survive across sessions. Both are written to disk and loaded at startup.

```mermaid
flowchart LR
    User["Terminal\n(chat.py)"]

    subgraph Pi["Raspberry Pi"]
        Chat["chat.py"]
        subgraph Memory["memory/"]
            History["history.json\n(last N turns)"]
            Identity["identity.md\n(Sudo's self-concept)"]
        end
    end

    Memory -->|load at startup| Chat
    User -->|input| Chat
    Chat -->|HTTPS| API["Anthropic API"]
    API --> Claude
    Claude -->|reply| Chat
    Chat -->|reflect + update on exit| Memory
```

## Phase 4: Screen ✅

Every reply includes a 16×16 pixel grid Sudo paints however it wants. Rendered live via pygame; saved as `memory/screen.png`.

## Phase 4b: SVG Screen + Autonomous Expression ✅

Replaces the pixel grid with SVG. Sudo has two independent output channels: conversation replies (optionally with `<screen><svg>…</svg></screen>`) and an autonomous expression loop that invites Sudo to draw every 30 seconds. The pygame window opens immediately at startup.

```mermaid
flowchart LR
    User["Terminal\n(chat.py)"]

    subgraph Pi["Raspberry Pi"]
        subgraph Threads["chat.py"]
            Main["Main thread\n(event loop + chat)"]
            InputT["Input thread\n(reads stdin)"]
            ExprT["Expression thread\n(every 30s)"]
        end
        Screen["ScreenRenderer\n(screen.py)"]
        PNG["memory/screen.png"]
    end

    InputT -->|queued line| Main
    Main -->|HTTPS stream| API["Anthropic API"]
    API --> Claude
    Claude -->|"text + optional &lt;screen&gt;&lt;svg&gt;"| Main
    Main -->|svg string| Screen
    ExprT -->|HTTPS| API
    Claude -->|"optional &lt;screen&gt;&lt;svg&gt;"| ExprT
    ExprT -->|svg string| Screen
    Screen -->|cairosvg + blit| Window["pygame window"]
    Screen --> PNG
    Main -->|tick 20×/sec| Screen
```

## Phase 5: Vision

Camera frames are sent to Claude. Claude can now see.

```mermaid
flowchart LR
    Camera -->|frame| Pi

    subgraph Pi["Raspberry Pi"]
        Capture["Capture & Compress\nframe"]
    end

    Pi -->|HTTPS\ntext + image| API["Anthropic API"]
    API --> Claude["Claude\n(sees + thinks)"]
    Claude -->|response| Pi
```

## Phase 6: Body

The Pi preprocesses sensor data locally and sends one-line summaries to Claude — not raw data — to keep token cost low.

```mermaid
flowchart LR
    subgraph Sensors
        Mic["Microphone\n(audio classifier)"]
        Light["BH1750\n(ambient light)"]
        Temp["DHT22\n(temperature)"]
        Clock["System clock"]
    end

    subgraph Pi["Raspberry Pi"]
        Summarizer["Local preprocessor\n→ text summary"]
        Chat["chat.py"]
    end

    Sensors -->|raw data| Summarizer
    Summarizer -->|"'It's quiet, midday...'"| Chat
    Chat -->|HTTPS| API["Anthropic API"]
```

## Phase 7: Autonomy

You give Sudo a goal. Claude navigates using the camera.

```mermaid
flowchart TB
    You["You: 'go to the door'"] --> Pi

    subgraph Pi["Raspberry Pi"]
        Loop["Capture frame\n→ send to Claude\n→ execute command\n→ repeat"]
    end

    Camera -->|frame| Loop
    Loop -->|goal + image| API["Anthropic API"]
    API --> Claude["Claude\n(decides next move)"]
    Claude -->|forward / left\nright / stop| Loop

    Loop --> Motors
    Loop --> LEDs
    Loop --> Speaker

    Sensor["Ultrasonic Sensor\n(hardware safety)"] -->|obstacle < threshold\ncut motors| Motors
```

---

The Pi is the hub — everything physical connects to it, and it talks to Claude over the internet.
Claude never touches the hardware directly; it sends back instructions that Python executes locally.
