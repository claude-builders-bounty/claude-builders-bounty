#!/usr/bin/env python3
import subprocess
import sys
import re
import os
from datetime import datetime

def run_git_command(args):
    try:
        result = subprocess.run(['git'] + args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_tags():
    tags_str = run_git_command(['tag', '--sort=-creatordate'])
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split('\n') if t.strip()]

def get_commits(revision_range=None):
    args = ['log', '--pretty=format:%h|%s|%ad', '--date=short']
    if revision_range:
        args.append(revision_range)
    
    log_output = run_git_command(args)
    if not log_output:
        return []
        
    commits = []
    for line in log_output.split('\n'):
        parts = line.split('|', 2)
        if len(parts) == 3:
            commits.append({
                'hash': parts[0],
                'subject': parts[1],
                'date': parts[2]
            })
    return commits

def categorize_commit(subject):
    subject_lower = subject.lower()
    if re.search(r'\b(add|added|feat|feature|new)\b', subject_lower) or subject_lower.startswith('feat:') or subject_lower.startswith('feat('):
        return 'Added'
    if re.search(r'\b(fix|fixed|resolve|resolved|bug|bugfix|patch)\b', subject_lower) or subject_lower.startswith('fix:') or subject_lower.startswith('fix('):
        return 'Fixed'
    if re.search(r'\b(remove|removed|delete|deleted|deprecate|deprecated)\b', subject_lower):
        return 'Removed'
    return 'Changed'

def generate_section(commits):
    categories = {
        'Added': [],
        'Fixed': [],
        'Changed': [],
        'Removed': []
    }
    
    for c in commits:
        cat = categorize_commit(c['subject'])
        categories[cat].append(f"- {c['subject']} ({c['hash']})")
        
    section_md = ""
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        if categories[cat]:
            section_md += f"### {cat}\n"
            for item in categories[cat]:
                section_md += f"{item}\n"
            section_md += "\n"
    return section_md

def main():
    if not os.path.exists('.git'):
        print("Error: Not a git repository.", file=sys.stderr)
        sys.exit(1)
        
    tags = get_tags()
    changelog_content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
    
    if not tags:
        commits = get_commits()
        if commits:
            changelog_content += "## [Unreleased] - " + datetime.now().strftime("%Y-%m-%d") + "\n\n"
            changelog_content += generate_section(commits)
    else:
        unreleased_commits = get_commits(f"{tags[0]}..HEAD")
        if unreleased_commits:
            changelog_content += "## [Unreleased]\n\n"
            changelog_content += generate_section(unreleased_commits)
            
        for i in range(len(tags)):
            tag = tags[i]
            tag_date = run_git_command(['log', '-1', '--format=%ad', '--date=short', tag])
            if not tag_date:
                tag_date = datetime.now().strftime("%Y-%m-%d")
                
            changelog_content += f"## [{tag}] - {tag_date}\n\n"
            
            if i + 1 < len(tags):
                prev_tag = tags[i+1]
                commits = get_commits(f"{prev_tag}..{tag}")
            else:
                commits = get_commits(tag)
                
            changelog_content += generate_section(commits)
            
    with open("CHANGELOG.md", "w") as f:
        f.write(changelog_content)
        
    print("CHANGELOG.md generated successfully!")

if __name__ == '__main__':
    main()
