#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORIES = {
    "Added": ("feat", "feature", "add", "added", "new"),
    "Fixed": ("fix", "bug", "bugfix", "repair", "patch"),
    "Changed": ("change", "changed", "refactor", "perf", "docs", "style", "test", "chore", "build", "ci"),
    "Removed": ("remove", "removed", "delete", "deleted", "drop", "deprecate", "deprecated"),
}


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def latest_tag(cwd: Path) -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def first_commit(cwd: Path) -> str:
    return run_git(["rev-list", "--max-parents=0", "HEAD"], cwd).splitlines()[0]


def collect_commits(cwd: Path, start_ref: str) -> list[Commit]:
    raw = run_git(["log", "--no-merges", "--pretty=format:%h%x09%s", f"{start_ref}..HEAD"], cwd)
    commits: list[Commit] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\t")
        commits.append(Commit(sha=sha, subject=subject.strip()))
    return commits


def normalize_subject(subject: str) -> str:
    cleaned = re.sub(r"^\w+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else subject


def category_for(subject: str) -> str:
    lowered = subject.lower()
    prefix = re.match(r"^(\w+)(?:\([^)]+\))?!?:", lowered)
    if prefix:
        token = prefix.group(1)
        for category, tokens in CATEGORIES.items():
            if token in tokens:
                return category

    for category, tokens in CATEGORIES.items():
        if any(lowered.startswith(token + " ") or lowered.startswith(token + ":") for token in tokens):
            return category
    return "Changed"


def group_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)
    return grouped


def render_changelog(commits: list[Commit], start_ref: str, version: str | None = None) -> str:
    heading = version or f"Unreleased - {date.today().isoformat()}"
    grouped = group_commits(commits)
    lines = [
        "# Changelog",
        "",
        "All notable changes are grouped from git commit history.",
        "",
        f"## {heading}",
        "",
        f"_Generated from commits after `{start_ref}`._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in ("Added", "Fixed", "Changed", "Removed"):
        lines.append(f"### {category}")
        entries = grouped[category]
        if entries:
            for commit in entries:
                lines.append(f"- {normalize_subject(commit.subject)} ({commit.sha})")
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits since the latest tag.")
    parser.add_argument("--from", dest="start_ref", help="Git ref/tag to start after. Defaults to latest tag or first commit.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path. Defaults to CHANGELOG.md")
    parser.add_argument("--version", help="Version heading. Defaults to Unreleased with today's date.")
    parser.add_argument("--repo", default=".", help="Repository path. Defaults to current directory.")
    args = parser.parse_args()

    cwd = Path(args.repo).resolve()
    start_ref = args.start_ref or latest_tag(cwd) or first_commit(cwd)
    commits = collect_commits(cwd, start_ref)
    changelog = render_changelog(commits, start_ref=start_ref, version=args.version)
    Path(args.output).write_text(changelog, encoding="utf-8")
    print(f"Wrote {args.output} from {len(commits)} commits after {start_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
