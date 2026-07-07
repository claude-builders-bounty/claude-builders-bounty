#!/usr/bin/env python3
"""
generate-changelog — Generate a structured CHANGELOG.md from git history.

Usage:
    python generate-changelog.py                    # Since last tag
    python generate-changelog.py --since v1.0.0     # Since specific tag
    python generate-changelog.py --all               # All commits
    python generate-changelog.py --output FILE       # Custom output path

Auto-categorizes commits into: Added / Fixed / Changed / Removed
Based on conventional commit prefixes and keyword heuristics.
"""

import subprocess
import sys
import re
import argparse
from datetime import datetime
from collections import defaultdict

CATEGORY_RULES = {
    "Added":   [r"^feat", r"^add", r"^new", r"^implement", r"^introduce"],
    "Fixed":   [r"^fix", r"^bug", r"^patch", r"^resolve", r"^hotfix", r"^correct"],
    "Changed": [r"^refactor", r"^update", r"^change", r"^tweak", r"^improve", r"^perf", r"^style", r"^ci", r"^build"],
    "Removed": [r"^remove", r"^drop", r"^deprecat", r"^delete"],
}

def get_commits(since_tag=None, all_commits=False):
    """Fetch commits from git history."""
    cmd = ["git", "log", "--oneline", "--no-merges"]

    if all_commits:
        pass  # all commits
    elif since_tag:
        cmd.extend([f"{since_tag}..HEAD"])
    else:
        # Since last tag
        try:
            last_tag = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"],
                stderr=subprocess.DEVNULL, text=True
            ).strip()
            cmd.extend([f"{last_tag}..HEAD"])
        except subprocess.CalledProcessError:
            pass  # No tags, use all commits

    try:
        output = subprocess.check_output(cmd, text=True).strip()
        if not output:
            return []
        return [line.strip() for line in output.split("\n")]
    except subprocess.CalledProcessError:
        return []


def categorize_commit(message):
    """Categorize a commit message into Added/Fixed/Changed/Removed."""
    msg_lower = message.lower()
    for category, patterns in CATEGORY_RULES.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return category
    return "Changed"  # default


def format_entry(line):
    """Format a commit line into a changelog entry."""
    # Remove the commit hash prefix
    match = re.match(r"^[a-f0-9]+\s+(.+)", line)
    if match:
        message = match.group(1)
    else:
        message = line
    return f"- {message}"


def generate_changelog(since_tag=None, all_commits=False):
    """Generate a complete CHANGELOG.md."""
    commits = get_commits(since_tag, all_commits)
    if not commits:
        return "# Changelog\n\nNo commits found.\n"

    categorized = defaultdict(list)
    for commit in commits:
        cat = categorize_commit(commit)
        categorized[cat].append(format_entry(commit))

    # Build output
    today = datetime.now().strftime("%Y-%m-%d")
    lines = ["# Changelog", ""]

    if since_tag:
        lines.append(f"## [{today}] — since {since_tag}")
    elif all_commits:
        lines.append(f"## [{today}] — Full History")
    else:
        try:
            last_tag = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"],
                stderr=subprocess.DEVNULL, text=True
            ).strip()
            lines.append(f"## [{today}] — since {last_tag}")
        except subprocess.CalledProcessError:
            lines.append(f"## [{today}]")

    lines.append("")

    for category in ["Added", "Fixed", "Changed", "Removed"]:
        entries = categorized.get(category, [])
        if entries:
            lines.append(f"### {category}")
            lines.extend(entries)
            lines.append("")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git history")
    parser.add_argument("--since", type=str, help="Tag to start from (e.g. v1.0.0)")
    parser.add_argument("--all", action="store_true", help="Include all commits")
    parser.add_argument("--output", "-o", type=str, default="CHANGELOG.md", help="Output file path")
    args = parser.parse_args()

    changelog = generate_changelog(since_tag=args.since, all_commits=args.all)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(changelog)

    print(f"✅ CHANGELOG.md generated ({len(changelog.splitlines())} lines)")
    print(f"📄 Output: {args.output}")


if __name__ == "__main__":
    main()
