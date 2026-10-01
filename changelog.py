#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History
Acceptance Criteria:
- Fetches commits since last git tag (or all if no tags)
- Auto-categorizes into: Added / Fixed / Changed / Removed
- Zero third-party dependencies (pure standard library)
"""
import subprocess
import re
import sys
from datetime import datetime

def get_last_tag():
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        return tag
    except Exception:
        return None

def get_commits(since_tag=None):
    cmd = ["git", "log", "--pretty=format:%H|||%s", "--no-merges"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    try:
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        commits = []
        for line in raw.strip().split("\n"):
            if "|||" in line:
                sha, msg = line.split("|||", 1)
                commits.append((sha.strip(), msg.strip()))
        return commits
    except Exception:
        return []

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    mapping = {
        "feat": "Added",
        "add": "Added",
        "fix": "Fixed",
        "bug": "Fixed",
        "change": "Changed",
        "refactor": "Changed",
        "perf": "Changed",
        "style": "Changed",
        "remove": "Removed",
        "deprecate": "Removed",
        "delete": "Removed"
    }
    
    for sha, msg in commits:
        matched = False
        short_sha = sha[:7]
        for prefix, target_cat in mapping.items():
            if re.match(rf"^{prefix}(\(.*\))?!?:?\s*", msg, re.IGNORECASE):
                clean_msg = re.sub(rf"^{prefix}(\(.*\))?!?:?\s*", "", msg, flags=re.IGNORECASE).strip()
                categories[target_cat].append(f"- {clean_msg} (`{short_sha}`)")
                matched = True
                break
        if not matched:
            categories["Changed"].append(f"- {msg} (`{short_sha}`)")
            
    return categories

def generate_markdown(categories, tag_info):
    now = datetime.now().strftime("%Y-%m-%d")
    version_header = f"## [{tag_info or 'Unreleased'}] - {now}"
    lines = ["# Changelog\n", "All notable changes to this project will be documented in this file.\n", version_header, ""]
    
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories[cat]
        if items:
            lines.append(f"### {cat}")
            lines.extend(items)
            lines.append("")
            
    return "\n".join(lines)

def main():
    last_tag = get_last_tag()
    commits = get_commits(last_tag)
    if not commits:
        commits = get_commits()
        
    categories = categorize_commits(commits)
    content = generate_markdown(categories, last_tag)
    
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"SUCCESS: Generated CHANGELOG.md ({len(commits)} commits processed)")

if __name__ == "__main__":
    main()
