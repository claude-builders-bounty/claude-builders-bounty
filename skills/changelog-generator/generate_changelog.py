#!/usr/bin/env python3
"""
Automated Git History Changelog Generator
Conforms to "Keep a Changelog" (https://keepachangelog.com)
Categorizes commits into Added, Fixed, Changed, and Removed.
"""

import subprocess
import sys
import re
import os
from datetime import datetime

def run_git(cmd: list) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()

def get_latest_tag() -> str:
    try:
        tag = run_git(["git", "describe", "--tags", "--abbrev=0"])
        return tag
    except Exception:
        return ""

def get_commits_since(tag: str = "") -> list:
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    cmd = ["git", "log", rev_range, "--pretty=format:%h%x09%s%x09%an%x09%ad", "--date=short"]
    try:
        output = run_git(cmd)
        if not output:
            return []
        lines = output.split("\n")
        commits = []
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 2:
                commits.append({
                    "hash": parts[0],
                    "subject": parts[1],
                    "author": parts[2] if len(parts) > 2 else "",
                    "date": parts[3] if len(parts) > 3 else ""
                })
        return commits
    except Exception as e:
        print(f"Error reading git log: {e}", file=sys.stderr)
        return []

def categorize_commit(subject: str) -> str:
    s = subject.lower().strip()
    # Check conventional commits prefixes and common keywords
    if re.match(r"^(feat|add|feature|new)(\(.*\))?(\!)?:", s) or "add " in s or "introduce " in s:
        return "Added"
    elif re.match(r"^(fix|bugfix|patch|hotfix)(\(.*\))?(\!)?:", s) or "fix " in s or "resolve " in s:
        return "Fixed"
    elif re.match(r"^(remove|deprecate|delete)(\(.*\))?(\!)?:", s) or "remove " in s or "delete " in s:
        return "Removed"
    elif re.match(r"^(refactor|change|update|perf|docs|style|build|chore|ci)(\(.*\))?(\!)?:", s) or "update " in s:
        return "Changed"
    else:
        return "Changed"

def clean_subject(subject: str) -> str:
    cleaned = re.sub(r"^(feat|fix|bugfix|patch|refactor|docs|perf|test|build|ci|chore|add|remove)(\(.*\))?(\!)?:\s*", "", subject, flags=re.IGNORECASE)
    return cleaned.strip()

def generate_changelog(version: str = "Unreleased", output_file: str = "CHANGELOG.md") -> str:
    latest_tag = get_latest_tag()
    commits = get_commits_since(latest_tag)
    
    today = datetime.now().strftime("%Y-%m-%d")
    tag_info = f"since tag `{latest_tag}`" if latest_tag else "initial history"
    
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for c in commits:
        cat = categorize_commit(c["subject"])
        msg = clean_subject(c["subject"])
        categories[cat].append(f"- {msg} ([`{c['hash']}`] - {c['author']})")
        
    changelog_entry = []
    changelog_entry.append(f"## [{version}] - {today}\n")
    changelog_entry.append(f"> Changes {tag_info} ({len(commits)} commits)\n\n")
    
    has_entries = False
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        if categories[cat]:
            has_entries = True
            changelog_entry.append(f"### {cat}\n")
            for item in categories[cat]:
                changelog_entry.append(f"{item}\n")
            changelog_entry.append("\n")
            
    if not has_entries:
        changelog_entry.append("No user-facing changes recorded.\n\n")
        
    entry_text = "".join(changelog_entry)
    
    # Read existing CHANGELOG if present, or create header
    header = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
        "---\n\n"
    )
    
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing = f.read()
        if "# Changelog" in existing:
            # Insert after the header line
            parts = existing.split("---\n\n", 1)
            if len(parts) == 2:
                final_content = parts[0] + "---\n\n" + entry_text + parts[1]
            else:
                final_content = header + entry_text + existing.replace("# Changelog\n\n", "")
        else:
            final_content = header + entry_text + existing
    else:
        final_content = header + entry_text
        
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    return entry_text

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "Unreleased"
    outfile = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    entry = generate_changelog(version, outfile)
    print(f"[+] Successfully updated {outfile} with {version} release notes:")
    print(entry)
