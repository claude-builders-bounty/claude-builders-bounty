#!/usr/bin/env python3
"""
📝 Automated Git Changelog Generator
Generates a clean, structured CHANGELOG.md from git commit history since the last release tag.
Follows the 'Keep a Changelog' standard (Added / Fixed / Changed / Removed).
"""

import subprocess
import sys
import os
import re
from datetime import datetime


def get_latest_tag():
    """Returns the latest git tag, or None if no tags exist."""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return tag
    except Exception:
        return None


def get_commits_since(tag=None):
    """Retrieves commit subjects and hashes since the given tag (or all commits if no tag)."""
    git_range = f"{tag}..HEAD" if tag else "HEAD"
    cmd = ["git", "log", git_range, "--no-merges", "--pretty=format:%h|%s"]
    try:
        output = subprocess.check_output(cmd, text=True).strip()
        if not output:
            return []
        commits = []
        for line in output.split("\n"):
            if "|" in line:
                sha, subject = line.split("|", 1)
                commits.append({"sha": sha.strip(), "message": subject.strip()})
        return commits
    except Exception as e:
        sys.stderr.write(f"Error reading git history: {e}\n")
        return []


def categorize_commit(message: str) -> str:
    """Categorizes a commit message into Added, Fixed, Changed, or Removed."""
    msg = message.lower()
    
    # Removed / Reverted
    if re.match(r"^(remove|deprecate|revert|drop|delete)", msg) or "remove" in msg:
        return "Removed"
    
    # Fixed / Bug fixes
    if re.match(r"^(fix|bug|patch|hotfix)", msg) or "fix" in msg:
        return "Fixed"
    
    # Added / Features
    if re.match(r"^(feat|add|new|implement)", msg) or "add" in msg:
        return "Added"
    
    # Changed / Refactoring / Docs / Chore
    return "Changed"


def clean_commit_message(message: str) -> str:
    """Cleans conventional commit prefixes (e.g., 'feat: add login' -> 'Add login')."""
    cleaned = re.sub(r"^(feat|fix|docs|style|refactor|perf|test|chore|build|ci)(\([^\)]+\))?:\s*", "", message, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    return cleaned[0].upper() + cleaned[1:] if cleaned else message


def generate_markdown(version: str, commits: list, last_tag: str = None) -> str:
    """Formats categorized commits into markdown changelog structure."""
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"## [{version}] - {today}\n"
    if last_tag:
        header += f"> Changes since release `{last_tag}`\n\n"
    else:
        header += f"> Initial release tracking\n\n"

    sections = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for c in commits:
        category = categorize_commit(c["message"])
        clean_msg = clean_commit_message(c["message"])
        sections[category].append(f"- {clean_msg} ([`{c['sha']}`])")

    content = header
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        if sections[cat]:
            content += f"### {cat}\n"
            for item in sections[cat]:
                content += f"{item}\n"
            content += "\n"

    return content


def update_changelog_file(new_section: str, output_path: str = "CHANGELOG.md"):
    """Prepends new release section to CHANGELOG.md preserving previous logs."""
    header_intro = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
    
    existing_content = ""
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    if existing_content.startswith("# Changelog"):
        # Strip header intro to avoid duplication
        body = re.sub(r"^# Changelog\s*\n\n.*?\n\n", "", existing_content, flags=re.DOTALL)
        final_content = header_intro + new_section + "\n" + body
    else:
        final_content = header_intro + new_section + "\n" + existing_content

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content.strip() + "\n")


def main():
    target_version = sys.argv[1] if len(sys.argv) > 1 else "Unreleased"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"

    latest_tag = get_latest_tag()
    commits = get_commits_since(latest_tag)

    if not commits:
        print(f"ℹ️ No new commits found since last tag: {latest_tag or 'initial commit'}.")
        sys.exit(0)

    print(f"🔍 Analyzing {len(commits)} commits since {latest_tag or 'repository start'}...")
    markdown = generate_markdown(target_version, commits, latest_tag)
    update_changelog_file(markdown, output_file)
    print(f"✅ Successfully updated {output_file}!")


if __name__ == "__main__":
    main()
