#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout.strip()


def ensure_git_repo() -> None:
    if run_git(["rev-parse", "--is-inside-work-tree"]) != "true":
        raise SystemExit("error: generate_changelog.py must be run inside a git repository")


def latest_tag() -> str | None:
    tag = run_git(["describe", "--tags", "--abbrev=0"])
    return tag or None


def commit_subjects(revision_range: str) -> list[str]:
    output = run_git(["log", revision_range, "--no-merges", "--pretty=format:%s"])
    return [line.strip() for line in output.splitlines() if line.strip()]


def category_for(subject: str) -> str:
    lower = subject.lower()
    if lower.startswith(("feat:", "feature:", "add:", "added:")):
        return "Added"
    if lower.startswith(("fix:", "bugfix:", "hotfix:")) or " fix " in lower:
        return "Fixed"
    if lower.startswith(("remove:", "removed:", "delete:", "deleted:", "deprecate:", "deprecated:")):
        return "Removed"
    return "Changed"


def render_changelog(subjects: list[str], scope: str) -> str:
    sections = {category: [] for category in CATEGORIES}
    for subject in subjects:
        sections[category_for(subject)].append(subject)

    today = dt.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        f"## {today}",
        "",
        f"Generated from git history {scope}.",
        "",
    ]

    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        entries = sections[category]
        if entries:
            lines.extend(f"- {entry}" for entry in entries)
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a structured changelog from git history.")
    parser.add_argument("output", nargs="?", default="CHANGELOG.md", help="Output path")
    args = parser.parse_args()

    ensure_git_repo()

    tag = latest_tag()
    if tag:
        revision_range = f"{tag}..HEAD"
        scope = f"since {tag}"
    else:
        revision_range = "HEAD"
        scope = "for all commits"

    subjects = commit_subjects(revision_range)
    output = "# Changelog\n\nNo commits found " + scope + ".\n" if not subjects else render_changelog(subjects, scope)
    Path(args.output).write_text(output, encoding="utf-8")
    print(f"Generated {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
