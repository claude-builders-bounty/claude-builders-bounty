#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def last_tag() -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def commits_since(ref: str | None) -> list[Commit]:
    revision_range = f"{ref}..HEAD" if ref else "HEAD"
    output = run_git(["log", "--reverse", "--pretty=format:%h%x09%s", revision_range])
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, subject = line.split("\t", 1)
        commits.append(Commit(sha=sha, subject=subject))
    return commits


def categorize(subject: str) -> str:
    normalized = subject.lower()
    prefix = normalized.split(":", 1)[0]

    if "remove" in prefix or "delete" in prefix or normalized.startswith(("remove ", "delete ")):
        return "Removed"
    if "fix" in prefix or "bug" in prefix or normalized.startswith(("fix ", "bugfix ")):
        return "Fixed"
    if "feat" in prefix or "add" in prefix or normalized.startswith(("add ", "create ")):
        return "Added"
    return "Changed"


def grouped_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    groups = {category: [] for category in CATEGORIES}
    for commit in commits:
        groups[categorize(commit.subject)].append(commit)
    return groups


def render_changelog(commits: list[Commit], since_ref: str | None) -> str:
    groups = grouped_commits(commits)
    heading = f"Unreleased - {date.today().isoformat()}"
    source = f"Commits since `{since_ref}`" if since_ref else "Commits from repository history"
    lines = ["# Changelog", "", f"## {heading}", "", source, ""]

    if not commits:
        lines.extend(["No changes found.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        entries = groups[category]
        if entries:
            lines.extend(f"- {commit.subject} ({commit.sha})" for commit in entries)
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path. Defaults to CHANGELOG.md.")
    parser.add_argument("--since", help="Git tag or ref to use instead of the latest tag.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog without writing a file.")
    args = parser.parse_args()

    since_ref = args.since if args.since else last_tag()
    changelog = render_changelog(commits_since(since_ref), since_ref)

    if args.stdout:
        print(changelog)
        return 0

    Path(args.output).write_text(changelog, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
