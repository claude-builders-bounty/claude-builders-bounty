#!/usr/bin/env python3
"""
Automated Git Changelog Generator
Generates structured CHANGELOG.md following 'Keep a Changelog' standards.
"""

import subprocess
import re
import sys
from datetime import datetime

CATEGORIES = {
    'Added': [r'^feat(\(.*\))?:', r'^add(\(.*\))?:', r'added', r'new:'],
    'Fixed': [r'^fix(\(.*\))?:', r'^bug(\(.*\))?:', r'fixed', r'patch:'],
    'Changed': [r'^refactor(\(.*\))?:', r'^perf(\(.*\))?:', r'^style(\(.*\))?:', r'update', r'changed'],
    'Removed': [r'^remove(\(.*\))?:', r'^deprecate(\(.*\))?:', r'deleted', r'removed']
}

def run_git(cmd):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""

def get_latest_tag():
    return run_git(['git', 'describe', '--tags', '--abbrev=0'])

def get_commits(since_tag=None):
    if since_tag:
        git_range = f"{since_tag}..HEAD"
    else:
        git_range = "HEAD"
    
    # Format: hash|subject|author|date
    raw = run_git(['git', 'log', git_range, '--pretty=format:%h|%s|%an|%as'])
    if not raw:
        return []
    
    commits = []
    for line in raw.split('\n'):
        parts = line.split('|')
        if len(parts) >= 2:
            commits.append({
                'hash': parts[0],
                'subject': parts[1],
                'author': parts[2] if len(parts) > 2 else '',
                'date': parts[3] if len(parts) > 3 else ''
            })
    return commits

def categorize_commit(subject):
    s = subject.strip()
    for cat, patterns in CATEGORIES.items():
        for p in patterns:
            if re.search(p, s, re.IGNORECASE):
                # Clean prefix for changelog bullet
                cleaned = re.sub(p, '', s, flags=re.IGNORECASE).strip()
                return cat, cleaned
    return 'Changed', s

def generate_changelog(version="Unreleased"):
    latest_tag = get_latest_tag()
    commits = get_commits(since_tag=latest_tag)
    
    if not commits:
        print("[!] No new commits found since last tag/init.")
        return ""
    
    sections = {'Added': [], 'Fixed': [], 'Changed': [], 'Removed': []}
    
    for c in commits:
        cat, cleaned = categorize_commit(c['subject'])
        bullet = f"- {cleaned} ([{c['hash']}]) - {c['author']}"
        sections[cat].append(bullet)
        
    date_str = datetime.now().strftime('%Y-%m-%d')
    output = []
    output.append(f"## [{version}] - {date_str}")
    if latest_tag:
        output.append(f"*(Changes since tag: `{latest_tag}`)*\n")
        
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        if sections[cat]:
            output.append(f"### {cat}")
            for item in sections[cat]:
                output.append(item)
            output.append("")
            
    return "\n".join(output)

if __name__ == '__main__':
    ver = sys.argv[1] if len(sys.argv) > 1 else "Unreleased"
    md = generate_changelog(ver)
    
    if md:
        target_file = "CHANGELOG.md"
        with open(target_file, "a", encoding="utf-8") as f:
            f.write("\n" + md + "\n")
        print(f"[OK] Generated CHANGELOG.md successfully!\n")
        print(md)
