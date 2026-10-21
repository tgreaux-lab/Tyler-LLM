# Security Policy

## The threat model this project is built against

A local LLM stack has four realistic enemies, and this repo is designed
against each of them explicitly:

1. **Exposure.** The most common way "local" AI leaks is a server bound to
   `0.0.0.0` with no auth — reachable by every device on the coffee-shop
   Wi-Fi, or forwarded to the internet by a helpful router feature.
   *Defense:* loopback-only bindings everywhere, and a client that
   refuses non-loopback endpoints in code, not just in config.

2. **Supply chain.** Downloads that aren't what they claim to be.
   *Defense:* models come only from the official Ollama registry over
   TLS; installers print content digests for pinning and later
   verification; the repo's own CI runs secret scanning (Gitleaks) and
   vulnerability scanning (Trivy) on every push; the Python client has
   zero third-party dependencies.

3. **The model itself.** Model output is untrusted text. A poisoned or
   prompt-injected answer must never become an action.
   *Defense:* the client gives models no tools, no shell, no file or
   network access beyond answering. Output is displayed, never executed.
   If you extend this stack with tool-calling, sandbox it and keep a
   human in the loop for anything destructive — read
   `docs/HARDENING.md` first.

4. **Your own data.** Prompts, chats, and embeddings are yours.
   *Defense:* nothing in this stack phones home; telemetry variables are
   pinned off; chat history lives in a Docker volume on your disk that
   you can wipe with `docker compose down -v`.

## Reporting a vulnerability

Open a GitHub security advisory on this repository (Security tab →
Report a vulnerability) rather than a public issue. You'll get a
response within a few days. Fixes to the hardening defaults ship as
priority releases, and reporters are credited unless they prefer not
to be.

## Supported versions

The `main` branch is the supported version. Pin a commit or tag if you
need reproducibility, and re-check model digests after any update.
