#!/usr/bin/env python3
"""
Generate Structured CHANGELOG from Git History
Parses git commits since the last tag (or from repository start) and categorizes them into:
- Added
- Fixed
- Changed
- Removed

Complies with the Keep a Changelog (https://keepachangelog.com) standard.
"""

import subprocess
import sys
import re
import os
from datetime import datetime, timezone
from pathlib import Path

# Conventional commit prefixes (stripped from output)
CONVENTIONAL_MAP = {
    "Added": ["feat", "feature", "add"],
    "Fixed": ["fix", "fixed", "bug", "bugfix", "patch", "hotfix"],
    "Removed": ["remove", "deprecate", "drop"],
    "Changed": ["change", "update", "refactor", "perf", "docs", "chore", "ci", "build", "test", "style"]
}

# Natural language start verbs (preserved in output)
NATURAL_MAP = {
    "Added": [r'\bimplement\b', r'\bcreate\b', r'\bintroduce\b', r'^\+'],
    "Fixed": [r'\bresolve\b', r'\bresolves\b', r'\bresolved\b', r'\bclose\b', r'\bcloses\b', r'\bclosed\b'],
    "Removed": [r'\bremove\b', r'\bremoved\b', r'\bdelete\b', r'\bdeleted\b', r'\bdeprecate\b', r'\bdeprecated\b'],
    "Changed": [r'\bupdate\b', r'\bmodify\b', r'\bupgrade\b', r'\boptimize\b', r'\brefactor\b']
}

def get_latest_tag() -> str | None:
    """Returns the latest git tag if available."""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return tag if tag else None
    except Exception:
        return None

def get_commits(since_tag: str | None = None) -> list[str]:
    """Retrieves commit subject lines since the specified tag or repository root."""
    try:
        git_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
        cmd = ["git", "log", git_range, "--no-merges", "--pretty=format:%h %s"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        if not output:
            return []
        return [line.strip() for line in output.split("\n") if line.strip()]
    except Exception:
        return []

def categorize_commit(commit_line: str) -> tuple[str, str, str]:
    """
    Categorizes a single commit into Added, Fixed, Changed, or Removed.
    Returns: (category, hash, clean_message)
    """
    parts = commit_line.split(" ", 1)
    commit_hash = parts[0]
    message = parts[1] if len(parts) > 1 else ""

    clean_message = message.strip()

    # 1. Check conventional commit style (e.g., feat(auth): add login -> Add login)
    conv_match = re.match(r'^([a-zA-Z]+)(?:\([^\)]+\))?:\s*(.+)$', clean_message)
    if conv_match:
        prefix = conv_match.group(1).lower()
        detail = conv_match.group(2).strip()
        for cat, prefixes in CONVENTIONAL_MAP.items():
            if prefix in prefixes:
                if detail:
                    detail = detail[0].upper() + detail[1:]
                return cat, commit_hash, detail
        # If prefix not in known, default to Changed
        if detail:
            detail = detail[0].upper() + detail[1:]
        return "Changed", commit_hash, detail

    # 2. Check natural language keywords (preserve full action description)
    for cat, patterns in NATURAL_MAP.items():
        for pat in patterns:
            if re.search(pat, clean_message, re.IGNORECASE):
                if clean_message:
                    clean_message = clean_message[0].upper() + clean_message[1:]
                return cat, commit_hash, clean_message

    # Fallback to Changed
    if clean_message:
        clean_message = clean_message[0].upper() + clean_message[1:]
    return "Changed", commit_hash, clean_message

def generate_changelog_content(
    version_title: str,
    categories: dict[str, list[str]],
    previous_tag: str | None = None
) -> str:
    """Formats categorized commits into Keep a Changelog Markdown format."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    header = f"## [{version_title}] - {today}"
    if previous_tag:
        header += f" (since {previous_tag})"

    sections = [header, ""]

    ordered_categories = ["Added", "Fixed", "Changed", "Removed"]

    has_any = False
    for cat in ordered_categories:
        items = categories.get(cat, [])
        if items:
            has_any = True
            sections.append(f"### {cat}")
            for item in items:
                sections.append(f"- {item}")
            sections.append("")

    if not has_any:
        sections.append("- Maintenance and documentation updates.\n")

    return "\n".join(sections).strip() + "\n"

def update_or_create_changelog_file(
    content: str,
    changelog_path: str = "CHANGELOG.md"
):
    """Inserts newly generated release notes at the top of CHANGELOG.md under # Changelog header."""
    header_block = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), "
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
    )

    if not os.path.exists(changelog_path):
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(header_block + content)
    else:
        with open(changelog_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        if "# Changelog" in existing_content:
            parts = existing_content.split("# Changelog", 1)
            after_header = parts[1].lstrip("\n")
            with open(changelog_path, "w", encoding="utf-8") as f:
                f.write(header_block + content + "\n---\n\n" + after_header)
        else:
            with open(changelog_path, "w", encoding="utf-8") as f:
                f.write(header_block + content + "\n---\n\n" + existing_content)

def main():
    version_title = "Unreleased"
    if len(sys.argv) > 1:
        version_title = sys.argv[1]

    latest_tag = get_latest_tag()
    commits = get_commits(latest_tag)

    categories: dict[str, list[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for commit in commits:
        cat, c_hash, clean_msg = categorize_commit(commit)
        categories[cat].append(f"{clean_msg} (`{c_hash}`)")

    output = generate_changelog_content(version_title, categories, latest_tag)
    update_or_create_changelog_file(output, "CHANGELOG.md")

    print(f"✅ Successfully generated CHANGELOG.md for [{version_title}] ({len(commits)} commits categorized)")
    print("\n--- Preview ---\n")
    print(output)

if __name__ == "__main__":
    main()
