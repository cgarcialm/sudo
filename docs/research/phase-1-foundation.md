# Research: Foundation (Phase 1)

## Problem

Before writing a single line of Sudo's logic, we need a reproducible environment that:
1. Runs Python + the Anthropic SDK
2. Matches the target hardware (Raspberry Pi 4, ARM64)
3. Works on a Mac during development without needing the Pi present

## Research

The Pi runs a 64-bit ARM OS (`linux/arm64`). Code that works on a Mac (`darwin/arm64` or
`darwin/amd64`) can silently fail on the Pi due to platform-specific packages, native
extensions (e.g. `cairosvg` → `cairo`), or OS-level differences.

Docker solves this: a container built with `--platform linux/arm64` on a Mac (via QEMU
emulation through Docker Desktop) produces an image that runs identically on the Pi.
The same `run.sh` script that developers use locally becomes the deployment artifact.

Alternatives considered:
- **Develop directly on Pi over SSH**: requires the Pi to be present and connected;
  slow edit/test loop; no reproducibility guarantee
- **Test on Mac, deploy to Pi ad hoc**: fast locally but no guarantee the Pi environment
  matches; system package differences often surface at deploy time
- **Virtual machine (QEMU standalone)**: more overhead, worse developer experience than
  Docker

## Options

### Option A: Native Mac development, deploy to Pi manually
- Pro: no Docker overhead, fast iteration locally
- Con: environment drift; Pi-specific failures only discovered at deploy time

### Option B: ARM64 Docker on Mac
- Pro: identical environment; CI-ready from day one; `docker build` is the deploy artifact
- Con: QEMU emulation adds some overhead; requires Docker Desktop

### Option C: Cross-compile for ARM64 without Docker
- Pro: native speed
- Con: complex toolchain; not idiomatic for Python projects

## Decision

**Option B: ARM64 Docker on Mac.**

A single `Dockerfile` + `run.sh` gives us a reproducible, Pi-identical environment on day
one. The QEMU overhead is acceptable — Sudo is I/O bound (API calls, pygame), not CPU
bound. The same image can be pushed to a registry and pulled on the Pi directly.

`ANTHROPIC_API_KEY` is passed via environment variable — never baked into the image.
