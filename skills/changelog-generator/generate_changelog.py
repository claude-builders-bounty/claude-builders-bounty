#!/usr/bin/env python3
"""Generate a structured changelog from git history."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORIES: "OrderedDict[str, tuple[str, ...]]" = OrderedDict(
    [
        ("Added", ("feat", "add")),
        ("Fixed", ("fix", "hotfix")),
        ("Changed", ("change", "refactor", "perf", "deps", "build", "ci")),
        ("Removed", ("remove", "delete", "drop")),
        ("Documentation", ("docs",)),
        ("Tests", ("test", "tests")),
        ("Other", ()),
    ]
)

COMMIT_RE = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?!?:\s*(?P<message>.+)$")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git_log(since: str | None, max_count: int | None) -> list[Commit]:
    revision = f"{since}..HEAD" if since else "HEAD"
    command = ["git", "log", revision, "--no-merges", "--pretty=format:%h%x09%s"]
    if max_count:
        command.insert(2, f"--max-count={max_count}")
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git log failed")
    commits = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        sha, subject = line.split("\t", 1)
        commits.append(Commit(sha=sha, subject=subject))
    return commits


def categorize(subject: str) -> str:
    match = COMMIT_RE.match(subject)
    if not match:
        return "Other"
    commit_type = match.group("type").lower()
    for category, prefixes in CATEGORIES.items():
        if commit_type in prefixes:
            return category
    return "Other"


def clean_subject(subject: str) -> str:
    match = COMMIT_RE.match(subject)
    if match:
        return match.group("message").strip()
    return subject.strip()


def render_changelog(commits: list[Commit], since: str | None) -> str:
    title = f"Unreleased - {date.today().isoformat()}"
    range_label = f"Changes since `{since}`" if since else "Recent changes"
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    lines = ["# Changelog", "", f"## {title}", "", range_label, ""]
    if not commits:
        lines.append("- No commits found.")
        lines.append("")
        return "\n".join(lines)

    for category, category_commits in grouped.items():
        if not category_commits:
            continue
        lines.extend([f"### {category}", ""])
        for commit in category_commits:
            lines.append(f"- {clean_subject(commit.subject)} ({commit.sha})")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--since", help="Git tag, branch, or revision to diff from")
    parser.add_argument("--max-count", type=int, help="Maximum number of commits to read")
    parser.add_argument("--output", help="Output file path. Defaults to stdout.")
    args = parser.parse_args(argv)

    try:
        changelog = render_changelog(run_git_log(args.since, args.max_count), args.since)
    except RuntimeError as exc:
        print(f"generate_changelog: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(changelog, encoding="utf-8")
    else:
        print(changelog, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
