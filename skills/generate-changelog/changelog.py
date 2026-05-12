#!/usr/bin/env python3
"""Generate a Keep a Changelog-style file from git history."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str = ""


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def last_tag(repo: Path) -> str | None:
    try:
        tag = run_git(repo, ["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None
    return tag or None


def commit_range(repo: Path, since: str | None) -> str:
    if since:
        return f"{since}..HEAD"
    tag = last_tag(repo)
    return f"{tag}..HEAD" if tag else "HEAD"


def load_commits(repo: Path, since: str | None = None) -> list[Commit]:
    fmt = "%H%x1f%s%x1f%b%x1e"
    output = run_git(repo, ["log", commit_range(repo, since), f"--pretty=format:{fmt}"])
    commits: list[Commit] = []
    for raw in output.split("\x1e"):
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.split("\x1f", 2)
        if len(parts) < 2:
            continue
        sha, subject = parts[0], parts[1].strip()
        body = parts[2].strip() if len(parts) == 3 else ""
        commits.append(Commit(sha=sha, subject=subject, body=body))
    return commits


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return subject[:1].upper() + subject[1:] if subject else "Update project"


def categorize(subject: str, body: str = "") -> str:
    text = f"{subject}\n{body}".lower()
    prefix = subject.split(":", 1)[0].lower()

    if any(word in text for word in ("remove", "removed", "delete", "deleted", "drop ", "deprecate")):
        return "Removed"
    if prefix.startswith("fix") or any(word in text for word in ("bug", "crash", "regression")):
        return "Fixed"
    if prefix.startswith("feat") or any(word in text for word in ("add ", "added", "implement", "introduce")):
        return "Added"
    return "Changed"


def group_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject, commit.body)].append(commit)
    return grouped


def render_changelog(commits: list[Commit], title: str = "Unreleased") -> str:
    grouped = group_commits(commits)
    lines = ["# Changelog", "", f"## {title}", ""]
    if not commits:
        lines.extend(["No changes found.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        entries = grouped[category]
        if not entries:
            continue
        lines.extend([f"### {category}", ""])
        for commit in entries:
            lines.append(f"- {clean_subject(commit.subject)} ({commit.sha[:7]})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits.")
    parser.add_argument("--repo", default=".", help="Repository path. Defaults to current directory.")
    parser.add_argument("--since", help="Git revision or tag to start after. Defaults to the last tag.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path.")
    parser.add_argument("--title", default="Unreleased", help="Heading for the generated release section.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output

    commits = load_commits(repo, args.since)
    output.write_text(render_changelog(commits, args.title), encoding="utf-8")
    print(f"Wrote {output} with {len(commits)} commits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
