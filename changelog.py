#!/usr/bin/env python3
"""changelog.py - Generate CHANGELOG.md from git history.

Usage:
    python3 changelog.py                    # Generate CHANGELOG.md from current repo
    python3 changelog.py /path/to/repo      # Generate from specified repo path
    python3 changelog.py --repo user/repo   # Generate from GitHub repo (requires git clone)

Output: CHANGELOG.md in the current directory
"""

import subprocess
import os
import sys
import re
from collections import defaultdict
from datetime import datetime


def get_last_tag():
    """Get the most recent git tag."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, cwd=repo_path
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def get_commits_since(tag=None):
    """Get commits since the given tag (or all commits if no tag)."""
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--oneline", "--format=%H|%s"]
    else:
        cmd = ["git", "log", "--oneline", "--format=%H|%s"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path)
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.strip().split("
") if line.strip()]
    except:
        pass
    return []


def get_commit_details(commit_hash):
    """Get detailed info for a commit."""
    try:
        result = subprocess.run(
            ["git", "show", "--format=%B", "--no-patch", commit_hash],
            capture_output=True, text=True, cwd=repo_path
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return ""


def categorize_commit(message):
    """Categorize a commit message into Added/Fixed/Changed/Removed."""
    msg_lower = message.lower()

    categories = {
        "Added": [r"^feat", r"^add", r"^feature", r"^implement", r"^create", r"^new"],
        "Fixed": [r"^fix", r"^bug", r"^hotfix", r"^patch", r"^correct"],
        "Changed": [r"^refactor", r"^update", r"^change", r"^improve", r"^optimize", r"^perf", r"^rework", r"^migrate"],
        "Removed": [r"^remove", r"^drop", r"^deprecate", r"^delete", r"^cleanup"],
    }

    for category, patterns in categories.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return category

    return "Changed"  # Default


def format_changelog(commits, tag):
    """Format changelog entries."""
    categorized = defaultdict(list)

    for line in commits:
        parts = line.split("|", 1)
        if len(parts) < 2:
            continue
        commit_hash, msg = parts[0], parts[1].strip()
        short_hash = commit_hash[:7]
        category = categorize_commit(msg)
        categorized[category].append((short_hash, msg))

    lines = []
    lines.append("# Changelog")
    lines.append("")
    lines.append(f"## [{tag or 'Initial release'}]")
    lines.append("")

    for category in ["Added", "Changed", "Fixed", "Removed"]:
        entries = categorized.get(category, [])
        if entries:
            lines.append(f"### {category}")
            for short_hash, msg in entries:
                # Remove conventional commit prefix for cleaner output
                clean_msg = re.sub(r"^(feat|fix|chore|docs|refactor|perf|test|ci|build|style)(\([^)]+\))?[!]?:?\s*", "", msg, flags=re.IGNORECASE)
                if not clean_msg:
                    clean_msg = msg
                lines.append(f"- {clean_msg} ({short_hash})")
            lines.append("")

    if not any(categorized.values()):
        lines.append("*No changes recorded*")
        lines.append("")

    return "
".join(lines)


def main():
    global repo_path
    repo_path = "."

    if len(sys.argv) > 1:
        repo_path = sys.argv[1]

    tag = get_last_tag()
    commits = get_commits_since(tag)

    if not commits:
        print("No commits found.")
        return

    changelog = format_changelog(commits, tag)

    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog)

    print(f"CHANGELOG.md generated with {len(commits)} commits since {'tag ' + tag if tag else 'beginning'}.")
    print(f"
Sample preview:")
    print(changelog[:500])


if __name__ == "__main__":
    main()
