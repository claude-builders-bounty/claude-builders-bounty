#!/usr/bin/env python3
import sys
import os
import subprocess
import re
from datetime import datetime

def get_git_commits(tag_range: str = None) -> list:
    """Fetches commit messages from git history."""
    if not tag_range:
        try:
            last_tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], stderr=subprocess.DEVNULL).decode('utf-8').strip()
            tag_range = f"{last_tag}..HEAD"
        except Exception:
            tag_range = "-n 30" # Fallback to last 30 commits if no tags exist

    cmd = ["git", "log", tag_range, "--pretty=format:%s|%h|%an|%ad", "--date=short"]
    try:
        raw = subprocess.check_output(cmd).decode('utf-8', errors='ignore')
        commits = []
        for line in raw.splitlines():
            if line.strip():
                parts = line.split('|')
                if len(parts) == 4:
                    commits.append({
                        "subject": parts[0],
                        "hash": parts[1],
                        "author": parts[2],
                        "date": parts[3]
                    })
        return commits
    except Exception as e:
        sys.stderr.write(f"Warning: Could not fetch git log: {e}\n")
        return []

def categorize_commits(commits: list) -> dict:
    """Categorizes commits into Added, Fixed, Changed, and Removed."""
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for c in commits:
        subj = c["subject"].strip()
        lower = subj.lower()

        if re.match(r'^(fix|bugfix|patch|resolve|fixed)\b', lower) or "fix" in lower:
            categories["Fixed"].append(c)
        elif re.match(r'^(feat|add|added|create|new)\b', lower) or "add" in lower:
            categories["Added"].append(c)
        elif re.match(r'^(remove|deprecate|delete)\b', lower) or "remove" in lower:
            categories["Removed"].append(c)
        else:
            categories["Changed"].append(c)

    return categories

def format_changelog(categories: dict, version: str = "Unreleased") -> str:
    """Formats categorized commits into a standard Keep A Changelog Markdown document."""
    today = datetime.now().strftime("%Y-%m-%d")
    md = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n## [{version}] - {today}\n"

    sections = ["Added", "Fixed", "Changed", "Removed"]
    has_entries = False

    for sec in sections:
        items = categories.get(sec, [])
        if items:
            has_entries = True
            md += f"\n### {sec}\n"
            for item in items:
                md += f"- {item['subject']} ([`{item['hash']}`])\n"

    if not has_entries:
        md += "\n- Maintenance updates and routine repository chores.\n"

    return md

def main():
    commits = get_git_commits()
    cat = categorize_commits(commits)
    changelog_md = format_changelog(cat)

    output_path = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(changelog_md)

    print(f"✅ Generated structured CHANGELOG to {output_path}")

if __name__ == "__main__":
    main()
