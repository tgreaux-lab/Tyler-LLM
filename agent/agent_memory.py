#!/usr/bin/env python3
"""Persistent local per-user memory for the Tyler-llm agent runtime.

Standard library only. Used by agent.py; it can also be imported on its own.

Design:
  * The store is one plain JSON file on the user's own machine:
        <data dir>/memory.json
    The data dir defaults to ./agent-data/ next to this file (the runtime),
    and can be overridden with the AGENT_DATA_DIR environment variable.
  * The file is human-inspectable: a JSON list of items, each
        {"id": "...", "text": "...", "learned_at": "<ISO time>",
         "source": "user"}
  * Memory is learned ONLY from the user's own statements. Extraction is
    built from user turns only - assistant replies and tool results are
    never included (see user_turns_from_messages), so tool output and web
    content can never enter the store through extraction.
  * Nothing leaves the machine: extraction uses the same loopback model
    endpoint as the chat itself (agent.py enforces loopback in code).
    There is no telemetry and no other network use.
  * The model's weights do NOT retrain themselves. Memory lives in this
    runtime file and is read back into the prompt at session start.

Commands handled deterministically by the runtime (no model call):
  "what do you remember about me"  -> list the store
  "forget <item>"                  -> remove matching items only
  "forget everything"              -> clear the store
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone

MAX_MEMORY_ITEMS = 500
MAX_MEMORY_TEXT = 500

# Phrases that ask the runtime to list the store. Matched loosely:
# case-insensitive, surrounding punctuation / filler ignored.
_LIST_PHRASES = (
    "what do you remember about me",
    "what do you remember",
    "what have you remembered about me",
    "what have you remembered",
    "show me what you remember",
    "list your memories",
    "list what you remember",
)


def data_dir() -> str:
    """Agent data directory: $AGENT_DATA_DIR, else ./agent-data by this file."""
    override = os.environ.get("AGENT_DATA_DIR", "").strip()
    if override:
        return override
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent-data")


def memory_path(directory: str | None = None) -> str:
    return os.path.join(directory or data_dir(), "memory.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).strip(" .!?\"'")


# ---------------------------------------------------------------- store
class MemoryStore:
    """A JSON-file-backed list of memory items. Bad files never crash."""

    def __init__(self, path: str | None = None, directory: str | None = None):
        self.path = path or memory_path(directory)
        self.items: list[dict] = []
        self.load()

    def load(self) -> list[dict]:
        self.items = []
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, ValueError):
            return self.items  # missing or unreadable file = empty store
        if isinstance(raw, dict):  # tolerate {"memories": [...]} files
            raw = raw.get("memories", [])
        if isinstance(raw, list):
            for entry in raw:
                if isinstance(entry, dict) and str(entry.get("text", "")).strip():
                    self.items.append({
                        "id": str(entry.get("id") or uuid.uuid4().hex[:12]),
                        "text": str(entry["text"]).strip()[:MAX_MEMORY_TEXT],
                        "learned_at": str(entry.get("learned_at") or _now_iso()),
                        "source": "user",
                    })
        return self.items

    def save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.items, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, self.path)  # atomic-ish: never a half-written store

    def add(self, text: str, replaces: str | None = None) -> dict | None:
        """Add one item. If `replaces` names an existing id, that old item
        is removed first (the user corrected it, so the new value wins)."""
        text = str(text).strip()[:MAX_MEMORY_TEXT]
        if not text:
            return None
        if replaces:
            self.items = [it for it in self.items if it["id"] != str(replaces)]
        if any(_norm(it["text"]) == _norm(text) for it in self.items):
            return None  # already known; do not duplicate
        item = {"id": uuid.uuid4().hex[:12], "text": text,
                "learned_at": _now_iso(), "source": "user"}
        self.items.append(item)
        del self.items[:-MAX_MEMORY_ITEMS]  # keep the newest, bounded
        self.save()
        return item

    def forget(self, query: str) -> list[dict]:
        """Remove items matching `query`. Returns the removed items.

        Matching is deliberately simple and predictable: case-insensitive,
        an item matches when the query text appears in the item, the item
        appears in the query, or every word of the query appears in it.
        """
        q = _norm(query)
        if not q:
            return []
        words = [w for w in q.split() if len(w) > 2] or q.split()
        removed, kept = [], []
        for it in self.items:
            t = _norm(it["text"])
            if q in t or t in q or all(w in t for w in words):
                removed.append(it)
            else:
                kept.append(it)
        if removed:
            self.items = kept
            self.save()
        return removed

    def clear(self) -> int:
        count = len(self.items)
        self.items = []
        self.save()
        return count

    # ------------------------------------------------------------ display
    def prompt_block(self) -> str:
        """Delimited block injected into the system context at start."""
        if not self.items:
            return ""
        lines = ["What you remember about the user (from their own statements):"]
        lines += [f"- {it['text']}" for it in self.items]
        return "\n".join(lines)

    def listing(self) -> str:
        if not self.items:
            return "I don't have anything saved in memory about you yet."
        lines = ["Here is what I remember about you (from your own statements):"]
        lines += [f"{n}. {it['text']}" for n, it in enumerate(self.items, 1)]
        return "\n".join(lines)


# ---------------------------------------------------------------- commands
def is_memory_command(text: str) -> bool:
    return handle_memory_command(text, None) is not None


def handle_memory_command(text: str, store: MemoryStore | None) -> str | None:
    """Return the runtime's reply if `text` is a memory command, else None.

    Deterministic: no model is consulted. When `store` is None this only
    classifies the text (used to keep commands out of extraction).
    """
    norm = _norm(text)
    if norm in _LIST_PHRASES or norm.startswith("what do you remember"):
        return store.listing() if store is not None else ""
    if norm in ("forget everything", "forget all", "forget all of it",
                "forget everything about me", "clear your memory",
                "clear all memory"):
        if store is None:
            return ""
        count = store.clear()
        return (f"Done - I forgot everything. I removed {count} "
                f"{'item' if count == 1 else 'items'} and my memory is now empty."
                if count else "My memory was already empty - nothing to forget.")
    if norm.startswith("forget "):
        query = norm[len("forget "):].strip()
        if query.startswith("about "):
            query = query[len("about "):].strip()
        if store is None:
            return ""
        removed = store.forget(query)
        if not removed:
            return f"I didn't find anything in memory matching \"{query}\" - I removed nothing."
        gone = "; ".join(it["text"] for it in removed)
        return f"Done - I forgot: {gone}"
    return None


# ---------------------------------------------------------------- extraction
def user_turns_from_messages(messages: list[dict]) -> list[str]:
    """Genuine user statements only, by construction.

    Tool results are fed back into the chat as user-role messages starting
    with "[RESULT" in agent.py - those are tool output, not user speech,
    and are excluded here. Memory commands are excluded too: they are
    instructions to the runtime, not facts to learn.
    """
    turns = []
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = str(msg.get("content", "")).strip()
        if not content or content.startswith("[RESULT") or content.startswith("[TOOL"):
            continue
        if is_memory_command(content):
            continue
        turns.append(content)
    return turns


_EXTRACTION_SYSTEM = (
    "You extract durable facts and preferences about a user from their own "
    "statements, for a local memory file. Reply with JSON only."
)


def build_extraction_prompt(user_turns: list[str], existing: list[dict]) -> str:
    known = "\n".join(f'- id={it["id"]}: {it["text"]}' for it in existing) or "(none)"
    said = "\n".join(f"- {turn}" for turn in user_turns) or "(nothing)"
    return (
        "From the USER STATEMENTS below, extract durable facts and preferences "
        "about the user (for example their name, likes, dislikes, job, plans, "
        "or how they want things done). Rules:\n"
        "- Only facts the user stated about themselves qualify. Ignore "
        "questions, requests, greetings, and anything temporary.\n"
        "- Write each fact as one short sentence in the user's own terms.\n"
        "- If a statement CORRECTS an already-known memory on the same topic, "
        "give the new fact and set \"replaces\" to that memory's id, so the new "
        "value replaces the old one.\n"
        "- If there is nothing durable to save, return an empty list.\n"
        'Reply with ONLY this JSON: {"memories": [{"text": "...", "replaces": null}]}\n\n'
        f"ALREADY KNOWN:\n{known}\n\nUSER STATEMENTS:\n{said}"
    )


def parse_extraction_response(text: str) -> list[dict]:
    """Parse the model's extraction reply defensively.

    Returns a list of {"text": str, "replaces": str|None}. Any malformed
    input - no JSON, wrong shapes, bad entries - yields [] or skips the
    bad entries. This never raises.
    """
    if not text:
        return []
    cleaned = re.sub(r"```(?:json)?", "", str(text)).strip()
    start = min([i for i in (cleaned.find("{"), cleaned.find("[")) if i >= 0],
                default=-1)
    if start < 0:
        return []
    try:
        data, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    except ValueError:
        return []
    if isinstance(data, dict):
        data = data.get("memories", data.get("facts", data.get("items", [])))
    if not isinstance(data, list):
        return []
    out = []
    for entry in data:
        if isinstance(entry, str) and entry.strip():
            out.append({"text": entry.strip()[:MAX_MEMORY_TEXT], "replaces": None})
        elif isinstance(entry, dict) and str(entry.get("text", "")).strip():
            replaces = entry.get("replaces") or entry.get("replaces_id")
            out.append({"text": str(entry["text"]).strip()[:MAX_MEMORY_TEXT],
                        "replaces": str(replaces) if replaces else None})
    return out


def extract_and_store(messages: list[dict], store: MemoryStore,
                      chat_fn, model: str) -> int:
    """End-of-session hook: ask the connected model to extract memories
    from the user turns of `messages` and apply them to `store`.

    `chat_fn` has agent.py's chat() signature: chat_fn(messages, model).
    It is the same loopback endpoint as the chat. Any failure - endpoint
    down, bad JSON, anything - saves nothing extra and never raises.
    Returns the number of items saved.
    """
    turns = user_turns_from_messages(messages)
    if not turns:
        return 0
    prompt = build_extraction_prompt(turns, store.items)
    try:
        reply = chat_fn([{"role": "system", "content": _EXTRACTION_SYSTEM},
                         {"role": "user", "content": prompt}], model)
    except BaseException:  # includes SystemExit from a dead endpoint
        return 0
    saved = 0
    for entry in parse_extraction_response(reply):
        if store.add(entry["text"], replaces=entry["replaces"]):
            saved += 1
    return saved
