#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.rstrip("\n")


def last_tag(cwd: Path) -> str | None:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"], cwd)
    except subprocess.CalledProcessError:
        return None

    return tag or None


def commits_since(cwd: Path, tag: str | None) -> list[Commit]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    raw = run_git(
        [
            "log",
            "--no-merges",
            "--format=%H%x1f%s%x1f%b%x1e",
            revision_range,
        ],
        cwd,
    )
    if not raw.strip():
        return []

    commits = []
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        fields = record.split("\x1f", 2)
        if len(fields) != 3:
            continue
        sha, subject, body = fields
        commits.append(Commit(sha=sha, subject=subject, body=body.strip()))
    return commits


def categorize(commit: Commit) -> str:
    subject = commit.subject.lower()

    if re.match(r"^(feat|feature|add|create|implement|introduce)(\(.+\))?:", subject):
        return "Added"
    if re.match(r"^(fix|bugfix|repair|resolve)(\(.+\))?:", subject):
        return "Fixed"
    if re.match(r"^(remove|delete|drop|deprecate)(\(.+\))?:", subject):
        return "Removed"
    if re.match(r"^(refactor|perf|docs|style|test|chore|ci|build|change|update)(\(.+\))?:", subject):
        return "Changed"

    words = set(re.findall(r"[a-z]+", subject))
    if words & {"remove", "removed", "delete", "deleted", "drop", "dropped"}:
        return "Removed"
    if words & {"fix", "fixed", "bug", "resolve", "resolved"}:
        return "Fixed"
    if words & {"add", "added", "new", "create", "created", "implement", "implemented"}:
        return "Added"
    return "Changed"


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return subject[:1].upper() + subject[1:] if subject else "Unspecified change"


def render_changelog(commits: list[Commit], tag: str | None) -> str:
    source = f"commits since `{tag}`" if tag else "all available git history"
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit)].append(commit)

    lines = [
        "# Changelog",
        "",
        f"## Unreleased - {date.today().isoformat()}",
        "",
        f"_Generated from {source}._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        entries = grouped[category]
        if entries:
            for commit in entries:
                lines.append(f"- {clean_subject(commit.subject)} ({commit.sha[:7]})")
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the last git tag.")
    parser.add_argument("--repo", default=".", help="Path to the git repository.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output markdown file.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    tag = last_tag(repo)
    commits = commits_since(repo, tag)
    changelog = render_changelog(commits, tag)
    Path(args.output).write_text(changelog, encoding="utf-8")
    print(f"Wrote {args.output} with {len(commits)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
