#!/usr/bin/env python3
"""
Structured Git Changelog Generator
Generates CHANGELOG.md following Keep a Changelog & Conventional Commits standards.
Solves Bounty #1 ($50) in claude-builders-bounty.
"""

import subprocess
import re
import sys
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "Added": [r"^feat(?:\(.*\))?!?:", r"^add(?:\(.*\))?!?:", r"^new(?:\(.*\))?!?:"],
    "Fixed": [r"^fix(?:\(.*\))?!?:", r"^bug(?:\(.*\))?!?:", r"^patch(?:\(.*\))?!?:"],
    "Changed": [r"^refactor(?:\(.*\))?!?:", r"^perf(?:\(.*\))?!?:", r"^style(?:\(.*\))?!?:", r"^chore(?:\(.*\))?!?:", r"^build(?:\(.*\))?!?:", r"^ci(?:\(.*\))?!?:"],
    "Removed": [r"^remove(?:\(.*\))?!?:", r"^deprecate(?:\(.*\))?!?:", r"^revert(?:\(.*\))?!?:"],
}

def get_last_tag() -> str:
    """Returns the most recent git tag, or empty string if no tags exist."""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        return tag
    except Exception:
        return ""

def get_commits_since(tag: str = "") -> list[tuple[str, str, str]]:
    """Fetches commit hash, author date, and subject since tag."""
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        raw_log = subprocess.check_output(
            ["git", "log", revision_range, "--no-merges", "--pretty=tformat:%h|%as|%s"],
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        if not raw_log:
            return []
        
        commits = []
        for line in raw_log.splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append((parts[0], parts[1], parts[2]))
        return commits
    except Exception as e:
        print(f"Error reading git log: {e}", file=sys.stderr)
        return []

def categorize_commits(commits: list[tuple[str, str, str]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    grouped["Other"] = []

    for commit_hash, _, subject in commits:
        matched = False
        clean_msg = subject
        for category, patterns in CATEGORIES.items():
            for pat in patterns:
                if re.search(pat, subject, re.IGNORECASE):
                    # Strip convention prefix for cleaner changelog
                    clean_msg = re.sub(pat, "", subject, flags=re.IGNORECASE).strip()
                    # Capitalize first letter
                    if clean_msg:
                        clean_msg = clean_msg[0].upper() + clean_msg[1:]
                    grouped[category].append(f"{clean_msg} (`{commit_hash}`)")
                    matched = True
                    break
            if matched:
                break
        if not matched:
            grouped["Other"].append(f"{subject} (`{commit_hash}`)")

    return grouped

def generate_markdown(tag: str, grouped: dict[str, list[str]]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    version_title = f"## [{tag or 'Unreleased'}] - {today}\n"

    sections = []
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = grouped.get(cat, [])
        if items:
            section = f"### {cat}\n" + "\n".join(f"- {item}" for item in items)
            sections.append(section)

    if grouped.get("Other"):
        sections.append("### Other Changes\n" + "\n".join(f"- {item}" for item in grouped["Other"]))

    if not sections:
        return version_title + "\n- No notable changes recorded.\n"

    return version_title + "\n" + "\n\n".join(sections) + "\n"

def main():
    tag = get_last_tag()
    commits = get_commits_since(tag)
    
    if not commits:
        print("No new commits found since last tag.")
        return

    grouped = categorize_commits(commits)
    new_entry = generate_markdown(tag, grouped)

    changelog_path = Path("CHANGELOG.md")
    if changelog_path.exists():
        existing_content = changelog_path.read_text(encoding="utf-8")
        if existing_content.lstrip().startswith("# Changelog"):
            lines = existing_content.splitlines(keepends=True)
            insert_at = next(
                (i + 1 for i, line in enumerate(lines) if line.strip() == "# Changelog"),
                1,
            )
            updated = (
                "".join(lines[:insert_at]).rstrip("\r\n")
                + f"\n\n{new_entry}\n"
                + "".join(lines[insert_at:]).lstrip("\r\n")
            )
        else:
            updated = f"# Changelog\n\n{new_entry}\n" + existing_content
    else:
        updated = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{new_entry}"

    changelog_path.write_text(updated, encoding="utf-8", newline="\n")
    print(f"Successfully updated CHANGELOG.md ({len(commits)} commits processed).")

if __name__ == "__main__":
    main()
