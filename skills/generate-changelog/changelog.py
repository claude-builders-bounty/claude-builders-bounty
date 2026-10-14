#!/usr/bin/env python3
"""
Changelog Generator Engine
Fetches git commits since the last tag, categorizes into Added/Fixed/Changed/Removed,
and generates or updates CHANGELOG.md adhering to Keep a Changelog.
"""

import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

CATEGORIES = {
    "Added": [r"^feat(?:\([^\)]+\))?!?:", r"^add(?:\([^\)]+\))?!?:", r"^new(?:\([^\)]+\))?!?:", r"^initial\b"],
    "Fixed": [r"^fix(?:\([^\)]+\))?!?:", r"^bug(?:\([^\)]+\))?!?:", r"^patch(?:\([^\)]+\))?!?:", r"^resolve(?:\([^\)]+\))?!?:"],
    "Changed": [r"^refactor(?:\([^\)]+\))?!?:", r"^perf(?:\([^\)]+\))?!?:", r"^chore(?:\([^\)]+\))?!?:", r"^style(?:\([^\)]+\))?!?:", r"^update(?:\([^\)]+\))?!?:", r"^docs(?:\([^\)]+\))?!?:", r"^test(?:\([^\)]+\))?!?:", r"^ci(?:\([^\)]+\))?!?:", r"^build(?:\([^\)]+\))?!?:"],
    "Removed": [r"^revert(?:\([^\)]+\))?!?:", r"^remove(?:\([^\)]+\))?!?:", r"^delete(?:\([^\)]+\))?!?:", r"^deprecate(?:\([^\)]+\))?!?:"]
}

def get_last_tag() -> str:
    """Find the latest git tag, or empty string if no tag exists."""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return tag
    except Exception:
        return ""

def get_commits_since(tag: str = "") -> List[Tuple[str, str, str]]:
    """
    Returns list of tuples: (hash, author, message).
    """
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        raw_log = subprocess.check_output(
            ["git", "log", rev_range, "--pretty=format:%h%x09%an%x09%s"],
            text=True,
            errors="replace"
        ).strip()
    except Exception as e:
        sys.stderr.write(f"Warning: git log error: {e}\n")
        return []

    if not raw_log:
        return []

    commits = []
    for line in raw_log.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            commits.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return commits

def categorize_commit(msg: str) -> str:
    """Determines category based on conventional commit prefixes."""
    msg_clean = msg.strip()
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, msg_clean, re.IGNORECASE):
                return cat
    return "Changed"

def format_clean_message(msg: str) -> str:
    """Strips conventional commit prefix for clean presentation."""
    return re.sub(r"^[a-zA-Z0-9_\-\(\)]+!?:\s*", "", msg).strip()

def generate_changelog_section(tag: str, commits: List[Tuple[str, str, str]]) -> str:
    """Builds the Markdown section for the new changes."""
    today = datetime.now().strftime("%Y-%m-%d")
    version_title = f"## [Unreleased] - {today}" if not tag else f"## [Unreleased] (since {tag}) - {today}"

    bucketed: Dict[str, List[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for commit_hash, author, msg in commits:
        cat = categorize_commit(msg)
        clean_msg = format_clean_message(msg)
        bucketed[cat].append(f"- {clean_msg} ([`{commit_hash}`] - {author})")

    lines = [version_title, ""]
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = bucketed[cat]
        if items:
            lines.append(f"### {cat}")
            lines.extend(items)
            lines.append("")

    return "\n".join(lines).strip()

def update_or_create_changelog(section: str, output_path: Path):
    """Prepends the new section to CHANGELOG.md under the main title."""
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n"
    
    if output_path.exists():
        existing = output_path.read_text(encoding="utf-8")
        if "# Changelog" in existing:
            # Insert after the main header block
            pattern = r"(# Changelog.*?\n\n)"
            if re.search(pattern, existing, re.DOTALL):
                new_content = re.sub(pattern, rf"\1{section}\n\n", existing, count=1)
            else:
                new_content = f"{header}{section}\n\n{existing}"
        else:
            new_content = f"{header}{section}\n\n{existing}"
    else:
        new_content = f"{header}{section}\n"

    output_path.write_text(new_content, encoding="utf-8")

def main():
    repo_root = Path.cwd()
    output_file = repo_root / "CHANGELOG.md"

    last_tag = get_last_tag()
    commits = get_commits_since(last_tag)

    if not commits:
        print("No commits found since the last tag.")
        sys.exit(0)

    section = generate_changelog_section(last_tag, commits)
    update_or_create_changelog(section, output_file)
    print(f"Successfully updated {output_file} with {len(commits)} commits!")

if __name__ == "__main__":
    main()
