```python
#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History
Complies with "Keep a Changelog" format and Conventional Commits.
"""

import subprocess
import re
import sys
from datetime import datetime
from collections import defaultdict

def run_git_cmd(args):
    try:
        res = subprocess.run(['git'] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def get_last_tag():
    tag = run_git_cmd(['describe', '--tags', '--abbrev=0'])
    return tag if tag else None

def get_commits_since_tag(last_tag):
    if last_tag:
        rev_range = f"{last_tag}..HEAD"
    else:
        rev_range = "HEAD"
    
    output = run_git_cmd(['log', rev_range, '--pretty=format:%h|%an|%s'])
    if not output:
        return []
    
    commits = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|', 2)
            commits.append({
                'hash': parts[0],
                'author': parts[1],
                'message': parts[2]
            })
    return commits

def categorize_commit(msg):
    """
    Auto-categorize into: Added / Fixed / Changed / Removed
    Based on Conventional Commits & keywords
    """
    m = msg.strip().lower()
    
    # 1. Added
    if re.search(r'^(feat|feature|add|new)(\(.*\))?:', m) or 'add ' in m or 'implement' in m:
        return 'Added'
    
    # 2. Fixed
    if re.search(r'^(fix|bugfix|patch|hotfix)(\(.*\))?:', m) or 'fix ' in m or 'resolve' in m or 'correct' in m:
        return 'Fixed'
    
    # 3. Removed / Deprecated
    if re.search(r'^(remove|delete|deprecated|drop)(\(.*\))?:', m) or 'remove ' in m or 'deprecated' in m:
        return 'Removed'
    
    # 4. Changed (refactor, chore, docs, perf, style, test)
    if re.search(r'^(refactor|chore|perf|style|test|docs|update|change)(\(.*\))?:', m) or 'update' in m or 'refactor' in m:
        return 'Changed'
    
    return 'Changed'

def generate_markdown(commits, last_tag):
    categories = defaultdict(list)
    for c in commits:
        cat = categorize_commit(c['message'])
        clean_msg = re.sub(r'^(feat|fix|refactor|docs|chore|style|perf|test)(\(.*\))?:\s*', '', c['message'], flags=re.IGNORECASE)
        clean_msg = clean_msg[0].upper() + clean_msg[1:] if clean_msg else c['message']
        categories[cat].append(f"- {clean_msg} ([`{c['hash']}`](https://github.com/commit/{c['hash']})) - @{c['author']}")

    now_date = datetime.now().strftime('%Y-%m-%d')
    version_title = f"[Unreleased] - {now_date}" if not last_tag else f"[{last_tag}..HEAD] - {now_date}"
    
    lines = [
        f"## {version_title}\n"
    ]
    
    order = ['Added', 'Fixed', 'Changed', 'Removed']
    for cat in order:
        items = categories.get(cat, [])
        if items:
            lines.append(f"### {cat}")
            lines.extend(items)
            lines.append("")
            
    return '\n'.join(lines)

if __name__ == '__main__':
    tag = get_last_tag()
    commits = get_commits_since_tag(tag)
    if not commits:
        print("No new git commits detected.")
        sys.exit(0)
    
    md_output = generate_markdown(commits, tag)
    print(md_output)
    
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n" + md_output)
    print("\n[+] Successfully generated CHANGELOG.md!")