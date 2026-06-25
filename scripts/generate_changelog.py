#!/usr/bin/env python3
"""Generate a Keep a Changelog-style CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path


CATEGORIES = {
    "Added": ("feat", "feature", "add", "added", "new"),
    "Fixed": ("fix", "bug", "bugfix", "hotfix", "patch", "repair"),
    "Changed": ("change", "changed", "refactor", "perf", "docs", "doc", "chore", "style", "test", "ci", "build"),
    "Removed": ("remove", "removed", "delete", "deleted", "drop", "deprecated"),
}


def git(args: list[str], cwd: Path) -> str:
    git_bin = os.environ.get("GIT_BIN", "git")
    return subprocess.check_output([git_bin, *args], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()


def last_tag(cwd: Path) -> str | None:
    try:
        return git(["describe", "--tags", "--abbrev=0"], cwd)
    except subprocess.CalledProcessError:
        return None


def commit_lines(cwd: Path, tag: str | None) -> list[str]:
    commit_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        output = git(["log", "--no-merges", "--pretty=format:%h%x09%s", commit_range], cwd)
    except subprocess.CalledProcessError:
        return []
    return [line for line in output.splitlines() if line.strip()]


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return subject[:1].upper() + subject[1:] if subject else "Update project"


def category_for(subject: str) -> str:
    lowered = subject.lower()
    conventional = re.match(r"^([a-zA-Z]+)(?:\([^)]+\))?!?:", lowered)
    if conventional:
        token = conventional.group(1)
        for category, tokens in CATEGORIES.items():
            if token in tokens:
                return category

    for category, tokens in CATEGORIES.items():
        if any(re.search(rf"\b{re.escape(token)}\b", lowered) for token in tokens):
            return category

    return "Changed"


def build_changelog(lines: list[str], tag: str | None) -> str:
    today = dt.date.today().isoformat()
    heading = f"## Unreleased - {today}"
    range_text = f"Commits since `{tag}`." if tag else "Commits from the full available history; no git tag was found."
    buckets = {category: [] for category in CATEGORIES}

    for line in lines:
        sha, subject = line.split("\t", 1)
        buckets[category_for(subject)].append(f"- {clean_subject(subject)} ({sha})")

    body = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        heading,
        "",
        range_text,
        "",
    ]

    for category in ("Added", "Fixed", "Changed", "Removed"):
        body.append(f"### {category}")
        body.append("")
        body.extend(buckets[category] or ["- No entries."])
        body.append("")

    return "\n".join(body).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the last git tag.")
    parser.add_argument("--repo", default=".", help="Path to the git repository to inspect.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 1

    tag = last_tag(repo)
    lines = commit_lines(repo, tag)
    changelog = build_changelog(lines, tag)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
