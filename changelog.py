#!/usr/bin/env python3
"""Generate CHANGELOG.md from git commits since last tag, categorised into Added/Fixed/Changed/Removed."""
import subprocess, sys, re
from datetime import date

def git(*args):
    try:
        return subprocess.check_output(["git"] + list(args), text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""

def get_commits():
    last_tag = git("describe", "--tags", "--abbrev=0")
    if last_tag:
        raw = git("log", "--no-merges", "--reverse", "--format=%h %s", f"{last_tag}..HEAD")
    else:
        raw = git("log", "--no-merges", "--reverse", "--format=%h %s")
        last_tag = None
    lines = [l for l in raw.split("\n") if l.strip()]
    return lines, last_tag

def categorise(msg):
    # 1) conventional commit: type(scope)!: desc
    m = re.match(r"^([a-zA-Z]+)(\(.*?\))?!?:\s*(.+)", msg)
    if m:
        typ = m.group(1).lower()
        desc = m.group(3)
        if typ == "feat":
            return "Added", desc
        if typ == "fix":
            return "Fixed", desc
        if typ in ("revert","remove"):
            return "Removed", desc
        return "Changed", desc   # refactor, style, test, docs, ci, build, chore, perf, etc.
    # 2) keyword fallback
    low = msg.lower()
    if re.match(r"^(add|added|implement|create)\b", low):
        return "Added", msg
    if re.match(r"^(fix|fixed|patch|bug|repair|correct)\b", low):
        return "Fixed", msg
    if re.match(r"^(remove|delete|drop|revert|deprecate)\b", low):
        return "Removed", msg
    if re.match(r"^(change|update|refactor|improve|bump|upgrade|style|test|doc|ci|build|chore|perf)\b", low):
        return "Changed", msg
    # fallback
    return "Changed", msg

def main():
    commits, last_tag = get_commits()
    buckets = {"Added":[], "Fixed":[], "Changed":[], "Removed":[]}
    for line in commits:
        hsh, _, msg = line.partition(" ")
        if not msg:
            continue
        cat, desc = categorise(msg)
        buckets[cat].append(f"  - {desc} ({hsh})")

    out = ["# Changelog\n"]
    today = date.today().isoformat()
    if last_tag:
        out.append(f"## Unreleased (since {last_tag}) — {today}\n")
    else:
        out.append(f"## Unreleased ({today})\n")
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        if buckets[cat]:
            out.append(f"### {cat}")
            out.extend(buckets[cat])
            out.append("")
    print("\n".join(out))

if __name__ == "__main__":
    main()
