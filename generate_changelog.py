#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Usage:
    python generate_changelog.py [--output CHANGELOG.md] [--since v1.0.0] [--repo /path/to/repo]

Categorizes commits into:
    - Added    (feat, add, new, introduce, implement)
    - Fixed    (fix, bugfix, hotfix, patch, resolve)
    - Changed  (update, refactor, improve, change, modify, chore, style)
    - Removed  (remove, delete, drop, deprecate, clean)

Unknown commits go under "Other".
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple

DEFAULT_OUTPUT = "CHANGELOG.md"

# Regex patterns for categorization
CATEGORIES = {
    "Added": re.compile(
        r"^(feat|feature|add|added|new|introduce|implement|create|build|init|setup)\b",
        re.IGNORECASE,
    ),
    "Fixed": re.compile(
        r"^(fix|fixed|bugfix|bug|hotfix|patch|resolve|solved|correct|repair|close)\b",
        re.IGNORECASE,
    ),
    "Changed": re.compile(
        r"^(update|updated|refactor|improve|improved|change|changed|modify|modified|chore|style|docs|doc|perf|optimize|enhance|tweak|upgrade|downgrade|bump)\b",
        re.IGNORECASE,
    ),
    "Removed": re.compile(
        r"^(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated|clean|cleanup|prune|strip)\b",
        re.IGNORECASE,
    ),
}


def run_git_log(repo_path: str, since_tag: str = None) -> List[Tuple[str, str, str, str]]:
    """Run git log and return list of (hash, date, author, message) tuples."""
    cmd = [
        "git", "-C", repo_path, "log",
        "--pretty=format:%H|%ai|%an|%s",
    ]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    else:
        cmd.append("--no-merges")  # exclude merge commits by default

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERR] git log failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append((parts[0], parts[1], parts[2], parts[3]))
    return commits


def get_latest_tag(repo_path: str) -> str:
    """Get the latest git tag, or None."""
    result = subprocess.run(
        ["git", "-C", repo_path, "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def categorize_commit(message: str) -> str:
    """Categorize a commit message into Added/Fixed/Changed/Removed/Other."""
    for category, pattern in CATEGORIES.items():
        if pattern.search(message):
            return category
    return "Other"


def group_commits(commits: List[Tuple[str, str, str, str]]) -> Dict[str, List[Tuple[str, str]]]:
    """Group commits by category."""
    groups: Dict[str, List[Tuple[str, str]]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Other": [],
    }
    for hash_, date, author, message in commits:
        category = categorize_commit(message)
        short_hash = hash_[:7]
        groups[category].append((short_hash, message))
    return groups


def generate_changelog(
    groups: Dict[str, List[Tuple[str, str]]],
    repo_name: str,
    output_path: str,
    since_tag: str = None,
) -> str:
    """Generate the CHANGELOG markdown content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tag_info = f" (since {since_tag})" if since_tag else ""

    lines = [
        f"# Changelog",
        "",
        f"All notable changes to this project will be documented in this file.",
        "",
        f"Generated on {now}{tag_info}.",
        "",
    ]

    # Order: Added, Changed, Fixed, Removed, Other
    order = ["Added", "Changed", "Fixed", "Removed", "Other"]

    for category in order:
        items = groups.get(category, [])
        if not items:
            continue
        lines.append(f"## {category}")
        lines.append("")
        for short_hash, message in items:
            # Clean up message for readability
            clean_msg = message.strip()
            lines.append(f"- {clean_msg} ({short_hash})")
        lines.append("")

    content = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return content


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the git repository (default: current directory)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Only include commits since this tag (e.g., v1.0.0)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all commits (including merges)",
    )
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo)
    if not os.path.exists(os.path.join(repo_path, ".git")):
        print(f"[ERR] Not a git repository: {repo_path}", file=sys.stderr)
        sys.exit(1)

    since_tag = args.since
    if not since_tag:
        since_tag = get_latest_tag(repo_path)
        if since_tag:
            print(f"[INFO] Auto-detected latest tag: {since_tag}")

    print(f"[INFO] Parsing git log from: {repo_path}")
    commits = run_git_log(repo_path, since_tag=since_tag)
    print(f"[INFO] Found {len(commits)} commits")

    groups = group_commits(commits)

    # Show summary
    total = 0
    for cat, items in groups.items():
        if items:
            print(f"  {cat}: {len(items)}")
            total += len(items)

    output_path = os.path.join(repo_path, args.output)
    content = generate_changelog(groups, os.path.basename(repo_path), output_path, since_tag)

    print(f"[PASS] CHANGELOG written to: {output_path}")
    print(f"[PASS] Total entries: {total}")


if __name__ == "__main__":
    main()
