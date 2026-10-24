#!/usr/bin/env python3
"""Tyler-llm agent runtime.

A small, safe agent harness for Tyler-llm (created and trained by Tyler Greaux).
Standard library only. The model runs locally through Ollama on a loopback
endpoint - this client REFUSES any non-loopback address, in code.

Safety model:
  * The model may only call an ALLOW-LIST of tools (below). Anything else it
    asks for is refused and logged back to it as an error result.
  * Tools: calculator (expressions parsed with an AST node allow-list - model
    text is never eval'd), now (date/time), convert (unit conversion),
    file_read / file_write jailed to ./agent-sandbox/ (paths are resolved and
    must stay inside the jail; "..", absolute paths, and symlinks out are
    refused).
  * file_write requires an interactive y/n approval from the human at the
    terminal, every time.
  * No shell tool. No network tools. No exceptions.
  * Bounded: max tool rounds per request, request timeouts, response size cap.

Usage:
  python agent.py                      # interactive chat
  python agent.py "What is 18% of 240?"   # one-shot
  python agent.py --help               # show this help
Environment:
  OLLAMA_HOST    loopback endpoint (default http://127.0.0.1:11434)
  TYLER_MODEL    model name (default tyler-llm)
  AGENT_DATA_DIR where local memory lives (default ./agent-data next to
                 this file; the store is agent-data/memory.json)
  AGENT_MEMORY   set to off/0/no to disable memory (memory is ON by default)

Memory: the runtime keeps a persistent LOCAL per-user memory on this
machine only (see AGENT-MEMORY.md). At the end of a session it asks the
same local model to save durable facts/preferences from your own
statements, and reads them back at the next session start. The model's
weights do not retrain themselves. In chat you can say:
  "what do you remember about me", "forget <item>", "forget everything".
"""

from __future__ import annotations

import ast
import ipaddress
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime

try:  # memory is a sibling module; the agent still runs if it is missing
    import agent_memory
except Exception:  # noqa: BLE001 - missing/broken memory must not break chat
    agent_memory = None

DEFAULT_HOST = "http://127.0.0.1:11434"
TIMEOUT_S = 180
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_TOOL_ROUNDS = 6
SANDBOX = os.path.join(os.getcwd(), "agent-sandbox")
MAX_FILE_BYTES = 256 * 1024

SYSTEM_PROMPT = (
    "You are Tyler-llm, a small local language model created and trained by "
    "Tyler Greaux. You run locally on the user's device. Be helpful, concise, "
    "and honest; if you don't know something, say so. For multi-step problems, "
    "work in a short Plan, do the steps, Verify the result, then Report the "
    "answer briefly. You can use tools by replying with exactly one line: "
    "[TOOL name {json}] and nothing else; the result returns as "
    "[RESULT name {json}]. Tools: calculator {expression}, now {}, "
    "convert {value, from, to}, file_read {path}, file_write {path, content}. "
    "Files live in a sandbox folder; never attempt paths outside it."
)

TOOL_RE = re.compile(r"\[TOOL\s+(\w+)\s+(\{.*?\})\]", re.S)


# ---------------------------------------------------------------- endpoint
def base_url() -> str:
    url = os.environ.get("OLLAMA_HOST", DEFAULT_HOST)
    if not url.startswith("http"):
        url = "http://" + url
    host = url.split("://", 1)[1].split(":")[0].split("/")[0]
    if host != "localhost":
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            raise SystemExit(f"Refusing non-loopback endpoint host: {host!r}. "
                             "Tyler-llm agent only talks to your own machine.")
        if not ip.is_loopback:
            raise SystemExit(f"Refusing non-loopback endpoint: {host}. "
                             "Tyler-llm agent only talks to your own machine.")
    return url.rstrip("/")


def chat(messages: list[dict], model: str) -> str:
    body = {"model": model, "stream": False, "messages": messages,
            "options": {"temperature": 0.4, "num_predict": 1024}}
    req = urllib.request.Request(base_url() + "/api/chat",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            raw = resp.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.URLError as exc:
        raise SystemExit(f"Cannot reach the local runtime at {base_url()} ({exc}). "
                         "Is Ollama running with the tyler-llm model installed?")
    if len(raw) > MAX_RESPONSE_BYTES:
        raise SystemExit("Response exceeded the size cap; aborted.")
    data = json.loads(raw.decode("utf-8"))
    text = data.get("message", {}).get("content", "")
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


# ---------------------------------------------------------------- tools
_BINOPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
           ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
           ast.FloorDiv: lambda a, b: a // b, ast.Mod: lambda a, b: a % b,
           ast.Pow: lambda a, b: a ** b}
_UNOPS = {ast.UAdd: lambda a: +a, ast.USub: lambda a: -a}
_FUNCS = {"sqrt": math.sqrt, "abs": abs, "round": round, "min": min, "max": max}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNOPS:
        return _UNOPS[type(node.op)](_eval_node(node.operand))
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in _FUNCS and not node.keywords):
        return _FUNCS[node.func.id](*[_eval_node(a) for a in node.args])
    raise ValueError("expression element not allowed")


def tool_calculator(args: dict) -> dict:
    expr = str(args.get("expression", ""))[:200]
    tree = ast.parse(expr, mode="eval")
    value = _eval_node(tree)
    if isinstance(value, float) and value == int(value):
        value = int(value)
    return {"value": value}


def tool_now(args: dict) -> dict:
    return {"datetime": datetime.now().astimezone().isoformat(timespec="seconds")}


_CONV = {  # unit -> (dimension, factor to base SI-ish unit)
    "km": ("length", 1000.0), "mi": ("length", 1609.34), "m": ("length", 1.0),
    "ft": ("length", 0.3048), "cm": ("length", 0.01), "in": ("length", 0.0254),
    "kg": ("mass", 1.0), "lb": ("mass", 0.453592), "g": ("mass", 0.001),
    "oz": ("mass", 0.0283495), "l": ("volume", 1.0), "gal": ("volume", 3.78541),
    "ml": ("volume", 0.001),
}


def tool_convert(args: dict) -> dict:
    v = float(args["value"]); frm = str(args["from"]).lower(); to = str(args["to"]).lower()
    if frm in ("c", "f") or to in ("c", "f"):
        if frm == "c" and to == "f":
            out = v * 9 / 5 + 32
        elif frm == "f" and to == "c":
            out = (v - 32) * 5 / 9
        elif frm == to:
            out = v
        else:
            raise ValueError("temperature conversion needs c and f")
        return {"value": round(out, 4), "unit": to}
    if frm not in _CONV or to not in _CONV:
        raise ValueError(f"unknown unit in {frm}->{to}")
    d1, f1 = _CONV[frm]; d2, f2 = _CONV[to]
    if d1 != d2:
        raise ValueError(f"cannot convert {d1} to {d2}")
    return {"value": round(v * f1 / f2, 4), "unit": to}


def _jail(path: str) -> str:
    os.makedirs(SANDBOX, exist_ok=True)
    full = os.path.realpath(os.path.join(SANDBOX, path))
    root = os.path.realpath(SANDBOX)
    if full != root and not full.startswith(root + os.sep):
        raise ValueError("path outside sandbox")
    return full


def tool_file_read(args: dict) -> dict:
    full = _jail(str(args.get("path", "")))
    with open(full, "r", encoding="utf-8") as fh:
        content = fh.read(MAX_FILE_BYTES)
    return {"ok": True, "path": args.get("path"), "content": content}


def tool_file_write(args: dict, approve) -> dict:
    rel = str(args.get("path", ""))
    content = str(args.get("content", ""))
    full = _jail(rel)
    if not approve(rel, content):
        return {"ok": False, "error": "write not approved by user"}
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content[:MAX_FILE_BYTES])
    return {"ok": True, "path": rel, "bytes": len(content.encode("utf-8"))}


TOOLS = {"calculator": tool_calculator, "now": tool_now, "convert": tool_convert,
         "file_read": tool_file_read, "file_write": tool_file_write}


def run_tool(name: str, args: dict, approve) -> dict:
    if name not in TOOLS:
        return {"ok": False, "error": f"tool {name!r} is not available"}
    try:
        if name == "file_write":
            return TOOLS[name](args, approve)
        return TOOLS[name](args)
    except Exception as exc:  # tools report errors; they never crash the agent
        return {"ok": False, "error": str(exc)[:200]}


# ---------------------------------------------------------------- memory
def memory_enabled() -> bool:
    if agent_memory is None:
        return False
    return os.environ.get("AGENT_MEMORY", "on").strip().lower() not in (
        "off", "0", "no", "false")


def open_memory_store():
    """Load the local memory store, or None when memory is off/unavailable."""
    if not memory_enabled():
        return None
    try:
        return agent_memory.MemoryStore()
    except Exception:  # noqa: BLE001 - a bad store must never break chat
        return None


def system_prompt_with_memory(store) -> str:
    if store is None:
        return SYSTEM_PROMPT
    block = store.prompt_block()
    return SYSTEM_PROMPT + ("\n\n" + block if block else "")


def learn_from_session(messages: list[dict], store, model: str) -> None:
    """End-of-session hook: extract durable user facts into the store.
    Failures are silent by design - leaving a chat must never crash."""
    if store is None:
        return
    try:
        saved = agent_memory.extract_and_store(messages, store, chat, model)
    except Exception:  # noqa: BLE001
        return
    if saved:
        print(f"[agent] Saved {saved} new "
              f"{'memory' if saved == 1 else 'memories'} to local memory "
              f"({store.path}).")


# ---------------------------------------------------------------- agent loop
def agent_turn(messages: list[dict], model: str, approve) -> str:
    for _ in range(MAX_TOOL_ROUNDS):
        reply = chat(messages, model)
        m = TOOL_RE.search(reply)
        if not m:
            messages.append({"role": "assistant", "content": reply})
            return reply
        name = m.group(1)
        try:
            args = json.loads(m.group(2))
        except json.JSONDecodeError:
            args = {}
            result = {"ok": False, "error": "tool arguments were not valid JSON"}
        else:
            result = run_tool(name, args, approve)
        messages.append({"role": "assistant", "content": f"[TOOL {name} {json.dumps(args)}]"})
        messages.append({"role": "user", "content": f"[RESULT {name} {json.dumps(result)}]"})
    return chat(messages, model)


HELP = (__doc__ or "").strip()


def main(argv: list[str]) -> int:
    if len(argv) > 1 and argv[1] in ("--help", "-h", "help"):
        print(HELP)
        return 0
    model = os.environ.get("TYLER_MODEL", "tyler-llm")
    store = open_memory_store()

    def approve(path: str, content: str) -> bool:
        print(f"\n[agent] The model wants to WRITE {len(content)} chars to sandbox file: {path}")
        print("[agent] Content preview:", content[:200].replace("\n", " "))
        return input("[agent] Approve this write? [y/N] ").strip().lower() == "y"

    if len(argv) > 1:
        text = " ".join(argv[1:])
        if store is not None:
            reply = agent_memory.handle_memory_command(text, store)
            if reply is not None:
                print(reply)
                return 0
        msgs = [{"role": "system", "content": system_prompt_with_memory(store)},
                {"role": "user", "content": text}]
        print(agent_turn(msgs, model, approve))
        learn_from_session(msgs, store, model)
        return 0
    print("Tyler-llm agent (local, loopback only). Ctrl+C or 'exit' to quit.")
    if store is not None:
        print("[agent] Local memory is ON "
              f"({store.path}). Say 'what do you remember about me', "
              "'forget <item>', or 'forget everything'.")
    msgs = [{"role": "system", "content": system_prompt_with_memory(store)}]
    while True:
        try:
            user = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            learn_from_session(msgs, store, model)
            return 0
        if user.lower() in ("exit", "quit"):
            learn_from_session(msgs, store, model)
            return 0
        if not user:
            continue
        if store is not None:
            reply = agent_memory.handle_memory_command(user, store)
            if reply is not None:
                print("\ntyler-llm>", reply)
                continue
        msgs.append({"role": "user", "content": user})
        print("\ntyler-llm>", agent_turn(msgs, model, approve))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
