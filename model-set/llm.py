#!/usr/bin/env python3
"""Local LLM Model Set - command line client.

Design rules (security first):
  * Standard library only. Nothing to pip-install, nothing to audit
    beyond this one file.
  * Talks ONLY to a loopback Ollama endpoint. Any non-loopback host is
    refused before a socket is opened - a downloaded config or a stray
    environment variable cannot quietly point your prompts at the
    internet.
  * Prompts are data. This client never executes model output, never
    follows instructions found inside output, and gives the model no
    tools, no shell, and no file access.
  * Hard timeouts and response-size caps on every request.

Usage:
  python llm.py health                 # is the local runtime up?
  python llm.py list                    # models installed locally
  python llm.py pull qwen3-4b           # download a model from models.json
  python llm.py chat qwen3-4b "Explain DNS like I'm five"
  python llm.py bundles                 # show the recommended bundles
"""

from __future__ import annotations

import ipaddress
import json
import os
import sys
import urllib.request
import urllib.error

DEFAULT_HOST = "http://127.0.0.1:11434"
TIMEOUT_S = 120
MAX_RESPONSE_BYTES = 8 * 1024 * 1024  # 8 MB cap on any single response


def base_url() -> str:
    url = os.environ.get("OLLAMA_HOST", DEFAULT_HOST)
    if not url.startswith("http"):
        url = "http://" + url
    host = url.split("://", 1)[1].split(":")[0].split("/")[0]
    _assert_loopback(host)
    return url.rstrip("/")


def _assert_loopback(host: str) -> None:
    """Refuse anything that is not this machine. This is the guardrail
    that keeps prompts local even if OLLAMA_HOST is tampered with."""
    if host in ("localhost",):
        return
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        raise SystemExit(
            f"Refusing non-loopback endpoint host: {host!r}. "
            "This client only talks to your own machine."
        )
    if not ip.is_loopback:
        raise SystemExit(
            f"Refusing non-loopback endpoint: {host}. "
            "This client only talks to your own machine."
        )


def _request(path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url() + path, data=data, headers=headers,
        method="POST" if data else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            body = resp.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Cannot reach the local runtime at {base_url()} ({exc}). "
            "Start it with: docker compose up -d"
        )
    if len(body) > MAX_RESPONSE_BYTES:
        raise SystemExit("Response exceeded the size cap; aborted.")
    return json.loads(body.decode("utf-8"))


def load_manifest() -> dict:
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "models.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def cmd_health() -> None:
    tags = _request("/api/tags")
    models = tags.get("models", [])
    print(f"Runtime OK at {base_url()} - {len(models)} model(s) installed.")


def cmd_list() -> None:
    tags = _request("/api/tags")
    models = tags.get("models", [])
    if not models:
        print("No models installed yet. Try: python llm.py pull qwen3-4b")
        return
    for m in models:
        size_gb = m.get("size", 0) / 1e9
        print(f"{m.get('name', '?'):45s} {size_gb:5.1f} GB  digest {m.get('digest', '')[:16]}...")


def cmd_pull(model_id: str) -> None:
    manifest = load_manifest()
    entry = next((m for m in manifest["models"] if m["id"] == model_id), None)
    if entry is None:
        ids = ", ".join(m["id"] for m in manifest["models"])
        raise SystemExit(f"Unknown model id {model_id!r}. Known ids: {ids}")
    tag = entry["ollama_tag"]
    print(f"Pulling {entry['display_name']} ({tag}, ~{entry['approx_download_gb']} GB)")
    print("Source: the official Ollama registry, over TLS. Verify afterwards with: python llm.py list")
    result = _request("/api/pull", {"name": tag, "stream": False})
    print("Done:", result.get("status", "ok"))


def cmd_chat(model_id: str, prompt: str) -> None:
    manifest = load_manifest()
    entry = next((m for m in manifest["models"] if m["id"] == model_id), None)
    tag = entry["ollama_tag"] if entry else model_id
    result = _request("/api/chat", {
        "model": tag,
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        # Sensible, bounded defaults. Long outputs are a resource risk on
        # small machines, so cap them.
        "options": {"temperature": 0.7, "num_predict": 1024},
    })
    print(result.get("message", {}).get("content", "").strip())


def cmd_bundles() -> None:
    manifest = load_manifest()
    by_id = {m["id"]: m for m in manifest["models"]}
    for name, ids in manifest["recommended_bundles"].items():
        total = sum(by_id[i]["approx_download_gb"] for i in ids)
        print(f"{name:10s} ~{total:4.1f} GB  ->  {', '.join(ids)}")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 0
    cmd = argv[1]
    if cmd == "health":
        cmd_health()
    elif cmd == "list":
        cmd_list()
    elif cmd == "bundles":
        cmd_bundles()
    elif cmd == "pull" and len(argv) == 3:
        cmd_pull(argv[2])
    elif cmd == "chat" and len(argv) >= 4:
        cmd_chat(argv[2], " ".join(argv[3:]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
