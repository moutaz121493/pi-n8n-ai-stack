#!/usr/bin/env python3
"""Validate n8n workflow templates for structure and accidental secret/IP leaks."""
from __future__ import annotations

import json
import pathlib
import re
import sys

WORKFLOWS_DIR = pathlib.Path(__file__).resolve().parent.parent / "workflows"
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),  # Tailscale CGNAT IPs
    re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
]


def validate_file(path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    raw = path.read_text(encoding="utf-8")
    for pat in SECRET_PATTERNS:
        if pat.search(raw):
            errors.append(f"Potential secret/private IP matched pattern {pat.pattern!r}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: {exc}"]

    for key in ("name", "nodes", "connections"):
        if key not in data:
            errors.append(f"Missing required top-level key: {key!r}")

    nodes = data.get("nodes", [])
    if not isinstance(nodes, list) or not nodes:
        errors.append("Workflow must contain at least one node")
    else:
        names = {n.get("name") for n in nodes if isinstance(n, dict)}
        for n in nodes:
            for req in ("id", "name", "type", "position"):
                if req not in n:
                    errors.append(f"Node missing {req!r}: {n}")
            # without webhookId n8n registers the webhook under a generated path, not /webhook/<path>
            if n.get("type") == "n8n-nodes-base.webhook" and not n.get("webhookId"):
                errors.append(f"Webhook node {n.get('name')!r} missing 'webhookId'")
        for src in data.get("connections", {}):
            if src not in names:
                errors.append(f"Connection source {src!r} does not match any node name")

    if data.get("active") is True:
        errors.append("Template workflows must be exported with active=false")

    return errors


def main() -> int:
    files = sorted(WORKFLOWS_DIR.glob("*.json"))
    if not files:
        print("No workflow JSON files found.", file=sys.stderr)
        return 1

    failed = 0
    for f in files:
        errs = validate_file(f)
        if errs:
            failed += 1
            print(f"FAIL {f.name}:")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"OK   {f.name}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
