#!/usr/bin/env python3
"""Validation for the model set: manifest integrity + hardening invariants.

Runs with the plain standard library:  python3 tests/test_manifest.py
These tests are the repo's promise, in executable form: the manifest is
well-formed, bundles reference real models, and the shipped runtime
config never widens the network exposure the README advertises.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
failures = []


def check(cond: bool, message: str) -> None:
    if not cond:
        failures.append(message)


def main() -> int:
    with open(os.path.join(ROOT, "models.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)

    models = manifest["models"]
    ids = [m["id"] for m in models]
    check(len(ids) == len(set(ids)), "model ids must be unique")
    for m in models:
        check(bool(m["ollama_tag"]), f"{m['id']}: missing ollama_tag")
        check(m["approx_download_gb"] > 0, f"{m['id']}: bad download size")
        check(m["min_ram_gb"] >= 2, f"{m['id']}: unrealistic RAM floor")
        check(bool(m["license"]), f"{m['id']}: license must be recorded")

    for name, bundle in manifest["recommended_bundles"].items():
        for mid in bundle:
            check(mid in ids, f"bundle {name}: unknown model id {mid}")
        check(len(bundle) >= 1, f"bundle {name}: empty bundle")

    compose = open(os.path.join(ROOT, "docker-compose.yml"), encoding="utf-8").read()
    # The loopback invariant: every published port must be 127.0.0.1-bound.
    for line in compose.splitlines():
        s = line.strip()
        if re.match(r'^-\s*"?\d+:\d+', s):
            check(s.startswith('- "127.0.0.1:'), f"non-loopback port mapping: {s}")
    check("no-new-privileges:true" in compose, "containers must forbid privilege escalation")
    check("cap_drop" in compose, "containers must drop capabilities")
    check('ENABLE_SIGNUP: "false"' in compose, "UI signup must be disabled by default")

    llm = open(os.path.join(ROOT, "llm.py"), encoding="utf-8").read()
    check("is_loopback" in llm, "client must enforce loopback endpoints")
    imports = set(re.findall(r"^\s*(?:import|from)\s+([a-zA-Z_][\w]*)", llm, re.M))
    stdlib = set(sys.stdlib_module_names)
    third_party = {i for i in imports if i not in stdlib and i != "__future__"}
    check(not third_party, f"llm.py must be stdlib-only, found: {third_party}")

    if failures:
        print("FAIL")
        for f in failures:
            print(" -", f)
        return 1
    print(f"OK - {len(models)} models, {len(manifest['recommended_bundles'])} bundles, hardening invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
