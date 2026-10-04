#!/usr/bin/env python3
"""
generate_changelog.py
=====================
Generates a structured CHANGELOG.md from git commit history.
Follows 'Keep a Changelog' standards (https://keepachangelog.com/).

Categories:
  - Added   : New features or capabilities
  - Fixed   : Bug fixes or patches
  - Changed : Changes in existing functionality, refactoring, chores
  - Removed : Removed features or deprecated items
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def get_latest_tag() -> Optional[str]:
    """Returns the most recent git tag, or None if no tags exist."""
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True
        )
        return r.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_git_commits(since_tag: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """
    Fetches git commits since tag (or all if since_tag is None).
    Returns list of (commit_hash, author_name, commit_message).
    """
    cmd = ["git", "log", "--pretty=format:%h|%an|%s"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = [line.strip() for line in r.stdout.splitlines() if line.strip()]
        commits = []
        for line in lines:
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append((parts[0], parts[1], parts[2]))
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Error reading git log: {e}", file=sys.stderr)
        return []


def categorize_commit(message: str) -> str:
    """
    Categorizes a commit message into: Added, Fixed, Changed, or Removed.
    Supports Conventional Commits syntax (e.g. feat:, fix:, chore:, refactor:)
    as well as plain-language prefixes.
    """
    msg_lower = message.lower().strip()

    # Fixed patterns
    if re.match(r"^(fix|bug|patch|resolve|close|fixed|fixing)(\([^)]+\))?:", msg_lower) or "fix" in msg_lower or "bug" in msg_lower:
        return "Fixed"

    # Removed patterns
    if re.match(r"^(remove|delete|deprecate|removed|deleting)(\([^)]+\))?:", msg_lower) or "remove" in msg_lower or "deprecate" in msg_lower:
        return "Removed"

    # Added patterns
    if re.match(r"^(feat|add|new|feature|added|adding)(\([^)]+\))?:", msg_lower) or "add" in msg_lower or "feat" in msg_lower:
        return "Added"

    # Default to Changed for chores, refactors, docs, updates, etc.
    return "Changed"


def clean_commit_message(message: str) -> str:
    """Strips conventional commit prefix for cleaner CHANGELOG bullets."""
    cleaned = re.sub(r"^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|add|remove|update)(\([^)]+\))?:\s*", "", message, flags=re.IGNORECASE)
    # Capitalize first letter
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def generate_markdown(
    commits: List[Tuple[str, str, str]],
    version_tag: str = "Unreleased",
    since_tag: Optional[str] = None
) -> str:
    """Formats categorized commits into Markdown adhering to Keep a Changelog."""
    categorized: Dict[str, List[Tuple[str, str, str]]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }

    for chash, author, msg in commits:
        category = categorize_commit(msg)
        categorized[category].append((chash, author, clean_commit_message(msg)))

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    header_since = f" (since {since_tag})" if since_tag else ""

    md_lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).",
        "",
        f"## [{version_tag}] - {date_str}{header_since}",
        "",
    ]

    total_items = 0
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categorized[cat]
        if items:
            md_lines.append(f"### {cat}")
            for chash, author, msg in items:
                md_lines.append(f"- {msg} (`{chash}` by {author})")
                total_items += 1
            md_lines.append("")

    if total_items == 0:
        md_lines.append("_No commits found in range._\n")

    return "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git log.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("-s", "--since", help="Git tag or commit to start from (default: latest tag)")
    parser.add_argument("-t", "--tag", default="Unreleased", help="Version tag name for section header")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing file")
    args = parser.parse_args()

    since_tag = args.since or get_latest_tag()
    commits = get_git_commits(since_tag)

    markdown = generate_markdown(commits, version_tag=args.tag, since_tag=since_tag)

    if args.stdout:
        print(markdown)
    else:
        out_path = Path(args.output)
        out_path.write_text(markdown, encoding="utf-8")
        print(f"✅ Generated {out_path} ({len(commits)} commits processed)")


if __name__ == "__main__":
    main()
