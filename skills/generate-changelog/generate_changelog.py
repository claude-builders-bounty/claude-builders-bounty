#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git commit history.
Auto-categorizes commits since the latest git tag into: Added, Fixed, Changed, Removed.
Follows the 'Keep a Changelog' specification. Zero-dependency Python 3.8+.
"""

import subprocess
import sys
import os
import re
import argparse
from datetime import datetime
from collections import defaultdict
from pathlib import Path

CATEGORY_PATTERNS = {
    "Added": re.compile(r"^(feat|feature|add|create|new|implement)(\(.*\))?:\s*", re.IGNORECASE),
    "Fixed": re.compile(r"^(fix|bug|resolve|patch|hotfix)(\(.*\))?:\s*", re.IGNORECASE),
    "Removed": re.compile(r"^(remove|delete|drop|revert|deprecate)(\(.*\))?:\s*", re.IGNORECASE),
    "Changed": re.compile(r"^(change|refactor|perf|chore|style|docs|build|ci|test|update)(\(.*\))?:\s*", re.IGNORECASE),
}

def get_last_tag() -> str | None:
    """Returns the latest git tag name or None if no tags exist."""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return tag if tag else None
    except subprocess.CalledProcessError:
        return None

def get_commits_since(tag: str | None) -> list[tuple[str, str, str]]:
    """
    Returns a list of (commit_hash, author_name, commit_subject)
    from tag..HEAD (or all commits if tag is None).
    """
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    cmd = ["git", "log", revision_range, "--pretty=format:%h%x09%an%x09%s"]
    try:
        output = subprocess.check_output(cmd, text=True).strip()
        if not output:
            return []
        commits = []
        for line in output.splitlines():
            parts = line.split("\t", 2)
            if len(parts) == 3:
                commits.append((parts[0], parts[1], parts[2]))
        return commits
    except subprocess.CalledProcessError:
        return []

def categorize_commit(subject: str) -> tuple[str, str]:
    """Matches subject against conventions and returns (category, cleaned_message)."""
    for category, pattern in CATEGORY_PATTERNS.items():
        if pattern.search(subject):
            cleaned = pattern.sub("", subject).strip()
            if cleaned:
                cleaned = cleaned[0].upper() + cleaned[1:]
            return category, cleaned
            
    lower = subject.lower()
    if any(k in lower for k in ["add", "new", "feat", "support"]):
        return "Added", subject
    elif any(k in lower for k in ["fix", "bug", "issue", "resolve"]):
        return "Fixed", subject
    elif any(k in lower for k in ["remove", "delete", "drop"]):
        return "Removed", subject
    else:
        return "Changed", subject

def build_changelog(version: str, previous_tag: str | None, commits: list[tuple[str, str, str]]) -> str:
    """Generates markdown CHANGELOG section."""
    categorized = defaultdict(list)
    for chash, author, subject in commits:
        cat, msg = categorize_commit(subject)
        categorized[cat].append(f"- {msg} ([`{chash}`] - {author})")

    today = datetime.now().strftime("%Y-%m-%d")
    compare_note = f" (comparing against `{previous_tag}`)" if previous_tag else " (initial release)"
    
    lines = [
        f"## [{version}] - {today}{compare_note}",
        ""
    ]

    for section in ["Added", "Fixed", "Changed", "Removed"]:
        if categorized[section]:
            lines.append(f"### {section}")
            lines.extend(categorized[section])
            lines.append("")

    if not any(categorized.values()):
        lines.append("_No qualifying commits recorded in this release range._\n")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Automated Keep a Changelog Generator")
    parser.add_argument("version", nargs="?", default="Unreleased", help="Version label (e.g. v1.0.0)")
    parser.add_argument("--stdout", action="store_true", help="Print changelog section to stdout without modifying file")
    parser.add_argument("--since-tag", help="Explicitly specify starting git tag instead of autodetecting latest")
    parser.add_argument("--file", default="CHANGELOG.md", help="Target output file (default: CHANGELOG.md)")
    args = parser.parse_args()

    target_file = Path(args.file)
    last_tag = args.since_tag or get_last_tag()
    commits = get_commits_since(last_tag)

    if not commits:
        print(f"ℹ️ No new commits found since tag: {last_tag or 'beginning'}")
        return

    new_section = build_changelog(args.version, last_tag, commits)

    if args.stdout:
        print(new_section)
        return

    existing = ""
    if target_file.exists():
        existing = target_file.read_text(encoding="utf-8")
        header_match = re.match(r"(# Changelog\s*\n\s*All notable changes to this project.*?\n\n)", existing, re.DOTALL | re.IGNORECASE)
        if header_match:
            header = header_match.group(1)
            rest = existing[len(header):]
            final_content = header + new_section + "\n" + rest
        else:
            final_content = "# Changelog\n\n" + new_section + "\n" + existing
    else:
        final_content = (
            "# Changelog\n\n"
            "All notable changes to this project will be documented in this file.\n"
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"
            + new_section
        )

    target_file.write_text(final_content, encoding="utf-8")
    print(f"✅ Generated {len(commits)} commits into {target_file.resolve()} (Version: {args.version})")

if __name__ == "__main__":
    main()
