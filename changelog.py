#!/usr/bin/env python3
"""generate-changelog: Generate a structured CHANGELOG.md from git history.

Usage:
    python3 changelog.py [--tag TAG] [--output FILE] [--repo PATH]

Options:
    --tag TAG       Starting tag (default: last git tag, or all commits)
    --output FILE   Output file path (default: CHANGELOG.md)
    --repo PATH     Repository path (default: current directory)
"""

import subprocess
import re
import sys
import os
import argparse
from datetime import datetime

# Commit message patterns for categorization
PATTERNS = {
    "Added": [
        r"(?i)^add(?:ed|s)?\b",
        r"(?i)^feat(?:ure)?\b",
        r"(?i)^new\b",
        r"(?i)^introduce\b",
        r"(?i)^implement(?:ed|s)?\b",
        r"(?i)^create(?:d|s)?\b",
    ],
    "Fixed": [
        r"(?i)^fix(?:es|ed)?\b",
        r"(?i)^bug(?:fix)?\b",
        r"(?i)^patch(?:ed|es)?\b",
        r"(?i)^resolve(?:d|s)?\b",
        r"(?i)^repair(?:ed|s)?\b",
        r"(?i)^correct(?:ed|s)?\b",
    ],
    "Changed": [
        r"(?i)^change(?:d|s)?\b",
        r"(?i)^update(?:d|s)?\b",
        r"(?i)^refactor(?:ed|s|ing)?\b",
        r"(?i)^improve(?:d|s)?\b",
        r"(?i)^enhance(?:d|s)?\b",
        r"(?i)^modify\b",
        r"(?i)^adjust(?:ed|s)?\b",
        r"(?i)^rewrite\b",
    ],
    "Removed": [
        r"(?i)^remov(?:e|ed|es|ing)?\b",
        r"(?i)^delet(?:e|ed|es|ing)?\b",
        r"(?i)^drop(?:ped|s|ping)?\b",
        r"(?i)^clean(?:s|ed|up)?\b",
        r"(?i)^revert(?:ed|s)?\b",
        r"(?i)^deprecate(?:d|s)?\b",
    ],
}

# Patterns that should be ignored (merge commits, etc.)
IGNORE_PATTERNS = [
    r"^Merge\s",
    r"^Revert\s",
    r"^Bump\s",
    r"^chore\s*:\s*release",
    r"^chore\s*:\s*bump",
]


def get_last_tag(repo_path="."):
    """Get the most recent git tag."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-creatordate"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        tags = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
        return tags[0] if tags else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_commits_since_tag(tag=None, repo_path="."):
    """Get commits since the given tag (or all commits)."""
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%H|%s|%ad", "--date=short"]
    else:
        cmd = ["git", "log", "--pretty=format:%H|%s|%ad", "--date=short"]

    try:
        result = subprocess.run(
            cmd, cwd=repo_path, capture_output=True, text=True, check=True
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append({
                    "hash": parts[0][:8],
                    "subject": parts[1],
                    "date": parts[2],
                })
        return commits
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: git command failed. Make sure you are in a git repository.", file=sys.stderr)
        sys.exit(1)


def categorize_commit(subject):
    """Categorize a commit message into Added/Fixed/Changed/Removed."""
    for ignore_pattern in IGNORE_PATTERNS:
        if re.match(ignore_pattern, subject):
            return None

    for category, patterns in PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, subject):
                return category

    return "Changed"  # Default fallback


def format_changelog(commits, tag=None):
    """Format commits into a structured CHANGELOG.md string."""
    categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}

    for commit in commits:
        category = categorize_commit(commit["subject"])
        if category:
            categories[category].append(commit)

    today = datetime.now().strftime("%Y-%m-%d")
    tag_label = tag if tag else "Initial"

    lines = []
    lines.append(f"## [{tag_label}] - {today}")
    lines.append("")

    for category in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories[category]
        if not items:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for item in items:
            lines.append(f"- {item['subject']} ({item['hash']})")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history"
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Starting tag (default: last git tag, or all commits)",
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Repository path (default: current directory)",
    )
    args = parser.parse_args()

    tag = args.tag
    if tag is None:
        tag = get_last_tag(args.repo)

    commits = get_commits_since_tag(tag, args.repo)

    if not commits:
        print(f"No new commits found since {tag or 'beginning'}.", file=sys.stderr)
        sys.exit(0)

    changelog = format_changelog(commits, tag)

    # If output file exists, prepend new entries
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            existing = f.read()
        full_content = changelog + "\n" + existing
    else:
        header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        full_content = header + changelog

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"CHANGELOG.md generated successfully!")
    print(f"  - Tag: {tag or 'N/A'}")
    print(f"  - Commits processed: {len(commits)}")
    print(f"  - Output: {args.output}")


if __name__ == "__main__":
    main()