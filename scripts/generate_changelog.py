#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

By default this script reads commits since the latest reachable tag and writes
CHANGELOG.md in Keep a Changelog-style sections: Added, Fixed, Changed, Removed.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import OrderedDict
from datetime import date
from pathlib import Path

SECTIONS = ("Added", "Fixed", "Changed", "Removed")

CATEGORY_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("Added", re.compile(r"^(add|added|feat|feature|create|created|introduce|introduced)\b", re.I)),
    ("Fixed", re.compile(r"^(fix|fixed|bugfix|hotfix|resolve|resolved|repair|patched)\b", re.I)),
    ("Removed", re.compile(r"^(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)\b", re.I)),
    ("Changed", re.compile(r"^(change|changed|update|updated|refactor|refactored|improve|improved|perf|optimize|optimized|docs?|ci|test|chore)\b", re.I)),
]

CONVENTIONAL_TYPE_MAP = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "docs": "Changed",
    "test": "Changed",
    "ci": "Changed",
    "build": "Changed",
    "chore": "Changed",
    "revert": "Changed",
    "remove": "Removed",
}


def git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return result.stdout.strip()


def latest_tag(cwd: Path) -> str | None:
    try:
        tag = git(["describe", "--tags", "--abbrev=0"], cwd)
    except subprocess.CalledProcessError:
        return None
    return tag or None


def commit_range(cwd: Path, since: str | None) -> str:
    if since:
        return f"{since}..HEAD"
    tag = latest_tag(cwd)
    return f"{tag}..HEAD" if tag else "HEAD"


def commits(cwd: Path, rev_range: str) -> list[str]:
    try:
        output = git(["log", rev_range, "--pretty=format:%s"], cwd)
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^\w+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return subject[:1].upper() + subject[1:] if subject else subject


def categorize(subject: str) -> str:
    conventional = re.match(r"^(\w+)(?:\([^)]+\))?!?:", subject)
    if conventional:
        mapped = CONVENTIONAL_TYPE_MAP.get(conventional.group(1).lower())
        if mapped:
            return mapped

    cleaned = clean_subject(subject)
    for category, pattern in CATEGORY_RULES:
        if pattern.search(cleaned):
            return category
    return "Changed"


def render(commit_subjects: list[str], version: str, previous_tag: str | None) -> str:
    grouped: OrderedDict[str, list[str]] = OrderedDict((section, []) for section in SECTIONS)
    for subject in commit_subjects:
        grouped[categorize(subject)].append(clean_subject(subject))

    lines = ["# Changelog", "", "All notable changes to this project are documented in this file.", ""]
    heading = f"## {version} - {date.today().isoformat()}"
    if previous_tag:
        heading += f" (since {previous_tag})"
    lines.extend([heading, ""])

    if not commit_subjects:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for section, items in grouped.items():
        if not items:
            continue
        lines.extend([f"### {section}", ""])
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits.")
    parser.add_argument("--repo", default=".", help="Git repository path. Defaults to current directory.")
    parser.add_argument("--since", help="Starting git tag/ref. Defaults to latest tag.")
    parser.add_argument("--version", default="Unreleased", help="Version heading to write.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path. Use '-' for stdout.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    rev_range = commit_range(repo, args.since)
    previous = args.since or latest_tag(repo)
    content = render(commits(repo, rev_range), args.version, previous)

    if args.output == "-":
        print(content, end="")
    else:
        output = Path(args.output)
        if not output.is_absolute():
            output = repo / output
        output.write_text(content, encoding="utf-8")
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
