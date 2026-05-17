#!/usr/bin/env python3
"""
Claude Code Skill: Generate structured CHANGELOG.md from git history
Usage: /generate-changelog
Or: python generate_changelog.py
"""

import subprocess
import re
import sys
from datetime import datetime

def get_latest_tag():
    """Get the latest git tag"""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # No tags yet, use initial commit
        result = subprocess.run(
            ['git', 'rev-list', '--max-parents=0', 'HEAD'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

def get_commits_since_tag(tag):
    """Get all commits since the latest tag"""
    try:
        result = subprocess.run(
            ['git', 'log', f'{tag}..HEAD', '--pretty=format:%H|%s|%an|%ai'],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        # If tag is a commit hash (initial commit case)
        result = subprocess.run(
            ['git', 'log', '--pretty=format:%H|%s|%an|%ai'],
            capture_output=True, text=True, check=True
        )
    
    commits = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('|')
        if len(parts) >= 4:
            commits.append({
                'hash': parts[0],
                'subject': parts[1],
                'author': parts[2],
                'date': parts[3]
            })
    return commits

def categorize_commit(subject):
    """Auto-categorize commit based on conventional commit patterns"""
    subject_lower = subject.lower()
    
    # Check for conventional commit prefixes
    if re.match(r'^(feat|feature|add)(\(.*\))?(\!)?:', subject_lower):
        return 'Added'
    if re.match(r'^(fix|bugfix|hotfix)(\(.*\))?(\!)?:', subject_lower):
        return 'Fixed'
    if re.match(r'^(change|update|refactor|improve|perf)(\(.*\))?(\!)?:', subject_lower):
        return 'Changed'
    if re.match(r'^(remove|delete|deprecate)(\(.*\))?(\!)?:', subject_lower):
        return 'Removed'
    
    # Keyword-based fallback
    if any(kw in subject_lower for kw in ['add', 'new', 'implement', 'introduce', 'create']):
        return 'Added'
    if any(kw in subject_lower for kw in ['fix', 'bug', 'issue', 'resolve', 'patch']):
        return 'Fixed'
    if any(kw in subject_lower for kw in ['change', 'update', 'modify', 'refactor', 'improve', 'optimize']):
        return 'Changed'
    if any(kw in subject_lower for kw in ['remove', 'delete', 'deprecate', 'drop']):
        return 'Removed'
    
    # Default to Changed
    return 'Changed'

def generate_changelog(commits, version=None):
    """Generate structured CHANGELOG.md content"""
    if not version:
        # Auto-generate version: increment patch of latest tag or start at 0.1.0
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True, text=True, check=True
            )
            latest_tag = result.stdout.strip().lstrip('v')
            parts = latest_tag.split('.')
            if len(parts) == 3:
                parts[2] = str(int(parts[2]) + 1)
                version = '.'.join(parts)
            else:
                version = '0.1.0'
        except subprocess.CalledProcessError:
            version = '0.1.0'
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Categorize commits
    categories = {'Added': [], 'Fixed': [], 'Changed': [], 'Removed': []}
    for commit in commits:
        category = categorize_commit(commit['subject'])
        categories[category].append(commit)
    
    # Build changelog content
    lines = []
    lines.append(f"## [{version}] - {today}")
    lines.append("")
    
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        if categories[cat]:
            lines.append(f"### {cat}")
            for commit in categories[cat]:
                # Clean up commit subject (remove conventional commit prefix)
                clean_subject = re.sub(r'^[a-z]+(\(.*?\))?(\!)?:\s*', '', commit['subject'], flags=re.IGNORECASE)
                lines.append(f"- {clean_subject} ([{commit['hash'][:7]}](https://github.com/CLAUDE_BUILDERS_BOUNTY/claude-builders-bounty/commit/{commit['hash']}))")
            lines.append("")
    
    if not any(categories.values()):
        lines.append("*No significant changes in this release.*")
        lines.append("")
    
    return '\n'.join(lines)

def main():
    print("[CHANGELOG Generator] Starting...")
    
    # Get latest tag
    print("  [1/4] Getting latest git tag...")
    latest_tag = get_latest_tag()
    print(f"    Latest tag/commit: {latest_tag[:12]}...")
    
    # Get commits since tag
    print("  [2/4] Fetching commits since tag...")
    commits = get_commits_since_tag(latest_tag)
    print(f"    Found {len(commits)} commit(s)")
    
    if not commits:
        print("\n[WARN] No commits found since last tag. Nothing to do.")
        sys.exit(0)
    
    # Generate changelog content
    print("  [3/4] Categorizing commits...")
    new_content = generate_changelog(commits)
    
    # Read existing CHANGELOG.md or create new
    print("  [4/4] Writing CHANGELOG.md...")
    try:
        with open('CHANGELOG.md', 'r', encoding='utf-8') as f:
            existing = f.read()
    except FileNotFoundError:
        existing = "# Changelog\n\n"
    
    # Prepend new content
    with open('CHANGELOG.md', 'w', encoding='utf-8') as f:
        f.write(existing.split('\n', 1)[0] + '\n\n')  # Keep title
        f.write(new_content + '\n')
        if len(existing.split('\n', 1)) > 1:
            f.write(existing.split('\n', 1)[1])
    
    print("\n[SUCCESS] CHANGELOG.md updated successfully!")
    print(f"\nPreview:\n{new_content[:500]}...")

if __name__ == '__main__':
    main()
