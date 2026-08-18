#!/usr/bin/env python3
import subprocess
import re
import os
import sys
from datetime import datetime

CATEGORIES = {
    'Added': ['feat', 'add', 'feature', 'new'],
    'Fixed': ['fix', 'bug', 'patch', 'hotfix', 'resolve'],
    'Changed': ['refactor', 'perf', 'change', 'update', 'style', 'improve'],
    'Removed': ['remove', 'deprecate', 'drop', 'delete'],
    'Maintenance': ['chore', 'ci', 'build', 'docs', 'test']
}

def get_latest_tag():
    try:
        tag = subprocess.check_output(
            ['git', 'describe', '--tags', '--abbrev=0'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        return tag
    except Exception:
        return None

def get_commits_since_tag(tag=None):
    cmd = ['git', 'log', '--pretty=format:%H|%s|%an|%ad', '--date=short']
    if tag:
        cmd.append(f'{tag}..HEAD')
    try:
        output = subprocess.check_output(cmd).decode('utf-8').strip()
        if not output:
            return []
        commits = []
        for line in output.splitlines():
            parts = line.split('|', 3)
            if len(parts) == 4:
                commits.append({
                    'hash': parts[0][:7],
                    'subject': parts[1],
                    'author': parts[2],
                    'date': parts[3]
                })
        return commits
    except Exception as e:
        print(f'Error reading git log: {e}', file=sys.stderr)
        return []

def categorize_commit(subject):
    clean = subject.strip()
    match = re.match(r'^([a-zA-Z0-9_-]+)(?:\([^\)]+\))?:\s*(.+)$', clean)
    if match:
        prefix = match.group(1).lower()
        desc = match.group(2)
        for cat, prefixes in CATEGORIES.items():
            if prefix in prefixes:
                return cat, desc
    
    words = clean.lower().split()
    if words:
        first = words[0]
        for cat, prefixes in CATEGORIES.items():
            if any(first.startswith(p) for p in prefixes):
                return cat, clean
                
    return 'Changed', clean

def generate_markdown(version_name='Unreleased', commits=None):
    if not commits:
        return ''
    
    categorized = {cat: [] for cat in CATEGORIES.keys()}
    for c in commits:
        cat, clean_desc = categorize_commit(c['subject'])
        h = c['hash']
        author = c['author']
        categorized[cat].append(f"- {clean_desc} (`{h}`) - {author}")
    
    today = datetime.now().strftime('%Y-%m-%d')
    lines = [f"## [{version_name}] - {today}\n"]
    
    has_entries = False
    for cat, items in categorized.items():
        if items:
            has_entries = True
            lines.append(f"### {cat}")
            lines.extend(items)
            lines.append("")
            
    if not has_entries:
        lines.append("- Maintenance and minor improvements.\n")
        
    return "\n".join(lines)

def main():
    tag = get_latest_tag()
    commits = get_commits_since_tag(tag)
    if not commits:
        print("No commits found.")
        return
        
    print(f"Found {len(commits)} commits since tag: {tag or 'initial commit'}")
    md = generate_markdown("Unreleased", commits)
    
    out_file = "CHANGELOG.md"
    existing = ""
    if os.path.exists(out_file):
        with open(out_file, "r") as f:
            existing = f.read()
            
    with open(out_file, "w") as f:
        f.write(f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{md}\n{existing}")
        
    print(f"Successfully generated and updated {out_file}")

if __name__ == '__main__':
    main()
