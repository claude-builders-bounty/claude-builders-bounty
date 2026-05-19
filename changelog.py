#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = {
    "Added": ("feat", "add", "added", "new"),
    "Fixed": ("fix", "bugfix", "bug", "hotfix", "repair"),
    "Changed": ("change", "changed", "refactor", "perf", "style", "docs", "test", "build", "ci", "chore"),
    "Removed": ("remove", "removed", "delete", "deleted", "drop", "dropped"),
}


@dataclass
class Commit:
    sha: str
    subject: str


def run_git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        sys.exit("git is required but was not found on PATH")
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "git command failed"
        sys.exit(message)
    return result.stdout.strip()


def last_tag() -> str | None:
    try:
        tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None
    return tag or None


def commit_range(tag: str | None) -> str:
    return f"{tag}..HEAD" if tag else "HEAD"


def load_commits(rev_range: str) -> list[Commit]:
    output = run_git(["log", rev_range, "--pretty=format:%h%x1f%s"])
    if not output:
        return []
    commits: list[Commit] = []
    for line in output.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        commits.append(Commit(sha=sha, subject=subject.strip()))
    return commits


def normalize_subject(subject: str) -> tuple[str, str]:
    lowered = subject.lower()
    prefix = lowered.split(":", 1)[0].split("(", 1)[0].strip()
    cleaned = subject.split(":", 1)[1].strip() if ":" in subject else subject.strip()
    return prefix, cleaned[:1].upper() + cleaned[1:] if cleaned else subject


def category_for(subject: str) -> str:
    prefix, _ = normalize_subject(subject)
    for category, prefixes in CATEGORIES.items():
        if prefix in prefixes:
            return category
    return "Changed"


def render_changelog(commits: list[Commit], tag: str | None, repo: str | None) -> str:
    today = dt.date.today().isoformat()
    base = tag if tag else "the beginning of history"
    title = f"## Unreleased - {today}"
    lines = [
        "# Changelog",
        "",
        title,
        "",
        f"Changes since {base}.",
        "",
    ]

    grouped: dict[str, list[Commit]] = {name: [] for name in CATEGORIES}
    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        items = grouped[category]
        if not items:
            continue
        lines.extend([f"### {category}", ""])
        for commit in items:
            _, cleaned = normalize_subject(commit.subject)
            ref = f" ([{commit.sha}]({repo}/commit/{commit.sha}))" if repo else f" ({commit.sha})"
            lines.append(f"- {cleaned}{ref}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def remote_url() -> str | None:
    try:
        url = run_git(["config", "--get", "remote.origin.url"])
    except SystemExit:
        return None
    if url.startswith("git@github.com:"):
        return "https://github.com/" + url.removeprefix("git@github.com:").removesuffix(".git")
    if url.startswith("https://github.com/"):
        return url.removesuffix(".git")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits since the last tag.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file.")
    args = parser.parse_args()

    tag = last_tag()
    commits = load_commits(commit_range(tag))
    changelog = render_changelog(commits, tag, remote_url())

    if args.stdout:
        print(changelog, end="")
    else:
        Path(args.output).write_text(changelog, encoding="utf-8")
        print(f"Wrote {args.output} with {len(commits)} commits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
