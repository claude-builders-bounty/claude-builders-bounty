#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


SECTION_ORDER = ("Added", "Fixed", "Changed", "Removed")

TYPE_TO_SECTION = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "docs": "Changed",
    "test": "Changed",
    "tests": "Changed",
    "ci": "Changed",
    "build": "Changed",
    "chore": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
    "deprecate": "Removed",
}


@dataclass(frozen=True)
class Commit:
    short_sha: str
    subject: str


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def latest_tag(repo: Path) -> str | None:
    try:
        return run_git(repo, ["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None


def commit_range(repo: Path, since: str | None, until: str) -> str:
    start = since or latest_tag(repo)
    if start:
        return f"{start}..{until}"
    return until


def parse_commits(raw: str) -> list[Commit]:
    commits: list[Commit] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        short_sha, _, subject = line.partition("\x1f")
        commits.append(Commit(short_sha=short_sha, subject=subject.strip()))
    return commits


def load_commits(repo: Path, since: str | None, until: str) -> list[Commit]:
    raw = run_git(
        repo,
        [
            "log",
            "--no-merges",
            "--date=short",
            "--pretty=format:%h%x1f%s",
            commit_range(repo, since, until),
        ],
    )
    return parse_commits(raw)


def clean_subject(subject: str) -> str:
    conventional = re.match(r"^(?P<kind>[a-zA-Z]+)(?:\([^)]+\))?!?:\s*(?P<text>.+)$", subject)
    if conventional:
        return conventional.group("text").strip()
    return subject.strip()


def classify(subject: str) -> str:
    conventional = re.match(r"^(?P<kind>[a-zA-Z]+)(?:\([^)]+\))?!?:", subject)
    if conventional:
        return TYPE_TO_SECTION.get(conventional.group("kind").lower(), "Changed")

    lowered = subject.lower()
    if any(word in lowered for word in ("remove", "delete", "drop", "deprecate")):
        return "Removed"
    if any(word in lowered for word in ("fix", "bug", "patch", "repair")):
        return "Fixed"
    if any(word in lowered for word in ("add", "new", "introduce", "support")):
        return "Added"
    return "Changed"


def render_changelog(commits: list[Commit], repo: Path, since: str | None, until: str) -> str:
    today = dt.date.today().isoformat()
    heading_range = commit_range(repo, since, until)
    sections: dict[str, list[str]] = {section: [] for section in SECTION_ORDER}

    for commit in commits:
        sections[classify(commit.subject)].append(
            f"- {clean_subject(commit.subject)} ({commit.short_sha})"
        )

    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"_Commit range: `{heading_range}`_",
        "",
    ]

    for section in SECTION_ORDER:
        entries = sections[section]
        if not entries:
            continue
        lines.append(f"### {section}")
        lines.extend(entries)
        lines.append("")

    if all(not entries for entries in sections.values()):
        lines.extend(["No changes found.", ""])

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Git repository to inspect")
    parser.add_argument("--since", help="Tag, commit, or date range start")
    parser.add_argument("--until", default="HEAD", help="Range end, default: HEAD")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output Markdown path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = Path(os.getcwd()) / output

    commits = load_commits(repo, args.since, args.until)
    output.write_text(render_changelog(commits, repo, args.since, args.until), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
