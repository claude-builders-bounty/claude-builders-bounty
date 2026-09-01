#!/usr/bin/env python3
"""
Automated Git Changelog Generator
Generates structured Keep-a-Changelog formatted CHANGELOG.md from git commits.
"""

import subprocess
import sys
import re
from datetime import datetime
from collections import defaultdict
from pathlib import Path

CATEGORY_MAPPING = {
    'feat': 'Added',
    'feature': 'Added',
    'add': 'Added',
    'fix': 'Fixed',
    'bugfix': 'Fixed',
    'patch': 'Fixed',
    'change': 'Changed',
    'refactor': 'Changed',
    'perf': 'Changed',
    'update': 'Changed',
    'remove': 'Removed',
    'deprecate': 'Removed',
    'docs': 'Documentation',
    'style': 'Changed',
    'chore': 'Maintenance',
    'ci': 'Maintenance'
}

def run_git(args):
    try:
        res = subprocess.run(['git'] + args, capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def get_latest_tag():
    tag = run_git(['describe', '--tags', '--abbrev=0'])
    return tag if tag else None

def get_commits_since_tag(tag=None):
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"
    
    # Format: %H (hash) | %an (author) | %ad (date) | %s (subject)
    log_output = run_git(['log', range_spec, '--pretty=format:%h|%an|%ad|%s', '--date=short'])
    if not log_output:
        return []
    
    commits = []
    for line in log_output.splitlines():
        parts = line.split('|', 3)
        if len(parts) == 4:
            commits.append({
                'hash': parts[0],
                'author': parts[1],
                'date': parts[2],
                'subject': parts[3]
            })
    return commits

def categorize_commit(subject):
    # Conventional commit regex: type(scope)?: description
    match = re.match(r'^([a-zA-Z]+)(?:\([^\)]+\))?(!)?:\s*(.*)$', subject)
    if match:
        ctype = match.group(1).lower()
        desc = match.group(3).strip()
        cat = CATEGORY_MAPPING.get(ctype, 'Changed')
        return cat, desc
    
    # Keyword fallback
    lower = subject.lower()
    if lower.startswith(('add', 'feat', 'create', 'implement')):
        return 'Added', subject
    elif lower.startswith(('fix', 'resolve', 'patch', 'bug')):
        return 'Fixed', subject
    elif lower.startswith(('remove', 'delete', 'deprecate')):
        return 'Removed', subject
    elif lower.startswith(('doc', 'readme')):
        return 'Documentation', subject
    
    return 'Changed', subject

def generate_markdown(commits, version="Unreleased", previous_tag=None):
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"## [{version}] - {today}\n\n"
    
    categories = defaultdict(list)
    for c in commits:
        cat, clean_desc = categorize_commit(c['subject'])
        categories[cat].append(f"- {clean_desc} ([`{c['hash']}`])")
    
    body = []
    order = ['Added', 'Changed', 'Fixed', 'Removed', 'Documentation', 'Maintenance']
    for cat in order:
        if categories[cat]:
            body.append(f"### {cat}\n" + "\n".join(categories[cat]) + "\n")
            
    for cat, items in categories.items():
        if cat not in order and items:
            body.append(f"### {cat}\n" + "\n".join(items) + "\n")
            
    return header + "\n".join(body)

def main():
    tag = get_latest_tag()
    commits = get_commits_since_tag(tag)
    
    if not commits:
        print("[!] No new commits found since last tag/init.")
        sys.exit(0)
        
    print(f"[*] Found {len(commits)} commits (since tag: {tag or 'Initial commit'})")
    new_section = generate_markdown(commits, version="Unreleased", previous_tag=tag)
    
    changelog_path = Path("CHANGELOG.md")
    existing_content = ""
    if changelog_path.exists():
        existing_content = changelog_path.read_text(encoding="utf-8")
        
    if "# Changelog" not in existing_content:
        full_changelog = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n" + new_section
        if existing_content:
            full_changelog += "\n" + existing_content
    else:
        # Insert after header
        parts = existing_content.split("# Changelog\n\n", 1)
        full_changelog = "# Changelog\n\n" + new_section + "\n" + (parts[1] if len(parts) > 1 else "")
        
    changelog_path.write_text(full_changelog, encoding="utf-8")
    print("[+] Successfully updated CHANGELOG.md")

if __name__ == "__main__":
    main()
