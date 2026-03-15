# Sudo

A Raspberry Pi 4 AI robot powered by Claude. Sudo can see, talk, move, and make decisions autonomously.

## Hardware
- Raspberry Pi 4
- Camera
- Microphone + Speaker
- Screen
- LEDs
- Wheels + motors
- Body mount

## Getting Started

### Prerequisites
- Docker (for local development on Mac/Linux ARM64)
- An [Anthropic API key](https://console.anthropic.com)

### Run locally with Docker

```bash
cp .env.example .env
# Add your API key to .env

docker build --platform linux/arm64 -t sudo .
docker run --rm --env-file .env sudo
```

### Run on the Pi

```bash
git clone https://github.com/cgarcialm/sudo.git
cd sudo
cp .env.example .env
# Add your API key to .env

docker build -t sudo .
docker run --rm --env-file .env sudo
```

## Docs

- [Development Plan](docs/PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
