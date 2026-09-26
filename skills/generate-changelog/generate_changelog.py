#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git commit history.
Auto-categorizes commits into Added, Fixed, Changed, and Removed.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def get_latest_git_tag() -> str:
    """Retrieve the most recent git tag, or return empty string if no tags exist."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def get_git_commits(since_tag: str = "") -> List[Tuple[str, str, str]]:
    """
    Retrieve git commits (hash, author, subject) since the specified tag.
    If since_tag is empty, fetches all commits.
    """
    revision_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
    cmd = ["git", "log", revision_range, "--pretty=format:%h|%an|%s"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()
        commits = []
        for line in lines:
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append((parts[0], parts[1], parts[2]))
        return commits
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def categorize_commit(message: str) -> str:
    """
    Categorize commit message into: Added, Fixed, Changed, or Removed.
    Defaults to 'Changed' if uncategorized.
    """
    msg_lower = message.lower()
    
    # Conventional commit prefixes or keywords
    if re.search(r"^(feat|add|feature|new)(\(.*\))?:", msg_lower) or "add " in msg_lower or "added" in msg_lower:
        return "Added"
    elif re.search(r"^(fix|bugfix|patch)(\(.*\))?:", msg_lower) or "fix" in msg_lower or "fixed" in msg_lower or "bug" in msg_lower:
        return "Fixed"
    elif re.search(r"^(remove|deprecate|delete)(\(.*\))?:", msg_lower) or "remove" in msg_lower or "deleted" in msg_lower:
        return "Removed"
    else:
        return "Changed"


def build_changelog_markdown(categorized: Dict[str, List[Tuple[str, str, str]]], version: str = "Unreleased") -> str:
    """Generate Markdown content for CHANGELOG."""
    lines = [
        f"# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        f"## [{version}]",
        ""
    ]
    
    categories = ["Added", "Fixed", "Changed", "Removed"]
    has_entries = False
    
    for category in categories:
        entries = categorized.get(category, [])
        if entries:
            has_entries = True
            lines.append(f"### {category}")
            for commit_hash, author, subject in entries:
                lines.append(f"- {subject} (`{commit_hash}` by {author})")
            lines.append("")
            
    if not has_entries:
        lines.append("_No notable changes found._\n")
        
    return "\n".join(lines)


def generate_changelog(output_file: str = "CHANGELOG.md", target_tag: str = "") -> str:
    """Main workflow to generate CHANGELOG.md."""
    since_tag = target_tag if target_tag else get_latest_git_tag()
    commits = get_git_commits(since_tag)
    
    categorized: Dict[str, List[Tuple[str, str, str]]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for commit_hash, author, subject in commits:
        cat = categorize_commit(subject)
        categorized[cat].append((commit_hash, author, subject))
        
    version_label = f"Since {since_tag}" if since_tag else "Unreleased"
    content = build_changelog_markdown(categorized, version=version_label)
    
    if output_file:
        Path(output_file).write_text(content, encoding="utf-8")
        
    return content


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git commit history.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output Markdown file path (default: CHANGELOG.md)")
    parser.add_argument("-t", "--tag", default="", help="Git tag to start from (default: auto-detect latest tag)")
    args = parser.parse_args()
    
    content = generate_changelog(output_file=args.output, target_tag=args.tag)
    print(f"CHANGELOG successfully written to {args.output}")


if __name__ == "__main__":
    main()
