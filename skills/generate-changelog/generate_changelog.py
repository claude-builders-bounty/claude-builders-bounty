#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History.
Parses conventional commits and groups them into:
- Added (feat)
- Fixed (fix)
- Changed (refactor, perf, style, chore)
- Removed (deprecate, revert, remove)
"""

import subprocess
import re
import sys
import datetime

def get_git_tag():
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return tag
    except Exception:
        return None

def get_commits(tag=None):
    cmd = ["git", "log", "--pretty=format:%h|%s|%an"]
    if tag:
        cmd.append(f"{tag}..HEAD")
    output = subprocess.check_output(cmd, text=True, errors="replace")
    commits = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({"hash": parts[0], "subject": parts[1], "author": parts[2]})
    return commits

def parse_commit(subject):
    pattern = r"^([a-zA-Z]+)(?:\(([^)]+)\))?!?: (.+)$"
    match = re.match(pattern, subject)
    if match:
        ctype, scope, desc = match.groups()
        return ctype.lower(), scope, desc
    return "other", None, subject

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    type_map = {
        "feat": "Added",
        "fix": "Fixed",
        "perf": "Changed",
        "refactor": "Changed",
        "style": "Changed",
        "docs": "Changed",
        "chore": "Changed",
        "revert": "Removed",
        "remove": "Removed",
        "deprecated": "Removed"
    }

    for c in commits:
        ctype, scope, desc = parse_commit(c["subject"])
        target_cat = type_map.get(ctype, "Changed")
        scope_prefix = f"**{scope}:** " if scope else ""
        entry = f"- {scope_prefix}{desc} (`{c['hash']}`)"
        categories[target_cat].append(entry)

    return categories

def generate_markdown(version, categories):
    today = datetime.date.today().isoformat()
    lines = [f"## [{version}] - {today}\n"]
    
    for section in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories.get(section, [])
        if items:
            lines.append(f"### {section}\n")
            lines.extend([item + "\n" for item in items])
            lines.append("\n")
            
    return "".join(lines)

def main():
    tag = get_git_tag()
    commits = get_commits(tag)
    version = sys.argv[1] if len(sys.argv) > 1 else ("Unreleased" if not tag else f"vNext (after {tag})")
    
    if not commits:
        print("No new commits found since last tag.")
        return

    categories = categorize_commits(commits)
    changelog_content = generate_markdown(version, categories)
    print(changelog_content)

    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write("# Changelog\n\n" + changelog_content)
    print("Successfully wrote to CHANGELOG.md")

if __name__ == "__main__":
    main()
