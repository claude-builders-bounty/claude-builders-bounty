#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def last_tag(repo: Path) -> str | None:
    result = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def commits_since(repo: Path, base_ref: str | None) -> list[Commit]:
    revision = f"{base_ref}..HEAD" if base_ref else "HEAD"
    result = run_git(
        repo,
        ["log", "--no-merges", "--pretty=format:%H%x1f%s%x1f%b%x1e", revision],
    )
    raw = result.stdout.strip("\x1e\n")
    if not raw:
        return []

    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        parts = record.strip("\n").split("\x1f", 2)
        if len(parts) != 3:
            continue
        commits.append(Commit(parts[0], parts[1].strip(), parts[2].strip()))
    return commits


def clean_subject(subject: str) -> str:
    cleaned = re.sub(
        r"^(feat|fix|change|changed|refactor|perf|docs|style|test|tests|build|ci|chore|remove|removed|delete|deleted)(\([^)]+\))?!?:\s*",
        "",
        subject,
        flags=re.IGNORECASE,
    ).strip()
    if not cleaned:
        cleaned = subject.strip()
    return cleaned[:1].upper() + cleaned[1:]


def categorize(subject: str) -> str:
    lowered = subject.lower()
    conventional = re.match(r"^([a-z]+)(\([^)]+\))?!?:", lowered)
    prefix = conventional.group(1) if conventional else ""

    if prefix in {"feat", "add", "added"} or re.search(r"\b(add|adds|added|introduce|new)\b", lowered):
        return "Added"
    if prefix == "fix" or re.search(r"\b(fix|fixes|fixed|bug|bugfix|patch|repair)\b", lowered):
        return "Fixed"
    if prefix in {"remove", "removed", "delete", "deleted"} or re.search(
        r"\b(remove|removes|removed|delete|deletes|deleted|drop|deprecate)\b",
        lowered,
    ):
        return "Removed"
    return "Changed"


def format_entry(commit: Commit) -> str:
    return f"- {clean_subject(commit.subject)} ({commit.sha[:7]})"


def build_changelog(commits: list[Commit], base_ref: str | None, version: str) -> str:
    grouped = {category: [] for category in CATEGORIES}
    for commit in reversed(commits):
        grouped[categorize(commit.subject)].append(format_entry(commit))

    base_label = f"since `{base_ref}`" if base_ref else "from full history (no git tag found)"
    lines = [
        "# Changelog",
        "",
        f"## {version} - {date.today().isoformat()}",
        "",
        f"Generated from commits {base_label}.",
        "",
    ]
    for category in CATEGORIES:
        lines.append(f"### {category}")
        entries = grouped[category]
        if entries:
            lines.extend(entries)
        else:
            lines.append("- No changes.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=".",
        help="Git repository path to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--from-ref",
        help="Override the base ref/tag. Defaults to the latest reachable git tag.",
    )
    parser.add_argument(
        "--version",
        default="Unreleased",
        help="Changelog version heading. Defaults to Unreleased.",
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Output file path. Defaults to CHANGELOG.md inside --repo.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated changelog instead of writing it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 2

    base_ref = args.from_ref or last_tag(repo)
    commits = commits_since(repo, base_ref)
    changelog = build_changelog(commits, base_ref, args.version)

    if args.dry_run:
        print(changelog, end="")
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
