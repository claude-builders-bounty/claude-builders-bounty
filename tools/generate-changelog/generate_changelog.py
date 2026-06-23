#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path


CATEGORIES = {
    "Added": ("feat", "add", "added"),
    "Fixed": ("fix", "bug", "bugfix", "hotfix"),
    "Changed": (
        "change",
        "changed",
        "update",
        "refactor",
        "perf",
        "docs",
        "test",
        "chore",
        "build",
        "ci",
    ),
    "Removed": ("remove", "removed", "delete", "drop", "deprecate"),
}


def git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_output(args: list[str], check: bool = True) -> str:
    result = git(args, check=check)
    return result.stdout.strip()


def latest_tag() -> str | None:
    result = git(["describe", "--tags", "--abbrev=0"], check=False)
    tag = result.stdout.strip()
    return tag or None


def clean_subject(subject: str) -> str:
    cleaned = re.sub(r"^[A-Za-z]+(\([^)]+\))?!?:\s*", "", subject.strip())
    return cleaned or "Untitled commit"


def category_for(subject: str) -> str:
    match = re.match(r"^([A-Za-z]+)(\([^)]+\))?!?:", subject.strip())
    prefix = match.group(1).lower() if match else ""
    for category, prefixes in CATEGORIES.items():
        if prefix in prefixes:
            return category
    return "Changed"


def collect_commits(commit_range: str) -> dict[str, list[str]]:
    grouped = {category: [] for category in CATEGORIES}
    log = git_output(["log", "--reverse", "--pretty=format:%H%x09%s", commit_range], check=False)

    for line in log.splitlines():
        if not line.strip():
            continue
        sha, subject = line.split("\t", 1)
        grouped[category_for(subject)].append(f"- {clean_subject(subject)} ({sha[:7]})")

    return grouped


def render_changelog(repo_name: str, range_label: str, grouped: dict[str, list[str]]) -> str:
    today = dt.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        f"## Unreleased - {today}",
        "",
        f"_Generated for `{repo_name}` using commits {range_label}._",
        "",
    ]

    for category in ("Added", "Fixed", "Changed", "Removed"):
        lines.extend([f"### {category}", ""])
        entries = grouped[category]
        lines.extend(entries if entries else ["- No entries."])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="CHANGELOG.md", help="output file path")
    args = parser.parse_args()

    try:
        git_output(["rev-parse", "--is-inside-work-tree"])
        root = Path(git_output(["rev-parse", "--show-toplevel"]))
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("error: generate_changelog.py must be run inside a git repository", file=sys.stderr)
        return 1

    tag = latest_tag()
    commit_range = f"{tag}..HEAD" if tag else "HEAD"
    range_label = f"since {tag}" if tag else "from the beginning of history"
    changelog = render_changelog(root.name, range_label, collect_commits(commit_range))

    output_path = Path(args.output)
    output_path.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
