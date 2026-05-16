#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from dataclasses import dataclass


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def latest_tag() -> str | None:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"])
    except RuntimeError:
        return None
    return tag or None


def collect_commits(tag: str | None) -> list[Commit]:
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    output = run_git(["log", "--no-merges", "--pretty=format:%h%x09%s", rev_range])
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\t")
        commits.append(Commit(sha=sha, subject=subject.strip()))
    return commits


def categorize(subject: str) -> str:
    lowered = subject.lower()
    if lowered.startswith(("fix", "bug", "repair")) or any(word in lowered for word in (" fix ", " bug ", " broken ")):
        return "Fixed"
    if lowered.startswith(("remove", "delete", "drop", "deprecate")):
        return "Removed"
    if lowered.startswith(("change", "update", "refactor", "rename", "improve")):
        return "Changed"
    return "Added"


def render_changelog(commits: list[Commit], tag: str | None, version: str) -> str:
    today = dt.date.today().isoformat()
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git history.",
        "",
        f"## {version} - {today}",
        "",
        f"_Commits since: {tag or 'repository start'}_",
        "",
    ]

    for category in CATEGORIES:
        lines.append(f"### {category}")
        entries = grouped[category]
        if entries:
            lines.extend(f"- {commit.subject} ({commit.sha})" for commit in entries)
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits since the last tag.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path.")
    parser.add_argument("--version", default="Unreleased", help="Version heading to write.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        tag = latest_tag()
        commits = collect_commits(tag)
        changelog = render_changelog(commits, tag, args.version)
        if args.stdout:
            print(changelog, end="")
        else:
            with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(changelog)
            print(f"Wrote {args.output}")
    except (OSError, RuntimeError) as exc:
        print(f"generate-changelog: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
