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

Pi runs a web server. You chat with Sudo from a browser.

```mermaid
flowchart LR
    User["Your Phone / Mac\n(browser)"]

    subgraph Pi["Raspberry Pi"]
        Server["FastAPI Server"]
        History["Conversation History"]
        Server <--> History
    end

    User -->|http://sudo.local| Server
    Server -->|HTTPS| API["Anthropic API"]
    API --> Claude
    Claude -->|text response| Server
```

Remote access outside home network: TBD

## Phase 3: Face

Claude decides Sudo's emotion, rendered on screen.

```mermaid
flowchart LR
    User["Your Phone / Mac\n(browser)"]

    subgraph Pi["Raspberry Pi"]
        Server["FastAPI Server"]
        Face["Face Renderer"]
    end

    User -->|http://sudo.local| Server
    Server -->|HTTPS| API["Anthropic API"]
    API --> Claude
    Claude -->|text + emotion| Server
    Server --> Face
    Face --> Screen
```

## Phase 4: Vision

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

## Phase 5: Autonomy

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
