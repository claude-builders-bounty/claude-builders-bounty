#!/usr/bin/env python3
"""
Structured Git Changelog Generator
Generates Keepachangelog-compliant CHANGELOG.md from git history.
Works standalone or via Claude Code skill / bash.
"""

import sys
import re
import subprocess
from datetime import datetime
from pathlib import Path

CATEGORY_PATTERNS = {
    "Added": [
        r"^feat(\(.*\))?:",
        r"^add(\b|:)",
        r"^new(\b|:)",
        r"^create(\b|:)"
    ],
    "Fixed": [
        r"^fix(\(.*\))?:",
        r"^bug(\(.*\))?:",
        r"^patch(\(.*\))?:",
        r"^resolve(\b|:)"
    ],
    "Changed": [
        r"^refactor(\(.*\))?:",
        r"^perf(\(.*\))?:",
        r"^chore(\(.*\))?:",
        r"^style(\(.*\))?:",
        r"^update(\b|:)",
        r"^change(\b|:)"
    ],
    "Removed": [
        r"^revert(\(.*\))?:",
        r"^remove(\b|:)",
        r"^delete(\b|:)",
        r"^deprecat"
    ]
}

def run_git_cmd(cmd):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""

def get_last_tag():
    return run_git_cmd(["git", "describe", "--tags", "--abbrev=0"])

def get_commits_since_tag(last_tag=None):
    if last_tag:
        git_range = f"{last_tag}..HEAD"
    else:
        git_range = "HEAD"
    
    cmd = ["git", "log", git_range, "--pretty=format:%h|%s|%an|%ad", "--date=short"]
    raw = run_git_cmd(cmd)
    if not raw:
        return []
    
    commits = []
    for line in raw.strip().split("\n"):
        parts = line.split("|")
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0],
                "subject": parts[1].strip(),
                "author": parts[2].strip(),
                "date": parts[3].strip()
            })
    return commits

def categorize_commit(subject):
    clean = subject.strip()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, clean, re.IGNORECASE):
                # Clean prefix for changelog display
                clean_msg = re.sub(r"^(feat|fix|bug|refactor|perf|chore|style|add|remove|update)(\(.*\))?:\s*", "", clean, flags=re.IGNORECASE)
                return category, clean_msg.strip().capitalize()
    return "Changed", clean.capitalize()

def generate_changelog(version="Unreleased", output_path="CHANGELOG.md"):
    last_tag = get_last_tag()
    commits = get_commits_since_tag(last_tag)

    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for c in commits:
        cat, msg = categorize_commit(c["subject"])
        entry = f"- {msg} ([`{c['hash']}`])"
        categories[cat].append(entry)

    today = datetime.now().strftime("%Y-%m-%d")
    header = f"## [{version}] - {today}\n"
    if last_tag:
        header += f"*Changes since tag: `{last_tag}`*\n"

    sections = [header]
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        if categories[cat]:
            sections.append(f"\n### {cat}\n")
            sections.extend([f"{item}\n" for item in categories[cat]])

    content = "".join(sections).strip() + "\n"

    # Merge or write to output file
    target = Path(output_path)
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        final_content = f"# Changelog\n\n{content}\n" + existing.replace("# Changelog", "").strip()
    else:
        final_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{content}"

    target.write_text(final_content, encoding="utf-8")
    print(f"[+] Changelog generated successfully at {target.resolve()}")
    return final_content

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "Unreleased"
    generate_changelog(version)
