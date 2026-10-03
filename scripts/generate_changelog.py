#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History
Complies with Keep a Changelog standard (https://keepachangelog.com)
"""

import sys
import os
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Tuple

CATEGORIES = {
    "Added": [
        r"^feat(\(.*\))?:",
        r"^add\b",
        r"^implement\b",
        r"^new\b",
        r"^create\b"
    ],
    "Fixed": [
        r"^fix(\(.*\))?:",
        r"^bug\b",
        r"^patch\b",
        r"^resolve\b",
        r"^hotfix\b",
        r"^prevent\b"
    ],
    "Changed": [
        r"^refactor(\(.*\))?:",
        r"^perf(\(.*\))?:",
        r"^change\b",
        r"^update\b",
        r"^improve\b",
        r"^upgrade\b",
        r"^style(\(.*\))?:"
    ],
    "Removed": [
        r"^remove\b",
        r"^deprecate\b",
        r"^delete\b",
        r"^drop\b"
    ],
    "Security": [
        r"^sec(\(.*\))?:",
        r"^security\b",
        r"^vulnerability\b"
    ]
}

def run_git_command(args: List[str]) -> str:
    """Executes a git command and returns stdout."""
    try:
        res = subprocess.run(
            ["git"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""

def get_last_tag() -> str:
    """Finds the latest tag reachable from HEAD."""
    tag = run_git_command(["describe", "--tags", "--abbrev=0"])
    return tag

def get_commits_since(tag: str = "") -> List[Tuple[str, str, str]]:
    """
    Returns a list of (short_hash, author, subject) since the specified tag.
    If no tag, returns all commits from repository inception.
    """
    cmd = ["log", "--no-merges", "--pretty=format:%h|||%an|||%s"]
    if tag:
        cmd.append(f"{tag}..HEAD")
    raw = run_git_command(cmd)
    if not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        parts = line.split("|||")
        if len(parts) == 3:
            commits.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return commits

def categorize_commit(subject: str) -> Tuple[str, str]:
    """
    Categorizes commit message into Added, Fixed, Changed, Removed, Security, or Other.
    Cleans commit message for clean changelog display.
    """
    for category, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, subject, re.IGNORECASE):
                # Clean prefix (e.g. 'feat(auth): add login' -> 'add login')
                cleaned = re.sub(r"^[a-zA-Z]+(\([^)]+\))?:\s*", "", subject)
                # Capitalize first letter
                if cleaned:
                    cleaned = cleaned[0].upper() + cleaned[1:]
                return category, cleaned

    # Fallback category
    return "Changed", subject[0].upper() + subject[1:] if subject else subject

def generate_markdown(version: str, tag: str, categorized: Dict[str, List[Tuple[str, str, str]]]) -> str:
    """Formats categorized commits into Keep a Changelog Markdown."""
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"## [{version}] - {today}\n"
    if tag:
        header += f"*(Changes since git tag `{tag}`)*\n\n"
    else:
        header += "*(Initial release / un-tagged history)*\n\n"

    sections = []
    # Print in preferred standard order
    for cat in ["Added", "Fixed", "Changed", "Removed", "Security"]:
        items = categorized.get(cat, [])
        if items:
            sec_text = f"### {cat}\n"
            for short_hash, author, clean_subj in items:
                sec_text += f"- {clean_subj} ([`{short_hash}`] - {author})\n"
            sections.append(sec_text)

    if not sections:
        return header + "- Maintenance release and documentation updates.\n\n"

    return header + "\n".join(sections) + "\n"

def update_changelog_file(filepath: str, new_content: str):
    """Prepends new release section to CHANGELOG.md, preserving existing history."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing = f.read()

        # If CHANGELOG already has header
        if "# Changelog" in existing:
            parts = existing.split("# Changelog", 1)
            updated = "# Changelog\n\n" + new_content + parts[1].lstrip()
        else:
            updated = "# Changelog\n\n" + new_content + existing
    else:
        updated = (
            "# Changelog\n\n"
            "All notable changes to this project will be documented in this file.\n\n"
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\n"
            "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
            + new_content
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated)

def main():
    version = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "Unreleased"
    output_file = "CHANGELOG.md"

    # Check git repository
    if not os.path.exists(".git"):
        # Check if parent is git
        parent_git = run_git_command(["rev-parse", "--is-inside-work-tree"])
        if parent_git != "true":
            print("Error: Current directory is not a git repository.", file=sys.stderr)
            sys.exit(1)

    last_tag = get_last_tag()
    commits = get_commits_since(last_tag)

    if not commits:
        print("No new commits found since last tag.")
        sys.exit(0)

    categorized: Dict[str, List[Tuple[str, str, str]]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Security": []
    }

    for short_hash, author, subject in commits:
        cat, clean_msg = categorize_commit(subject)
        categorized[cat].append((short_hash, author, clean_msg))

    md_output = generate_markdown(version, last_tag, categorized)
    update_changelog_file(output_file, md_output)

    print(f"Successfully generated {output_file} for version [{version}]:")
    print("-" * 50)
    print(md_output.strip())
    print("-" * 50)

if __name__ == "__main__":
    main()
