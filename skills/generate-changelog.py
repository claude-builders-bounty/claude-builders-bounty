#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

import subprocess
import re
import sys
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "Added": [r"^feat", r"^add", r"^\+", r"^new"],
    "Fixed": [r"^fix", r"^bug", r"^patch", r"^resolve"],
    "Changed": [r"^refactor", r"^update", r"^modify", r"^change", r"^improve"],
    "Removed": [r"^remove", r"^delete", r"^-", r"^deprecate"],
}

def get_last_tag():
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", "HEAD~1"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None

def get_commits_since(tag=None):
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%s"]
    else:
        cmd = ["git", "log", "--pretty=format:%s", "-50"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().split("\n")
    return []

def categorize_commit(message):
    msg_lower = message.lower()
    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if re.match(pattern, msg_lower):
                return category
    return "Changed"

def generate_changelog(commits, version=None):
    if not version:
        version = datetime.now().strftime("%Y.%m.%d")
    
    categorized = {cat: [] for cat in CATEGORIES}
    for commit in commits:
        if commit.strip():
            cat = categorize_commit(commit)
            categorized[cat].append(commit.strip())
    
    lines = [f"# Changelog", "", f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}", ""]
    
    for category in CATEGORIES:
        items = categorized[category]
        if items:
            lines.append(f"### {category}")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
    
    return "\n".join(lines)

def main():
    tag = get_last_tag()
    commits = get_commits_since(tag)
    
    if not commits or commits == [""]:
        print("No commits found since last tag.")
        sys.exit(1)
    
    changelog = generate_changelog(commits, tag)
    
    output_path = Path("CHANGELOG.md")
    output_path.write_text(changelog, encoding="utf-8")
    print(f"Generated {output_path.absolute()}")
    print(changelog)

if __name__ == "__main__":
    main()