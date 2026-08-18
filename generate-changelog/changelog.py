#!/usr/bin/env python3
"""Build CHANGELOG.md from git commits since the latest tag."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(p.stderr.strip() or f"git {' '.join(args)} failed")
    return p.stdout


def last_tag() -> str | None:
    p = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True)
    if p.returncode != 0:
        return None
    return p.stdout.strip() or None


def commits_since(tag: str | None) -> list[str]:
    rng = f"{tag}..HEAD" if tag else "HEAD"
    log = git("log", rng, "--pretty=format:%s")
    return [ln.strip() for ln in log.splitlines() if ln.strip()]


def category(msg: str) -> str:
    lower = msg.lower()
    m = re.match(r"^(feat|fix|chore|docs|refactor|perf|test|style|revert)(\(.+\))?(!)?:\s*(.+)$", msg, re.I)
    if m:
        kind = m.group(1).lower()
        breaking = bool(m.group(3)) or "breaking" in lower
        rest = m.group(4)
        if kind == "feat" or breaking:
            return "Added"
        if kind == "fix":
            return "Fixed"
        if kind in ("refactor", "perf", "chore", "docs", "style", "test"):
            return "Changed"
        if kind == "revert" or rest.startswith("remove") or rest.startswith("drop"):
            return "Removed"
    if re.search(r"\b(fix|bug|hotfix|patch)\b", lower):
        return "Fixed"
    if re.search(r"\b(add|added|feat|feature|introduce|support)\b", lower):
        return "Added"
    if re.search(r"\b(remove|removed|drop|delete|deprecate)\b", lower):
        return "Removed"
    return "Changed"


def render(groups: dict[str, list[str]], tag: str | None) -> str:
    heading = f"## {date.today().isoformat()}"
    if tag:
        heading += f" (since `{tag}`)"
    else:
        heading += " (all commits; no tags yet)"
    parts = [heading, ""]
    for section in ("Added", "Fixed", "Changed", "Removed"):
        items = groups.get(section) or []
        if not items:
            continue
        parts.append(f"### {section}")
        parts.append("")
        for item in items:
            parts.append(f"- {item}")
        parts.append("")
    if len(parts) == 2:
        parts.append("No commits in range.")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Write CHANGELOG.md from git history since last tag")
    parser.add_argument("-o", "--output", default="CHANGELOG.md")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    git("rev-parse", "--is-inside-work-tree")
    tag = last_tag()
    msgs = commits_since(tag)
    groups: dict[str, list[str]] = defaultdict(list)
    for msg in msgs:
        groups[category(msg)].append(msg)
    text = render(groups, tag)
    if args.stdout:
        sys.stdout.write(text)
        return 0
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"Wrote {args.output} ({len(msgs)} commits, since {tag or 'beginning'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
