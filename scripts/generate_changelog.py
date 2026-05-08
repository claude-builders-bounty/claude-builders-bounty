#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    author: str
    date: str


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def latest_tag() -> str | None:
    result = run_git(["describe", "--tags", "--abbrev=0"], check=False)
    tag = result.stdout.strip()
    return tag or None


def commits_since(tag: str | None) -> list[Commit]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    result = run_git(
        [
            "log",
            revision_range,
            "--pretty=format:%H%x1f%s%x1f%an%x1f%ad",
            "--date=short",
        ]
    )

    commits: list[Commit] = []
    for line in result.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        commits.append(Commit(*parts))
    return commits


def conventional_type(subject: str) -> str:
    match = re.match(r"^([a-zA-Z]+)(?:\([^)]+\))?!?:\s*(.+)$", subject)
    if not match:
        return ""
    return match.group(1).lower()


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject)
    return subject[:1].upper() + subject[1:] if subject else subject


def categorize(subject: str) -> str:
    lowered = subject.lower()
    ctype = conventional_type(subject)

    if ctype in {"feat", "feature"}:
        return "Added"
    if ctype in {"fix", "bugfix", "hotfix"}:
        return "Fixed"
    if ctype in {"remove", "removed"}:
        return "Removed"
    if ctype in {"refactor", "perf", "docs", "style", "test", "build", "ci", "chore"}:
        return "Changed"

    keyword_rules = [
        ("Removed", r"\b(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)\b"),
        ("Fixed", r"\b(fix|fixed|bug|bugfix|repair|resolve|resolved|patch)\b"),
        ("Added", r"\b(add|added|create|created|new|implement|implemented|introduce|introduced)\b"),
        ("Changed", r"\b(change|changed|update|updated|refactor|improve|improved|rename|renamed)\b"),
    ]
    for category, pattern in keyword_rules:
        if re.search(pattern, lowered):
            return category

    return "Changed"


def render_changelog(commits: list[Commit], tag: str | None) -> str:
    today = dt.date.today().isoformat()
    source = f"commits since `{tag}`" if tag else "all commits; no git tag was found"
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}

    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"_Source: {source}._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.append("")
        entries = grouped[category]
        if not entries:
            lines.append("- No changes.")
        else:
            for commit in entries:
                subject = clean_subject(commit.subject)
                lines.append(f"- {subject} (`{commit.sha[:7]}`, {commit.date})")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest git tag.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output path. Defaults to CHANGELOG.md")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file")
    args = parser.parse_args()

    tag = latest_tag()
    commits = commits_since(tag)
    changelog = render_changelog(commits, tag)

    if args.stdout:
        print(changelog)
        return 0

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output} from {len(commits)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
