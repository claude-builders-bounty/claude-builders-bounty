#!/usr/bin/env python3
"""
Structured Git Changelog Generator
Extracts git commits since the last tag and outputs Keep-a-Changelog Markdown.
Bounty #1: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
"""

import subprocess
import re
import sys
import os
from datetime import datetime, timezone

def run_git(args):
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def get_latest_tag():
    # Attempt to find the most recent reachable tag
    tag = run_git(["describe", "--tags", "--abbrev=0"])
    return tag if tag else None

def get_commits_since_tag(tag=None):
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"

    log_raw = run_git([
        "log",
        range_spec,
        "--pretty=format:%h|%s|%an|%ad",
        "--date=short",
        "--no-merges"
    ])

    commits = []
    for line in log_raw.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) >= 2:
            commits.append({
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2] if len(parts) > 2 else "",
                "date": parts[3] if len(parts) > 3 else ""
            })
    return commits

def categorize_commit(subject: str):
    sub = subject.strip()
    
    # Conventional commit prefixes
    # feat -> Added
    if re.match(r"^feat(\(.*\))?:", sub, re.IGNORECASE):
        clean_msg = re.sub(r"^feat(\(.*\))?:\s*", "", sub, flags=re.IGNORECASE)
        return "Added", clean_msg
        
    # fix / bugfix -> Fixed
    if re.match(r"^(fix|bugfix)(\(.*\))?:", sub, re.IGNORECASE):
        clean_msg = re.sub(r"^(fix|bugfix)(\(.*\))?:\s*", "", sub, flags=re.IGNORECASE)
        return "Fixed", clean_msg
        
    # remove / revert / deprecate -> Removed
    if re.match(r"^(revert|remove|deprecated)(\(.*\))?:", sub, re.IGNORECASE):
        clean_msg = re.sub(r"^(revert|remove|deprecated)(\(.*\))?:\s*", "", sub, flags=re.IGNORECASE)
        return "Removed", clean_msg
        
    # refactor / perf / style / chore / docs / test -> Changed
    if re.match(r"^(refactor|perf|style|chore|docs|test|build|ci)(\(.*\))?:", sub, re.IGNORECASE):
        clean_msg = re.sub(r"^(refactor|perf|style|chore|docs|test|build|ci)(\(.*\))?:\s*", "", sub, flags=re.IGNORECASE)
        return "Changed", clean_msg

    # Fallback heuristic
    lower = sub.lower()
    if lower.startswith("add ") or "initial" in lower:
        return "Added", sub
    if lower.startswith("fix ") or "bug" in lower:
        return "Fixed", sub
    if lower.startswith("remove ") or lower.startswith("delete "):
        return "Removed", sub

    return "Changed", sub

def generate_changelog(version="Unreleased", output_file="CHANGELOG.md"):
    tag = get_latest_tag()
    commits = get_commits_since_tag(tag)
    
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

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    header = f"## [{version}] - {today}"
    if tag:
        header += f" (since tag `{tag}`)"

    sections = [header, ""]
    
    has_entries = False
    for cat_name in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories[cat_name]
        if items:
            has_entries = True
            sections.append(f"### {cat_name}")
            sections.extend(items)
            sections.append("")

    if not has_entries:
        sections.append("_No commits found in range._\n")

    content = "\n".join(sections)

    # Read existing CHANGELOG if exists to prepend, or create fresh
    existing_content = ""
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing_content = f.read()

    with open(output_file, "w", encoding="utf-8") as f:
        if not existing_content.startswith("# Changelog"):
            f.write("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n")
        f.write(content)
        if existing_content:
            # Strip previous header if prepending
            clean_existing = re.sub(r"^# Changelog\s*\n\n(All notable changes[^\n]+\n\n)?", "", existing_content)
            f.write("\n" + clean_existing)

    print(f"Generated changelog successfully to {output_file}")
    print(content)

if __name__ == "__main__":
    ver = sys.argv[1] if len(sys.argv) > 1 else "Unreleased"
    dest = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    generate_changelog(version=ver, output_file=dest)
