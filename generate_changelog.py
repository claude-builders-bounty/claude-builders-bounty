#!/usr/bin/env python3
"""Generate CHANGELOG.md from git commit history.

Reads the repository's commit log and buckets each commit into
Added / Fixed / Changed / Removed based on a Conventional Commits
style prefix (feat, fix, refactor/change, remove/chore, etc.).
Commits that don't match a known prefix land in "Other".
"""

import subprocess
import sys
from collections import OrderedDict
from datetime import datetime

CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "change": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "style": "Changed",
    "docs": "Changed",
    "remove": "Removed",
    "delete": "Removed",
    "chore": "Removed",
}

CATEGORY_ORDER = ["Added", "Fixed", "Changed", "Removed", "Other"]


def get_commits():
    """Return list of (hash, subject, date) tuples, newest first."""
    result = subprocess.run(
        ["git", "log", "--pretty=format:%h|%s|%ad", "--date=short"],
        capture_output=True,
        text=True,
        check=True,
    )
    commits = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        commits.append(tuple(parts))
    return commits


def categorize(subject):
    prefix = subject.split(":", 1)[0].strip().lower()
    prefix = prefix.split("(", 1)[0].strip()  # handle "feat(scope): ..."
    return CATEGORY_MAP.get(prefix, "Other")


def clean_subject(subject):
    if ":" in subject:
        head, rest = subject.split(":", 1)
        prefix = head.split("(", 1)[0].strip().lower()
        if prefix in CATEGORY_MAP:
            return rest.strip()
    return subject.strip()


def build_changelog(commits):
    buckets = OrderedDict((cat, []) for cat in CATEGORY_ORDER)
    for commit_hash, subject, date in commits:
        category = categorize(subject)
        buckets[category].append((clean_subject(subject), commit_hash, date))

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project are documented in this file.",
        f"Generated on {datetime.now().strftime('%Y-%m-%d')} from git history.",
        "",
    ]

    for category in CATEGORY_ORDER:
        entries = buckets[category]
        if not entries:
            continue
        lines.append(f"## {category}")
        lines.append("")
        for subject, commit_hash, date in entries:
            lines.append(f"- {subject} (`{commit_hash}`, {date})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    try:
        commits = get_commits()
    except subprocess.CalledProcessError as exc:
        print(f"Error reading git log: {exc}", file=sys.stderr)
        sys.exit(1)

    if not commits:
        print("No commits found.", file=sys.stderr)
        sys.exit(1)

    changelog = build_changelog(commits)

    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog)

    print(f"Generated CHANGELOG.md from {len(commits)} commits.")
    print()
    print(changelog)


if __name__ == "__main__":
    main()
