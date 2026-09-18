#!/usr/bin/env python3
import subprocess
import re
import sys

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return ""

def get_commits_since_last_tag():
    last_tag = run_cmd("git describe --tags --abbrev=0")
    if last_tag:
        commits_raw = run_cmd(f'git log {last_tag}..HEAD --oneline')
    else:
        commits_raw = run_cmd('git log --oneline')
    
    return [line.strip() for line in commits_raw.split('\n') if line.strip()]

def categorize_commits(commits):
    categories = {
        'Added': [],
        'Fixed': [],
        'Changed': [],
        'Removed': []
    }
    
    added_patterns = ['add', 'feat', 'new', 'create']
    fixed_patterns = ['fix', 'bug', 'resolve', 'patch']
    removed_patterns = ['remove', 'delete', 'drop', 'rm']
    
    for commit in commits:
        parts = commit.split(' ', 1)
        if len(parts) < 2:
            continue
        hash_val, message = parts
        msg_lower = message.lower()
        
        assigned = False
        if any(p in msg_lower for p in added_patterns):
            categories['Added'].append((hash_val, message))
            assigned = True
        elif any(p in msg_lower for p in fixed_patterns):
            categories['Fixed'].append((hash_val, message))
            assigned = True
        elif any(p in msg_lower for p in removed_patterns):
            categories['Removed'].append((hash_val, message))
            assigned = True
        else:
            categories['Changed'].append((hash_val, message))
            
    return categories

def generate_changelog(categories):
    output = ["# CHANGELOG\n"]
    
    for cat, items in categories.items():
        if items:
            output.append(f"## {cat}")
            for h, m in items:
                output.append(f"- {m} ({h})")
            output.append("")
            
    return "\n".join(output)

def main():
    commits = get_commits_since_last_tag()
    if not commits:
        print("No commits found.")
        sys.exit(0)
        
    categories = categorize_commits(commits)
    changelog = generate_changelog(categories)
    
    with open('CHANGELOG.md', 'w') as f:
        f.write(changelog)
        
    print("Successfully generated CHANGELOG.md!")
    print("\nPreview:")
    print(changelog)

if __name__ == "__main__":
    main()
