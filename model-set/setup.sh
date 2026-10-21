#!/usr/bin/env bash
# Local LLM Model Set - macOS / Linux setup
#
# What this does, in order, with nothing hidden:
#   1. Checks Docker is installed and running.
#   2. Starts the hardened Ollama container (loopback only - see
#      docker-compose.yml).
#   3. Pulls the model bundle you chose (default: "starter" = Qwen3 4B).
#   4. Prints the installed digests so you can record / verify them.
#
# It never asks for sudo, never changes firewall rules, and never sends
# anything anywhere except the model downloads from the official Ollama
# registry over TLS.
set -euo pipefail
cd "$(dirname "$0")"

BUNDLE="${1:-starter}"

command -v docker >/dev/null 2>&1 || {
  echo "Docker is required. Install Docker Desktop / Engine first: https://docs.docker.com/get-docker/"
  exit 1
}
docker info >/dev/null 2>&1 || {
  echo "Docker is installed but not running. Start it, then re-run ./setup.sh"
  exit 1
}

echo "==> Starting the local runtime (loopback only: 127.0.0.1:11434)"
docker compose up -d ollama

echo "==> Waiting for the runtime to answer"
for i in $(seq 1 30); do
  if curl -fs http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then break; fi
  sleep 2
  [ "$i" = "30" ] && { echo "Runtime did not come up. Check: docker compose logs ollama"; exit 1; }
done

echo "==> Pulling bundle: $BUNDLE"
python3 - "$BUNDLE" <<'PYEOF'
import json, subprocess, sys
bundle = sys.argv[1]
with open("models.json") as fh:
    manifest = json.load(fh)
bundles = manifest["recommended_bundles"]
if bundle not in bundles:
    raise SystemExit(f"Unknown bundle {bundle!r}. Choose from: {', '.join(bundles)}")
by_id = {m["id"]: m for m in manifest["models"]}
for mid in bundles[bundle]:
    tag = by_id[mid]["ollama_tag"]
    print(f"--> {by_id[mid]['display_name']} ({tag})")
    subprocess.run(["docker", "exec", "local-llm-ollama", "ollama", "pull", tag], check=True)
PYEOF

echo
echo "==> Installed models and digests (save these to verify later):"
python3 llm.py list

echo
echo "Done. Talk to your model:"
echo "  python3 llm.py chat qwen3-4b \"Write a haiku about local AI\""
echo "Optional private chat UI (auth on, signup off, loopback only):"
echo "  docker compose --profile ui up -d   then open http://127.0.0.1:3000"
echo "Stop everything:  docker compose down"
