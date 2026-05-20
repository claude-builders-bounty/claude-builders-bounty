#!/usr/bin/env python3
"""Generate a structured Markdown changelog from git history."""

from __future__ import annotations

import argparse
import subprocess
from collections import defaultdict
from pathlib import Path

GROUPS = {
    "feat": "Features",
    "fix": "Fixes",
    "docs": "Documentation",
    "test": "Tests",
    "tests": "Tests",
    "refactor": "Refactors",
    "chore": "Maintenance",
    "build": "Maintenance",
    "ci": "Maintenance",
    "perf": "Maintenance",
}
ORDER = ["Features", "Fixes", "Documentation", "Tests", "Refactors", "Maintenance", "Other"]


def classify(subject: str) -> str:
    prefix = subject.split(":", 1)[0].split("(", 1)[0].lower()
    return GROUPS.get(prefix, "Other")


def git_log(since: str | None, until: str) -> list[tuple[str, str]]:
    rev_range = f"{since}..{until}" if since else until
    cmd = ["git", "log", "--no-merges", "--pretty=format:%h%x09%s", rev_range]
    rows = subprocess.check_output(cmd, text=True).splitlines()
    commits: list[tuple[str, str]] = []
    for row in rows:
        if "\t" in row:
            short_hash, subject = row.split("\t", 1)
            commits.append((short_hash, subject))
    return commits


def render(commits: list[tuple[str, str]], title: str) -> str:
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for short_hash, subject in commits:
        grouped[classify(subject)].append((short_hash, subject))

    lines = ["# Changelog", "", f"## {title}", ""]
    if not commits:
        lines.append("No commits found.")
        return "\n".join(lines) + "\n"

    for group in ORDER:
        items = grouped.get(group, [])
        if not items:
            continue
        lines.extend([f"### {group}", ""])
        for short_hash, subject in items:
            lines.append(f"- `{short_hash}` {subject}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="Start ref/tag/commit, exclusive")
    parser.add_argument("--until", default="HEAD", help="End ref/tag/commit, inclusive")
    parser.add_argument("--output", default="CHANGELOG.md", help="Markdown output path")
    args = parser.parse_args()

    title = f"{args.since or 'root'}..{args.until}"
    Path(args.output).write_text(render(git_log(args.since, args.until), title), encoding="utf-8")


if __name__ == "__main__":
    main()
