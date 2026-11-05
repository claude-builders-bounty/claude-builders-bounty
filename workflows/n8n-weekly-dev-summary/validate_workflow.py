#!/usr/bin/env python3
"""Validate an n8n workflow JSON: structure + connection integrity (stdlib only)."""
import json
import sys
from pathlib import Path

REQUIRED = ("parameters", "id", "name", "type", "typeVersion", "position")


def main(path="workflow.json"):
    wf = json.loads(Path(path).read_text())
    errs = []
    names = set()
    for n in wf.get("nodes", []):
        for k in REQUIRED:
            if k not in n:
                errs.append(f"node {n.get('name','?')} missing '{k}'")
        names.add(n.get("name"))
        if not str(n.get("type", "")).startswith("n8n-nodes-base."):
            errs.append(f"node {n.get('name')} has non-core type {n.get('type')}")
    if not any("trigger" in str(n.get("type")).lower() for n in wf.get("nodes", [])):
        errs.append("no trigger node found")
    for src, out in wf.get("connections", {}).items():
        if src not in names:
            errs.append(f"connection from unknown node '{src}'")
        for branch in out.get("main", []):
            for c in branch:
                if c.get("node") not in names:
                    errs.append(f"connection to unknown node '{c.get('node')}'")
    if errs:
        print("INVALID:")
        [print(" -", e) for e in errs]
        return 1
    print(f"OK: {len(wf['nodes'])} nodes, {len(wf.get('connections', {}))} connections, trigger present")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
