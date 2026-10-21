# Local LLM Model Set

**Small language models that run entirely on your own machine — private by design, hardened by default, free to download.**

No accounts. No API keys. No cloud. Your prompts never leave your computer.

This repo is a curated *set* — the models worth having at small sizes, the hardened runtime to serve them, one-command installers for Windows, macOS, and Linux, and a dependency-free command-line client. It ships configuration and tooling only; model weights download from the official Ollama registry on your machine, under their publishers' licenses.

## The set

| Model | Size | Best at | License |
|---|---|---|---|
| **Qwen3 4B Instruct** | ~2.6 GB | Daily driver: chat, writing, summaries | Apache-2.0 |
| Qwen3 1.7B | ~1.4 GB | Speed: classification, routing, old laptops | Apache-2.0 |
| Llama 3.2 3B Instruct | ~2.0 GB | Instruction following, tiny footprint | Llama 3.2 Community |
| Phi-4 Mini 3.8B | ~2.5 GB | Reasoning and math per parameter | MIT |
| Gemma 3 4B | ~3.3 GB | Text **and image** understanding | Gemma Terms |
| Qwen2.5-Coder 3B | ~1.9 GB | Code completion and explanation | Apache-2.0 |
| Nomic Embed Text | ~0.3 GB | Embeddings for local search / RAG | Apache-2.0 |

Full specs, hardware needs, and bundle definitions live in [`models.json`](models.json) and [`docs/MODELS.md`](docs/MODELS.md). Bundles: `starter` (just the daily driver), `everyday`, `coder`, and `full_set` (~14 GB total).

## Quick start

You need [Docker](https://docs.docker.com/get-docker/) and Python 3. Nothing else — the client uses only the Python standard library.

**Windows (PowerShell):**
```powershell
git clone https://github.com/tgreaux-lab/Tyler-LLM.git
cd Tyler-LLM
.\setup.ps1            # or .\setup.ps1 -Bundle full_set
python llm.py chat qwen3-4b "Explain how a bill becomes a law, simply"
```

**macOS / Linux:**
```bash
git clone https://github.com/tgreaux-lab/Tyler-LLM.git
cd Tyler-LLM
./setup.sh             # or ./setup.sh full_set
python3 llm.py chat qwen3-4b "Explain how a bill becomes a law, simply"
```

Prefer clicking to typing? An optional chat UI (login required, signups disabled, also loopback-only) starts with `docker compose --profile ui up -d`, then open `http://127.0.0.1:3000`.

## Why "super secure" isn't marketing here

Most local-LLM guides tell you to bind the server to your whole network, disable auth, and pipe model output into tools. This set does the opposite — see [`docs/HARDENING.md`](docs/HARDENING.md) and [`SECURITY.md`](SECURITY.md):

- **Loopback only.** The runtime binds `127.0.0.1` and nothing else. It is unreachable from your LAN and the internet.
- **The client enforces it too.** `llm.py` refuses to talk to any non-loopback address, even if an environment variable or edited config tries to point it elsewhere. Your prompts can't be silently redirected.
- **Least privilege containers.** Every Linux capability dropped, privilege escalation forbidden, idle models unloaded, response sizes capped.
- **No telemetry.** Analytics and phone-home variables are explicitly off in the UI container.
- **The model gets no tools.** No shell, no files, no browsing. Output is treated as untrusted text — displayed, never executed.
- **Verifiable downloads.** Models pull over TLS from the official registry, and the installer prints each model's digest so you can pin and re-verify what you actually got.
- **Scanned in the open.** GitHub Actions runs secret scanning, dependency/container vulnerability scanning, and manifest validation on every push (see `.github/workflows/security.yml`). If it isn't clean, it doesn't ship quietly.

## Hardware

Any machine with **8 GB RAM** runs the starter bundle comfortably on CPU. **16 GB RAM** (or 8 GB VRAM) runs the full set smoothly, and a modest GPU makes the 4B models feel instant. No GPU is required for anything here.

## Commands

```
python llm.py health     # is the runtime up?
python llm.py bundles    # what bundles exist and how big are they?
python llm.py pull gemma3-4b
python llm.py list       # installed models + digests
python llm.py chat phi4-mini "Prove the square root of 2 is irrational"
```

## Layout

```
models.json            the model manifest (single source of truth)
docker-compose.yml     hardened runtime (Ollama + optional UI)
setup.sh / setup.ps1   one-command installers
llm.py                 dependency-free CLI client (loopback-enforced)
docs/MODELS.md         model-by-model guide
docs/HARDENING.md      the security model, explained
SECURITY.md            reporting + threat model
tests/                 manifest & hardening validation
```

## License

Code in this repository is MIT (see `LICENSE`). **Model weights are not included** and remain under their publishers' licenses listed in `models.json` — check them before commercial use.

Built and maintained by Tyler Greaux. Contributions welcome; security reports especially — see `SECURITY.md`.
