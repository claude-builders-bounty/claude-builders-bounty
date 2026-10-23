#!/usr/bin/env python3
"""
changelog.py — Cross-platform generator for Keep a Changelog from git history.
Works seamlessly across Windows, Linux, and macOS.
"""
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

CATEGORY_PATTERNS = [
    ("Added", re.compile(r"^(feat|feature|add|new)(\([^)]+\))?!?:?\s*(.+)$", re.IGNORECASE)),
    ("Fixed", re.compile(r"^(fix|bug|patch|hotfix)(\([^)]+\))?!?:?\s*(.+)$", re.IGNORECASE)),
    ("Removed", re.compile(r"^(revert|remove|deprecate|drop)(\([^)]+\))?!?:?\s*(.+)$", re.IGNORECASE)),
    ("Changed", re.compile(r"^(refactor|perf|chore|docs|style|update|change)(\([^)]+\))?!?:?\s*(.+)$", re.IGNORECASE)),
]

def get_latest_tag() -> str:
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return tag
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""

def get_commits(since_tag: str = "") -> List[Tuple[str, str, str]]:
    cmd = ["git", "log", "--pretty=format:%s|%h|%an"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        commits = []
        for line in output.splitlines():
            parts = line.strip().split("|", 2)
            if len(parts) == 3:
                commits.append((parts[0], parts[1], parts[2]))
        return commits
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def categorize_commits(commits: List[Tuple[str, str, str]]) -> Dict[str, List[str]]:
    categorized: Dict[str, List[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }

    for msg, h, author in commits:
        matched = False
        for category, pattern in CATEGORY_PATTERNS:
            match = pattern.match(msg)
            if match:
                clean_msg = match.group(3).strip()
                categorized[category].append(f"- {clean_msg} (`{h}` by {author})")
                matched = True
                break
        if not matched:
            categorized["Changed"].append(f"- {msg} (`{h}` by {author})")

    return categorized

def build_changelog_section(categorized: Dict[str, List[str]], tag: str = "", date_str: str = "") -> str:
    date_str = date_str or datetime.utcnow().strftime("%Y-%m-%d")
    header = f"## [Unreleased] - {date_str}"
    if tag:
        header += f" (since {tag})"
    
    lines = [header, ""]
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categorized.get(cat, [])
        if items:
            lines.append(f"### {cat}")
            lines.extend(items)
            lines.append("")
    return "\n".join(lines).strip() + "\n"

def update_changelog_file(filepath: Path, new_section: str):
    header = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/).\n\n"
    )
    if not filepath.exists():
        filepath.write_text(header + new_section, encoding="utf-8")
        return

    content = filepath.read_text(encoding="utf-8")
    if "# Changelog" in content:
        parts = content.split("# Changelog", 1)
        # Find where header ends and versions start
        subparts = parts[1].split("## ", 1)
        if len(subparts) == 2:
            updated = f"# Changelog{subparts[0]}\n{new_section}\n## {subparts[1]}"
        else:
            updated = f"# Changelog{subparts[0]}\n\n{new_section}"
    else:
        updated = f"{new_section}\n\n{content}"

    filepath.write_text(updated, encoding="utf-8")

def main():
    target_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("CHANGELOG.md")
    tag = get_latest_tag()
    commits = get_commits(tag)
    if not commits:
        print("No new commits found.")
        return 0
    categorized = categorize_commits(commits)
    section = build_changelog_section(categorized, tag)
    update_changelog_file(target_file, section)
    print(f"Successfully generated {target_file}.")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
