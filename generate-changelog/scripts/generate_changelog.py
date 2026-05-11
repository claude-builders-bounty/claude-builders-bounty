#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORIES: list[tuple[str, tuple[str, ...]]] = [
    ("Added", ("feat", "feature", "add", "added")),
    ("Fixed", ("fix", "bug", "patch", "resolve", "resolved")),
    ("Removed", ("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecate", "deprecated")),
]


@dataclass(frozen=True)
class Commit:
    short_hash: str
    author: str
    subject: str


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def latest_tag(repo: Path) -> str | None:
    tags = run_git(repo, ["tag", "--sort=-creatordate"]).splitlines()
    return tags[0] if tags else None


def commit_range(repo: Path, start_ref: str | None) -> list[Commit]:
    revision = f"{start_ref}..HEAD" if start_ref else "HEAD"
    output = run_git(
        repo,
        [
            "log",
            revision,
            "--no-merges",
            "--pretty=format:%h%x1f%an%x1f%s%x1e",
        ],
    )
    commits: list[Commit] = []
    for record in output.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) != 3:
            continue
        commits.append(Commit(short_hash=parts[0], author=parts[1], subject=parts[2]))
    return commits


def category_for(subject: str) -> str:
    normalized = subject.lower().strip()
    conventional = re.match(r"(?P<type>[a-z]+)(?:\([^)]+\))?!?:", normalized)
    token = conventional.group("type") if conventional else normalized.split(maxsplit=1)[0]
    token = token.strip(":[]()")
    for category, aliases in CATEGORIES:
        if token in aliases or any(normalized.startswith(f"{alias}:") for alias in aliases):
            return category
    return "Changed"


def format_entry(commit: Commit) -> str:
    subject = commit.subject.strip()
    subject = subject[:1].upper() + subject[1:] if subject else "Update"
    return f"- {subject} ({commit.short_hash}, {commit.author})"


def render_changelog(start_ref: str | None, commits: list[Commit]) -> str:
    today = dt.date.today().isoformat()
    title = "Unreleased"
    if start_ref:
        title = f"Unreleased changes since {start_ref}"

    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        f"## {title} - {today}",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    grouped: dict[str, list[Commit]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }
    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)

    for heading in grouped:
        entries = grouped[heading]
        if not entries:
            continue
        lines.extend([f"### {heading}", ""])
        lines.extend(format_entry(commit) for commit in entries)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Path to the git repository")
    parser.add_argument("--from", dest="from_ref", help="Start ref or tag. Defaults to latest tag")
    parser.add_argument("--all", action="store_true", help="Use all commits instead of latest tag range")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output markdown file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 2

    try:
        start_ref = None if args.all else args.from_ref or latest_tag(repo)
        commits = commit_range(repo, start_ref)
        changelog = render_changelog(start_ref, commits)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(changelog, encoding="utf-8", newline="\n")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
