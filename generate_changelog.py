#!/usr/bin/env python3
"""Generate a Keep a Changelog-style CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")
TYPE_TO_CATEGORY = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "change": "Changed",
    "changed": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "docs": "Changed",
    "style": "Changed",
    "test": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
}
KEYWORD_RULES = (
    ("Fixed", re.compile(r"\b(fix|fixed|bug|patch|repair|resolve|resolved)\b", re.I)),
    ("Removed", re.compile(r"\b(remove|removed|delete|deleted|drop|dropped)\b", re.I)),
    ("Added", re.compile(r"\b(add|added|new|introduce|introduced|implement|implemented)\b", re.I)),
)
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?(?P<breaking>!)?:\s*(?P<message>.+)$"
)


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    author_date: str


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def maybe_fetch_tags(repo: Path) -> None:
    result = run_git(repo, ["fetch", "--tags", "--quiet"], check=False)
    if result.returncode != 0:
        print(f"warning: could not fetch tags: {result.stderr.strip()}", file=sys.stderr)


def latest_tag(repo: Path) -> str | None:
    result = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def commits_since(repo: Path, tag: str | None) -> list[Commit]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    fmt = "%H%x1f%ad%x1f%s"
    result = run_git(
        repo,
        [
            "log",
            "--date=short",
            f"--pretty=format:{fmt}",
            "--no-merges",
            revision_range,
        ],
    )
    commits: list[Commit] = []
    for line in result.stdout.splitlines():
        parts = line.split("\x1f", 2)
        if len(parts) != 3:
            continue
        commits.append(Commit(sha=parts[0][:7], author_date=parts[1], subject=parts[2]))
    return commits


def categorize(subject: str) -> tuple[str, str]:
    match = CONVENTIONAL_RE.match(subject)
    if match:
        commit_type = match.group("type").lower()
        category = TYPE_TO_CATEGORY.get(commit_type, "Changed")
        message = match.group("message").strip()
        if match.group("breaking"):
            message = f"{message} (BREAKING)"
        return category, message

    for category, pattern in KEYWORD_RULES:
        if pattern.search(subject):
            return category, subject.strip()

    return "Changed", subject.strip()


def render_changelog(tag: str | None, commits: list[Commit]) -> str:
    today = dt.date.today().isoformat()
    base = tag or "beginning of history"
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORY_ORDER}

    for commit in commits:
        category, message = categorize(commit.subject)
        grouped[category].append(f"- {message} ({commit.sha})")

    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git commit history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"_Changes since {base}._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORY_ORDER:
        lines.append(f"### {category}")
        lines.extend(grouped[category] or ["- None"])
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from commits since the latest git tag."
    )
    parser.add_argument("--repo", default=".", help="Path to the git repository.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output Markdown file.")
    parser.add_argument("--since", help="Use a specific tag or revision instead of the latest tag.")
    parser.add_argument("--no-fetch", action="store_true", help="Do not run git fetch --tags first.")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog instead of writing it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 2

    if not args.no_fetch:
        maybe_fetch_tags(repo)

    tag = args.since if args.since else latest_tag(repo)
    changelog = render_changelog(tag, commits_since(repo, tag))

    if args.dry_run:
        print(changelog)
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
