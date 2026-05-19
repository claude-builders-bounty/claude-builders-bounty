#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

The script collects commits since the latest git tag (or all commits when no tag
exists), categorizes them, and writes a Keep-a-Changelog style CHANGELOG.md.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


CATEGORIES = {
    "Added": ("feat", "add", "new", "implement", "create"),
    "Fixed": ("fix", "bug", "repair", "resolve", "correct"),
    "Changed": ("change", "update", "refactor", "improve", "adjust", "modify"),
    "Removed": ("remove", "delete", "drop", "deprecate"),
}


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def latest_tag() -> str | None:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"])
        return tag or None
    except subprocess.CalledProcessError:
        return None


def collect_commits(since_tag: str | None) -> list[Commit]:
    revision_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
    try:
        raw = run_git(["log", revision_range, "--pretty=format:%h%x09%s"])
    except subprocess.CalledProcessError:
        return []

    commits: list[Commit] = []
    for line in raw.splitlines():
        if not line.strip() or "\t" not in line:
            continue
        sha, subject = line.split("\t", 1)
        commits.append(Commit(sha=sha, subject=subject.strip()))
    return commits


def normalize_subject(subject: str) -> str:
    # Conventional commit: feat(scope): message -> message
    match = re.match(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*(.+)$", subject)
    if match:
        subject = match.group(1)
    return subject[:1].upper() + subject[1:]


def category_for(subject: str) -> str:
    lowered = subject.lower()
    conventional = re.match(r"^([a-zA-Z]+)(?:\([^)]+\))?!?:", lowered)
    prefix = conventional.group(1) if conventional else ""

    if prefix in {"feat"}:
        return "Added"
    if prefix in {"fix"}:
        return "Fixed"
    if prefix in {"refactor", "perf", "style", "chore", "docs", "test", "ci", "build"}:
        return "Changed"
    if prefix in {"remove", "revert"}:
        return "Removed"

    for category, keywords in CATEGORIES.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "Changed"


def render_changelog(commits: list[Commit], since_tag: str | None) -> str:
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)

    base = since_tag or "the beginning of history"
    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git commit history.",
        "",
        f"## Unreleased - {date.today().isoformat()}",
        "",
        f"_Changes since {base}._",
        "",
    ]

    if not commits:
        lines += ["No commits found for this range.", ""]
        return "\n".join(lines)

    for category in ("Added", "Fixed", "Changed", "Removed"):
        items = grouped[category]
        if not items:
            continue
        lines += [f"### {category}", ""]
        for commit in items:
            lines.append(f"- {normalize_subject(commit.subject)} ({commit.sha})")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--since-tag", help="Override the latest git tag")
    args = parser.parse_args()

    tag = args.since_tag if args.since_tag is not None else latest_tag()
    commits = collect_commits(tag)
    changelog = render_changelog(commits, tag)
    Path(args.output).write_text(changelog, encoding="utf-8")
    print(f"Wrote {args.output} with {len(commits)} commits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
