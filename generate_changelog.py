#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    author: str
    date: str


CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def get_last_tag() -> str | None:
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None


def get_commits(since_ref: str | None) -> list[Commit]:
    revision_range = f"{since_ref}..HEAD" if since_ref else "HEAD"
    raw = run_git(
        [
            "log",
            revision_range,
            "--reverse",
            "--date=short",
            "--format=%h%x1f%s%x1f%an%x1f%ad",
        ]
    )
    commits: list[Commit] = []
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 4:
            commits.append(Commit(*parts))
    return commits


def categorize(subject: str) -> str:
    text = subject.lower()
    prefix = text.split(":", 1)[0]

    if prefix.startswith("feat") or any(word in text for word in (" add ", "added ", "create ", "introduce ")):
        return "Added"
    if prefix.startswith("fix") or any(word in text for word in (" bug", "repair", "resolve", "patch")):
        return "Fixed"
    if prefix.startswith(("remove", "delete")) or any(word in text for word in (" remove ", "removed ", "delete ", "drop ")):
        return "Removed"
    return "Changed"


def clean_subject(subject: str) -> str:
    if ":" in subject:
        return subject.split(":", 1)[1].strip()
    return subject.strip()


def render_changelog(commits: list[Commit], since_ref: str | None) -> str:
    today = dt.date.today().isoformat()
    scope = f"Changes since `{since_ref}`" if since_ref else "All commits; no git tags found"
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORY_ORDER}

    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git commit history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"_{scope}._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORY_ORDER:
        category_commits = grouped[category]
        if not category_commits:
            continue
        lines.extend([f"### {category}", ""])
        for commit in category_commits:
            subject = clean_subject(commit.subject)
            lines.append(f"- {subject} ({commit.sha}, {commit.date}, {commit.author})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest git tag.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file path. Default: CHANGELOG.md")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file.")
    args = parser.parse_args()

    since_ref = get_last_tag()
    commits = get_commits(since_ref)
    content = render_changelog(commits, since_ref)

    if args.stdout:
        print(content, end="")
    else:
        output = Path(args.output)
        output.write_text(content, encoding="utf-8")
        print(f"Wrote {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
