#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    hash: str
    subject: str


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_last_tag(cwd: Path) -> str | None:
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], cwd)
    except subprocess.CalledProcessError:
        return None


def get_commit_range(cwd: Path, since: str | None = None) -> tuple[str, str]:
    if since:
        return since, f"{since}..HEAD"

    tag = get_last_tag(cwd)
    if tag:
        return tag, f"{tag}..HEAD"

    return "repository start", "HEAD"


def parse_commits(raw_log: str) -> list[Commit]:
    commits: list[Commit] = []
    for line in raw_log.splitlines():
        if not line:
            continue
        short_hash, _, subject = line.partition("\t")
        commits.append(Commit(hash=short_hash, subject=subject.strip()))
    return commits


def get_commits(cwd: Path, revision_range: str) -> list[Commit]:
    raw_log = run_git(["log", "--pretty=format:%h%x09%s", revision_range], cwd)
    return parse_commits(raw_log)


def categorize(subject: str) -> str:
    lowered = subject.lower()
    prefix = lowered.split(":", 1)[0].split("(", 1)[0].strip().rstrip("!")

    if prefix in {"feat", "feature", "add", "added"} or lowered.startswith(("add ", "adds ", "added ")):
        return "Added"
    if prefix in {"fix", "bugfix", "hotfix"} or lowered.startswith(("fix ", "fixes ", "fixed ")):
        return "Fixed"
    if prefix in {"remove", "removed", "delete", "deleted"} or lowered.startswith(("remove ", "removes ", "removed ", "delete ", "deletes ", "deleted ")):
        return "Removed"
    if prefix in {"refactor", "change", "changed", "update", "updated", "docs", "doc", "chore", "perf", "style", "test"}:
        return "Changed"
    return "Changed"


def grouped_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)
    return grouped


def render_changelog(commits: list[Commit], since_label: str, title: str = "Unreleased") -> str:
    today = dt.date.today().isoformat()
    grouped = grouped_commits(commits)
    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git commit history.",
        "",
        f"## {title} - {today}",
        "",
        f"_Commits since: {since_label}_",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        entries = grouped[category]
        if entries:
            lines.extend(f"- {commit.subject} ({commit.hash})" for commit in entries)
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines)


def write_changelog(content: str, output: Path) -> None:
    output.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits since the last tag.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository path. Defaults to current directory.")
    parser.add_argument("--since", help="Optional git revision/tag to use instead of the latest tag.")
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"), help="Output path. Defaults to CHANGELOG.md.")
    parser.add_argument("--title", default="Unreleased", help="Release heading. Defaults to Unreleased.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    since_label, revision_range = get_commit_range(repo, args.since)
    commits = get_commits(repo, revision_range)
    content = render_changelog(commits, since_label, args.title)
    output = args.output if args.output.is_absolute() else repo / args.output
    write_changelog(content, output)
    print(f"Wrote {output} with {len(commits)} commits since {since_label}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
