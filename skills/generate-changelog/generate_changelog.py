#!/usr/bin/env python3
"""Generate a Markdown changelog from commits since the latest git tag."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
COMMIT_TYPES = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "change": "Changed",
    "changed": "Changed",
    "chore": "Changed",
    "docs": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "style": "Changed",
    "test": "Changed",
    "ci": "Changed",
    "build": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
    "deprecate": "Removed",
}
MERGE_RE = re.compile(r"^Merge\b", re.IGNORECASE)
CONVENTIONAL_RE = re.compile(r"^(?P<kind>[a-zA-Z]+)(?:\([^)]+\))?(?P<breaking>!)?:\s*(?P<subject>.+)$")


@dataclass(frozen=True)
class Commit:
    short_hash: str
    subject: str


def run_git(args: list[str], cwd: Path | None = None, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def latest_tag(cwd: Path | None = None) -> str | None:
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd, check=False)
    return tag or None


def commit_range(tag: str | None) -> str:
    return f"{tag}..HEAD" if tag else "HEAD"


def read_commits(tag: str | None = None, cwd: Path | None = None) -> list[Commit]:
    output = run_git(
        ["log", "--no-merges", "--pretty=format:%h%x09%s", commit_range(tag)],
        cwd=cwd,
        check=False,
    )
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        short_hash, _, subject = line.partition("\t")
        if not subject or MERGE_RE.match(subject):
            continue
        commits.append(Commit(short_hash=short_hash, subject=subject.strip()))
    return commits


def normalize_subject(subject: str) -> tuple[str, str]:
    match = CONVENTIONAL_RE.match(subject)
    if not match:
        return "Changed", sentence_case(subject)

    kind = match.group("kind").lower()
    category = COMMIT_TYPES.get(kind, "Changed")
    text = sentence_case(match.group("subject"))
    if match.group("breaking"):
        text = f"{text} (breaking)"
    return category, text


def sentence_case(value: str) -> str:
    value = value.strip().rstrip(".")
    if not value:
        return value
    return value[0].upper() + value[1:]


def categorize(commits: Iterable[Commit]) -> dict[str, list[Commit]]:
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        category, text = normalize_subject(commit.subject)
        grouped[category].append(Commit(short_hash=commit.short_hash, subject=text))
    return grouped


def render_changelog(
    grouped: dict[str, list[Commit]],
    version: str,
    since_tag: str | None,
    date: dt.date | None = None,
) -> str:
    date = date or dt.date.today()
    lines = [
        "# Changelog",
        "",
        f"## {version} - {date.isoformat()}",
        "",
    ]

    if since_tag:
        lines.extend([f"Changes since `{since_tag}`.", ""])
    else:
        lines.extend(["Changes from the full repository history.", ""])

    wrote_entry = False
    for category in CATEGORIES:
        commits = grouped.get(category, [])
        if not commits:
            continue
        wrote_entry = True
        lines.extend([f"### {category}", ""])
        for commit in commits:
            lines.append(f"- {commit.subject} ({commit.short_hash})")
        lines.append("")

    if not wrote_entry:
        lines.extend(["No changes found.", ""])

    return "\n".join(lines).rstrip() + "\n"


def generate(version: str, cwd: Path | None = None) -> str:
    tag = latest_tag(cwd=cwd)
    commits = read_commits(tag=tag, cwd=cwd)
    return render_changelog(categorize(commits), version=version, since_tag=tag)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("output", nargs="?", default="CHANGELOG.md", help="Output file path.")
    parser.add_argument("version", nargs="?", default="Unreleased", help="Version heading.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.write_text(generate(args.version), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
