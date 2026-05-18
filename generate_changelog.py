#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()


def category(subject: str) -> str:
    lower = subject.lower()
    if lower.startswith(("feat:", "add:", "added:")) or " add " in lower or " adds " in lower:
        return "Added"
    if lower.startswith(("fix:", "bug:", "bugfix:", "hotfix:")) or " fix " in lower or " fixes " in lower:
        return "Fixed"
    if lower.startswith(("remove:", "removed:", "delete:", "deleted:", "deprecate:", "deprecated:")):
        return "Removed"
    if " remove " in lower or " delete " in lower:
        return "Removed"
    return "Changed"


def main() -> int:
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md")
    try:
        git("rev-parse", "--is-inside-work-tree")
    except subprocess.CalledProcessError:
        print("error: generate_changelog.py must run inside a git repository", file=sys.stderr)
        return 1

    try:
        latest_tag = git("describe", "--tags", "--abbrev=0")
    except subprocess.CalledProcessError:
        latest_tag = ""

    revision_range = f"{latest_tag}..HEAD" if latest_tag else "HEAD"
    since_label = f"since {latest_tag}" if latest_tag else "for full history"
    log = git("log", revision_range, "--no-merges", "--pretty=format:%s|%h")

    buckets = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for line in log.splitlines():
        if not line:
            continue
        subject, _, commit_hash = line.partition("|")
        buckets[category(subject)].append(f"{subject} ({commit_hash})")

    lines = [
        "# Changelog",
        "",
        f"## {dt.date.today().isoformat()} - {since_label}",
        "",
    ]
    for section in ("Added", "Fixed", "Changed", "Removed"):
        lines.append(f"### {section}")
        items = buckets[section]
        lines.extend(f"- {item}" for item in items) if items else lines.append("- No changes.")
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
