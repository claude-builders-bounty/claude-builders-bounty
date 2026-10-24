#!/usr/bin/env python3
"""Generate a structured changelog from git history since the most recent tag."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

CATEGORIES = {
    "Added": re.compile(r"^(feat|add)(\([^)]+\))?!?:", re.I),
    "Fixed": re.compile(r"^(fix|bugfix)(\([^)]+\))?!?:", re.I),
    "Removed": re.compile(r"^(remove|delete)(\([^)]+\))?!?:", re.I),
    "Changed": re.compile(r"^(refactor|perf|docs|style|test|build|ci|chore|change)(\([^)]+\))?!?:", re.I),
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def latest_tag() -> str | None:
    try:
        value = git("describe", "--tags", "--abbrev=0")
        return value or None
    except subprocess.CalledProcessError:
        return None


def commits_since_tag() -> list[tuple[str, str]]:
    tag = latest_tag()
    rev = f"{tag}..HEAD" if tag else "HEAD"
    raw = git("log", rev, "--no-merges", "--format=%h%x1f%s")
    commits = []
    for line in raw.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        commits.append((sha, subject.strip()))
    return commits


def category(subject: str) -> str:
    for name, pattern in CATEGORIES.items():
        if pattern.search(subject):
            return name
    return "Changed"


def render(commits: list[tuple[str, str]], version: str) -> str:
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for sha, subject in commits:
        grouped[category(subject)].append((sha, subject))
    lines = [f"## {version}", ""]
    for name in ("Added", "Fixed", "Changed", "Removed"):
        entries = grouped.get(name, [])
        if entries:
            lines.extend((f"### {name}", ""))
            lines.extend(f"- {subject} ({sha})" for sha, subject in entries)
            lines.append("")
    if not any(grouped.values()):
        lines.extend(("- No changes recorded.", ""))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="Unreleased", help="heading for this release")
    parser.add_argument("--output", default="CHANGELOG.md", help="output Markdown path")
    parser.add_argument("--append", action="store_true", help="prepend to an existing changelog")
    args = parser.parse_args()
    try:
        commits = commits_since_tag()
        section = render(commits, args.version)
        target = Path(args.output)
        if args.append and target.exists():
            old = target.read_text(encoding="utf-8")
            target.write_text(section + "\n" + old, encoding="utf-8")
        else:
            target.write_text(section, encoding="utf-8")
        print(f"Wrote {len(commits)} commits to {target}")
        return 0
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"changelog generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
