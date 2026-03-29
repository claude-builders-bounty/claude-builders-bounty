#!/usr/bin/env python3
"""
Generate Changelog - Cross-platform CHANGELOG generator
Usage: python changelog.py [--since TAG] [--output FILE] [--repo PATH]
"""

import subprocess
import argparse
from datetime import datetime
from collections import defaultdict

def run_git(cmd, repo_path):
    try:
        result = subprocess.run(cmd, shell=True, cwd=repo_path, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False

def get_last_tag(repo_path):
    output, _ = run_git("git describe --tags --abbrev=0", repo_path)
    return output if output else None

def get_commits_since_tag(tag, repo_path):
    if tag:
        cmd = f'git log {tag}..HEAD --format="%H|%s|%an|%ad" --date=short'
    else:
        cmd = 'git log --format="%H|%s|%an|%ad" --date=short'
    output, success = run_git(cmd, repo_path)
    if not success or not output:
        return []
    return output.split('\n')

def categorize_commit(subject):
    subject_lower = subject.lower()
    if subject_lower.startswith(('feat', 'add')):
        return 'Added'
    elif subject_lower.startswith('fix'):
        return 'Fixed'
    elif subject_lower.startswith(('refactor', 'perf', 'optimize')):
        return 'Changed'
    elif subject_lower.startswith(('chore', 'ci', 'build', 'deps')):
        return 'Maintenance'
    elif any(word in subject_lower for word in ['remove', 'delete', 'drop']):
        return 'Removed'
    else:
        return 'Changed'

def generate_changelog(repo_path, since_tag=None, output_file='CHANGELOG.md'):
    commits = get_commits_since_tag(since_tag, repo_path)
    categories = defaultdict(list)
    
    for line in commits:
        if not line or '|' not in line:
            continue
        parts = line.split('|')
        if len(parts) < 2:
            continue
        subject = parts[1].strip()
        if subject.startswith('Merge '):
            continue
        category = categorize_commit(subject)
        categories[category].append(f"- {subject}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Changelog\n\n")
        f.write(f"## [Unreleased] - {datetime.now().strftime('%Y-%m-%d')}\n")
        for category in ['Added', 'Fixed', 'Changed', 'Removed', 'Maintenance']:
            if categories[category]:
                f.write(f"\n### {category}\n")
                for entry in categories[category]:
                    f.write(entry + "\n")
    
    return output_file

if __name__ == '__main__':
    import sys
    parser = argparse.ArgumentParser(description='Generate CHANGELOG from git')
    parser.add_argument('--since', help='Since TAG')
    parser.add_argument('--output', default='CHANGELOG.md', help='Output file')
    parser.add_argument('--repo', default='.', help='Repo path')
    args = parser.parse_args()
    since_tag = args.since or get_last_tag(args.repo)
    output = generate_changelog(args.repo, since_tag, args.output)
    print(f"[OK] Generated: {output}")