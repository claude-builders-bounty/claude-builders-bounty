#!/usr/bin/env python3
"""
Validate an n8n workflow JSON against the *official* structural rules that
n8n enforces on import (mirrors packages/workflow/src/workflow-structure-validation.ts):

  - nodes: list of {name(>=1), type(>=1), position:[num,num], ...}
  - connections: {sourceName: {main: [[{node,type,index} | null]]}}
  - no duplicate node names / ids
  - every connection source & target must reference an existing node
"""
import json
import sys
from collections import Counter


def validate(wf):
    errs = []
    nodes = wf.get("nodes")
    conns = wf.get("connections")
    if not isinstance(nodes, list) or not nodes:
        errs.append("nodes: must be a non-empty list")
        nodes = []
    if not isinstance(conns, dict):
        errs.append("connections: must be an object")
        conns = {}

    names, ids = [], []
    for i, n in enumerate(nodes):
        p = f"nodes[{i}]"
        if not isinstance(n, dict):
            errs.append(f"{p}: not an object")
            continue
        if not isinstance(n.get("name"), str) or not n["name"]:
            errs.append(f"{p}.name: required non-empty string")
        else:
            names.append(n["name"])
        if not isinstance(n.get("type"), str) or not n["type"]:
            errs.append(f"{p}.type: required non-empty string")
        pos = n.get("position")
        if not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(x, (int, float)) for x in pos)):
            errs.append(f"{p}.position: must be [number, number]")
        if "id" in n and isinstance(n["id"], str):
            ids.append(n["id"])

    for name, c in Counter(names).items():
        if c > 1:
            errs.append(f"duplicate node name: {name!r} ({c}x)")
    for nid, c in Counter(ids).items():
        if c > 1:
            errs.append(f"duplicate node id: {nid!r} ({c}x)")

    known = set(names)
    for src, types in conns.items():
        if src not in known:
            errs.append(f"connections source {src!r} is not a node")
        if not isinstance(types, dict):
            errs.append(f"connections[{src!r}]: must be an object")
            continue
        for conn_type, buckets in types.items():
            if not isinstance(buckets, list):
                errs.append(f"connections[{src!r}][{conn_type!r}]: must be a list")
                continue
            for bi, bucket in enumerate(buckets):
                if bucket is None:
                    continue
                if not isinstance(bucket, list):
                    errs.append(f"connections[{src!r}][{conn_type!r}][{bi}]: must be list or null")
                    continue
                for ei, entry in enumerate(bucket):
                    if not isinstance(entry, dict):
                        errs.append(f"connections[{src!r}][{conn_type!r}][{bi}][{ei}]: not an object")
                        continue
                    if entry.get("node") not in known:
                        errs.append(f"connections target {entry.get('node')!r} is not a node")
                    if not isinstance(entry.get("type"), str) or not entry["type"]:
                        errs.append(f"connection entry missing type at {src}->{entry.get('node')}")
                    if not isinstance(entry.get("index"), int):
                        errs.append(f"connection entry missing int index at {src}->{entry.get('node')}")
    return errs, nodes, conns


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "weekly-github-summary.json"
    wf = json.load(open(path, encoding="utf-8"))
    errs, nodes, conns = validate(wf)
    if errs:
        print(f"❌ {path}: {len(errs)} issue(s)")
        for e in errs:
            print("   -", e)
        return 1
    print(f"✅ {path}: structure OK — {len(nodes)} nodes, {len(conns)} connection sources")
    # extra sanity: report node types + whether a trigger exists
    types = [n["type"] for n in nodes]
    triggers = [t for t in types if "trigger" in t.lower()]
    print(f"   nodes: {len(nodes)} | triggers: {len(triggers)} ({triggers or 'NONE'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
