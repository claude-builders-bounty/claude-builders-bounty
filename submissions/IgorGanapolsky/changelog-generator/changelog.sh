#!/usr/bin/env bash
# Generate a structured CHANGELOG from git history
# Set exit on error
set -e

python3 - << 'EOF'
import subprocess
import sys
import re

def run_git(args):
    try:
        res = subprocess.run(['git'] + args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        if 'describe' in args:
            return None
        print(f"Error running git {' '.join(args)}: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def main():
    last_tag = run_git(['describe', '--tags', '--abbrev=0'])
    if last_tag:
        print(f"Generating changelog since tag: {last_tag}")
        revision_range = f"{last_tag}..HEAD"
    else:
        print("No git tags found. Generating changelog from first commit.")
        revision_range = "HEAD"
        
    commits_raw = run_git(['log', revision_range, '--pretty=format:%s|%h|%an'])
    if not commits_raw:
        print("No commits found in the range.")
        return

    categories = {
        'Added': [],
        'Fixed': [],
        'Changed': [],
        'Removed': []
    }
    
    re_added = re.compile(r'\b(add|added|feat|feature|new|introduce|create)\b', re.IGNORECASE)
    re_fixed = re.compile(r'\b(fix|fixed|bug|correct|resolve|close|hotfix)\b', re.IGNORECASE)
    re_removed = re.compile(r'\b(remove|removed|delete|deleted|rm|cleanup|deprecate)\b', re.IGNORECASE)

    for line in commits_raw.splitlines():
        if not line or '|' not in line:
            continue
        parts = line.split('|', 2)
        subject = parts[0].strip()
        sha = parts[1].strip()
        author = parts[2].strip() if len(parts) > 2 else "Unknown"
        
        if re_added.search(subject):
            cat = 'Added'
        elif re_fixed.search(subject):
            cat = 'Fixed'
        elif re_removed.search(subject):
            cat = 'Removed'
        else:
            cat = 'Changed'
            
        categories[cat].append((subject, sha, author))
        
    changelog = ["# CHANGELOG\n"]
    if last_tag:
        changelog.append(f"## [Unreleased] (Since {last_tag})\n")
    else:
        changelog.append("## [Unreleased]\n")
        
    for cat in ['Added', 'Changed', 'Fixed', 'Removed']:
        items = categories[cat]
        if items:
            changelog.append(f"### {cat}\n")
            for subject, sha, author in items:
                clean_subject = re.sub(r'^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)(\(.+?\))?:\s*', '', subject, flags=re.IGNORECASE)
                clean_subject = clean_subject[0].upper() + clean_subject[1:] if clean_subject else ""
                changelog.append(f"- {clean_subject} ({sha}) by @{author}")
            changelog.append("")
            
    output_content = "\n".join(changelog)
    with open("CHANGELOG.md", "w") as f:
        f.write(output_content)
    print("CHANGELOG.md generated successfully.")

if __name__ == '__main__':
    main()
EOF
