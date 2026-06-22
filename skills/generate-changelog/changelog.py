#!/usr/bin/env python3
"""Generate CHANGELOG.md from git commits since the last tag."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SECTIONS = ("Added", "Fixed", "Changed", "Removed")

RULES: list[tuple[str, str]] = [
    (r"^(feat|feature|add|new)(\(.+\))?:", "Added"),
    (r"^(fix|bug|patch)(\(.+\))?:", "Fixed"),
    (r"^(remove|delete|drop)(\(.+\))?:", "Removed"),
]


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def latest_tag() -> str | None:
    try:
        return run_git("describe", "--tags", "--abbrev=0")
    except subprocess.CalledProcessError:
        return None


def commits_since(tag: str | None) -> list[tuple[str, str, str]]:
    log_range = f"{tag}..HEAD" if tag else "HEAD"
    raw = run_git("log", log_range, "--pretty=format:%s|%h|%an", "--reverse")
    if not raw:
        return []
    rows: list[tuple[str, str, str]] = []
    for line in raw.splitlines():
        subject, commit_hash, author = line.split("|", 2)
        rows.append((subject, commit_hash, author))
    return rows


def categorize(subject: str) -> str:
    for pattern, section in RULES:
        if re.match(pattern, subject, re.I):
            return section
    return "Changed"


def build_changelog(tag: str | None, rows: list[tuple[str, str, str]]) -> str:
    buckets = {name: [] for name in SECTIONS}
    for subject, commit_hash, author in rows:
        section = categorize(subject)
        buckets[section].append(f"- {subject} ({commit_hash}, {author})")

    version = tag or "Unreleased"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = ["# Changelog", "", f"## [{version}] - {date}", ""]
    for section in SECTIONS:
        items = buckets[section]
        if not items:
            continue
        lines.extend([f"### {section}", "", *items, ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md")
    tag = latest_tag()
    rows = commits_since(tag)
    content = build_changelog(tag, rows)
    out.write_text(content, encoding="utf-8")
    print(f"Wrote {out} ({len(content.splitlines())} lines)")
    if tag:
        print(f"Range: {tag}..HEAD")
    else:
        print("Range: full history (no tags found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
