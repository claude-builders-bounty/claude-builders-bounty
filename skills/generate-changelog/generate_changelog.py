#!/usr/bin/env python3
"""Generate a Keep a Changelog-style document from Git history."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
TYPE_TO_CATEGORY = {
    "feat": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "docs": "Changed",
    "style": "Changed",
    "test": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "remove": "Removed",
    "revert": "Removed",
}


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def git(repo: Path, *args: str, allow_failure: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode and not allow_failure:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def last_tag(repo: Path) -> str | None:
    tag = git(repo, "describe", "--tags", "--abbrev=0", allow_failure=True)
    return tag or None


def commits_since(repo: Path, tag: str | None) -> list[Commit]:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    raw = git(repo, "log", revision, "--no-merges", "--pretty=format:%H%x1f%s%x1e")
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record or "\x1f" not in record:
            continue
        sha, subject = record.split("\x1f", 1)
        commits.append(Commit(sha=sha.strip(), subject=subject.strip()))
    return commits


def categorize(subject: str) -> tuple[str, str]:
    match = re.match(r"(?P<type>[A-Za-z]+)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<body>.+)", subject)
    if match:
        kind = match.group("type").lower()
        body = match.group("body").strip()
        category = TYPE_TO_CATEGORY.get(kind, "Changed")
        if match.group("breaking"):
            body = f"**Breaking:** {body}"
        return category, body

    lowered = subject.lower()
    if lowered.startswith(("add ", "create ", "implement ")):
        return "Added", subject
    if lowered.startswith(("fix ", "resolve ", "correct ")):
        return "Fixed", subject
    if lowered.startswith(("remove ", "delete ", "drop ")):
        return "Removed", subject
    return "Changed", subject


def render(commits: list[Commit], tag: str | None) -> str:
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        category, cleaned = categorize(commit.subject)
        grouped[category].append(Commit(commit.sha, cleaned))

    lines = ["# Changelog", "", "All notable changes to this project are documented here.", "", "## [Unreleased]", ""]
    if tag:
        lines.extend([f"Changes since `{tag}`.", ""])
    for category in CATEGORIES:
        if not grouped[category]:
            continue
        lines.extend([f"### {category}", ""])
        for commit in grouped[category]:
            lines.append(f"- {commit.subject} (`{commit.sha[:7]}`)")
        lines.append("")
    if not commits:
        lines.extend(["No changes since the latest tag.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository (default: current directory)")
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"), help="Output file")
    parser.add_argument("--stdout", action="store_true", help="Print instead of writing a file")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        parser.error(f"not a Git repository: {repo}")
    tag = last_tag(repo)
    output = render(commits_since(repo, tag), tag)
    if args.stdout:
        print(output, end="")
    else:
        destination = args.output if args.output.is_absolute() else repo / args.output
        destination.write_text(output, encoding="utf-8")
        print(f"Generated {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
