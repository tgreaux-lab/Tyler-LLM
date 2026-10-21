# Hardening guide — what "secure by default" means here

This stack is designed so that the *default* way to run it is also the
*safe* way. Every control below is already applied in the shipped
configuration. This document exists so you can verify that claim instead
of trusting it.

## Network

- Ollama is published on `127.0.0.1:11434` only. Verify it yourself:
  - Windows: `netstat -ano | findstr 11434` should show `127.0.0.1`, never `0.0.0.0`.
  - macOS/Linux: `ss -tlnp | grep 11434` or `lsof -i :11434`.
- The optional web UI is published on `127.0.0.1:3000` only, with
  authentication on and public signup disabled (`ENABLE_SIGNUP=false`).
  Create the first (admin) account immediately after starting it, or
  don't start the UI at all.
- **Never** port-forward 11434 or 3000 on your router. If you truly need
  remote access, use a VPN or Tailscale and an authenticated reverse
  proxy — and understand you are changing the threat model.

## Client

- `llm.py` parses the endpoint before connecting and **refuses any
  non-loopback host**. A copied config, a typo, or a malicious
  `OLLAMA_HOST` value cannot redirect your prompts to someone else's
  server.
- It is standard-library only. `grep "^import" llm.py` is the entire
  dependency audit.
- Every request has a timeout and an 8 MB response cap.

## Containers

- `cap_drop: ALL` and `no-new-privileges` on every service.
- Models unload after 5 idle minutes (`OLLAMA_KEEP_ALIVE`), bounding
  RAM/VRAM use and shrinking the window where a loaded model sits in
  memory.
- Telemetry is pinned off in the UI service: `ANONYMIZED_TELEMETRY`,
  `DO_NOT_TRACK`, and `SCARF_NO_ANALYTICS` are all set.

## Models and downloads

- Models download only from the official Ollama registry, over TLS,
  when *you* run setup or `llm.py pull`.
- After pulling, `llm.py list` prints a digest per model. Save those
  digests somewhere you trust; if a digest ever changes without you
  pulling an update, treat it as an incident.
- This repository ships **no model weights**, so there is nothing
  executable hiding in a clone of this repo beyond the scripts you can
  read in minutes.

## The model is not your friend (operational rules)

- Treat all model output as **untrusted text**. Never pipe it into a
  shell, an interpreter, or a tool without reading it first.
- Don't paste secrets (passwords, keys, private documents you wouldn't
  share) into *any* chat UI that syncs — local models are safe because
  they're local; browser extensions and cloud sync are separate risks.
- If you add tool-calling or agents later: least-privilege tools,
  allow-listed actions, human approval for anything destructive or
  external, and full logging. An LLM with a shell and no guardrails is
  just remote code execution with extra steps.

## Housekeeping

- Update Docker and the images regularly: `docker compose pull && docker compose up -d`.
- Wipe everything (models, UI data, history) with `docker compose down -v`.
- Report anything that looks off — see `SECURITY.md`.
