#!/usr/bin/env python3
"""
generate-changelog.py — Generate a structured CHANGELOG.md from git history.

Usage:
    python generate-changelog.py              # run in current repo
    python generate-changelog.py --since TAG  # generate since a specific tag
    python generate-changelog.py --output FILE  # change output file (default: CHANGELOG.md)

Accepts conventional commit prefixes:
    feat:, add:, fix:, bug:, change:, refactor:, remove:, drop:
Commits are auto-categorized into: Added / Fixed / Changed / Removed
"""

import argparse
import subprocess
import sys
from collections import OrderedDict

CATEGORIES = OrderedDict([
    ("Added", ["feat:", "add:", "Add:", "Added:"]),
    ("Fixed", ["fix:", "bug:", "Fix:", "Fixed:"]),
    ("Changed", ["change:", "chore:", "refactor:", "Change:", "Changed:"]),
    ("Removed", ["remove:", "drop:", "Remove:", "Removed:"]),
])


def get_commits(repo_path: str, since_tag: str | None = None) -> list[str]:
    """Get commit messages from git log."""
    cmd = ["git", "-C", repo_path, "log", "--pretty=format:%h %s", "--no-merges"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.strip().split("\n") if line]


def categorize_commit(msg: str) -> str:
    """Categorize a commit message based on its prefix."""
    for category, prefixes in CATEGORIES.items():
        for prefix in prefixes:
            if msg.lower().startswith(prefix.lower()):
                return category
    return "Other"


def get_latest_tag(repo_path: str) -> str | None:
    """Get the most recent git tag."""
    result = subprocess.run(
        ["git", "-C", repo_path, "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--repo-path", default=".", help="Path to the git repository")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--since", default=None, help="Generate changelog since this tag")
    args = parser.parse_args()

    repo_path = args.repo_path
    output_file = args.output
    since_tag = args.since

    # Verify it's a git repo
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--git-dir"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error: {repo_path} is not a git repository", file=sys.stderr)
        sys.exit(1)

    # Auto-detect latest tag if --since not provided
    if not since_tag:
        since_tag = get_latest_tag(repo_path)

    # Get commits
    commits = get_commits(repo_path, since_tag)

    # Categorize
    entries: dict[str, list[str]] = {cat: [] for cat in list(CATEGORIES.keys()) + ["Other"]}
    for commit in commits:
        hash_part = commit.split(" ")[0]
        msg = commit.split(" ", 1)[1] if " " in commit else commit
        cat = categorize_commit(msg)
        entries[cat].append(f"- {msg} ({hash_part})")

    # Write CHANGELOG.md
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Changelog\n\n")
        f.write("All notable changes to this project will be documented in this file.\n\n")
        if since_tag:
            f.write(f"> Generated since tag: `{since_tag}`\n\n")
        for category in list(CATEGORIES.keys()) + ["Other"]:
            if entries[category]:
                f.write(f"## {category}\n\n")
                for entry in entries[category]:
                    f.write(entry + "\n")
                f.write("\n")

    print(f"CHANGELOG generated at {output_file}")


if __name__ == "__main__":
    main()