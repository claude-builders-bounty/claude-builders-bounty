#!/usr/bin/env python3
"""Generate a Keep a Changelog-style file from Git commit history."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")
CONVENTIONAL_RE = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?!?:\s*(?P<subject>.+)$")


@dataclass(frozen=True)
class Commit:
    short_hash: str
    subject: str
    body: str


def run_git(*args: str) -> str:
    result = subprocess.run(("git", *args), text=True, capture_output=True, check=False)
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise RuntimeError(message)
    return result.stdout


def latest_tag() -> str | None:
    try:
        return run_git("describe", "--tags", "--abbrev=0").strip() or None
    except RuntimeError:
        return None


def commits_since(tag: str | None, include_merges: bool) -> list[Commit]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    args = ["log", "--reverse", "--format=%h%x1f%s%x1f%b%x1e"]
    if not include_merges:
        args.append("--no-merges")
    args.append(revision_range)
    raw = run_git(*args)
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip("\r\n")
        if not record:
            continue
        parts = record.split("\x1f", 2)
        if len(parts) == 3:
            commits.append(Commit(*(part.strip() for part in parts)))
    return commits


def categorize(subject: str, body: str) -> tuple[str, str]:
    match = CONVENTIONAL_RE.match(subject)
    commit_type = match.group("type").lower() if match else ""
    cleaned = match.group("subject") if match else subject
    text = subject.lower()
    if commit_type in {"feat", "add"}:
        return "Added", cleaned
    if commit_type in {"fix", "hotfix", "security"}:
        return "Fixed", cleaned
    if commit_type in {"remove", "delete"}:
        return "Removed", cleaned
    if re.search(r"\b(remove|delete|drop|deprecat)\b", text):
        return "Removed", cleaned
    if re.search(r"\b(fix|repair|resolve|prevent|security)\b", text):
        return "Fixed", cleaned
    if re.search(r"\b(add|introduce|support|create)\b", text):
        return "Added", cleaned
    return "Changed", cleaned


def render(commits: list[Commit], tag: str | None) -> str:
    grouped: dict[str, list[tuple[str, str]]] = {name: [] for name in CATEGORY_ORDER}
    for commit in commits:
        category, subject = categorize(commit.subject, commit.body)
        grouped[category].append((subject.rstrip("."), commit.short_hash))
    start = f"after `{tag}`" if tag else "from the complete Git history (no tag found)"
    lines = ["# Changelog", "", "All notable changes to this project will be documented in this file.", "", "## [Unreleased]", "", f"Generated from commits {start}."]
    if not commits:
        lines.extend(["", "No commits found in the selected range."])
    for category in CATEGORY_ORDER:
        entries = grouped[category]
        if entries:
            lines.extend(["", f"### {category}", ""])
            lines.extend(f"- {subject} ({short_hash})" for subject, short_hash in entries)
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a categorized CHANGELOG.md from Git history.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output Markdown path.")
    parser.add_argument("--since", metavar="TAG", help="Use commits after this tag instead of the latest tag.")
    parser.add_argument("--include-merges", action="store_true", help="Include merge commits.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_git("rev-parse", "--is-inside-work-tree")
        tag = args.since or latest_tag()
        content = render(commits_since(tag, args.include_merges), tag)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output} using commits after {tag or 'the repository start'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
