import subprocess
import sys
import os
from collections import defaultdict
from datetime import datetime

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_last_tag():
    # Try to get the latest tag
    return run_command("git describe --tags --abbrev=0")

def get_commits_since(tag):
    if tag:
        cmd = f'git log {tag}..HEAD --pretty=format:"%s (%h)"'
    else:
        cmd = 'git log --pretty=format:"%s (%h)"'
    
    output = run_command(cmd)
    if output is None:
        return []
    return output.splitlines()

def categorize_commits(commits):
    categories = defaultdict(list)
    
    for commit in commits:
        commit_lower = commit.lower()
        
        # Categorization logic
        if commit_lower.startswith(('feat:', 'feat ', 'add ', 'added ', 'new ')):
            categories['Added'].append(commit)
        elif commit_lower.startswith(('fix:', 'fix ', 'fixed ', 'bug ', 'bugfix ')):
            categories['Fixed'].append(commit)
        elif commit_lower.startswith(('remove:', 'remove ', 'removed ', 'delete ', 'deleted ', 'drop ')):
            categories['Removed'].append(commit)
        else:
            categories['Changed'].append(commit)
            
    return categories

def generate_changelog(categories, tag):
    today = datetime.now().strftime("%Y-%m-%d")
    version = "Unreleased" if not tag else f"Changes since {tag}"
    
    lines = []
    lines.append(f"# CHANGELOG")
    lines.append(f"## {version} ({today})")
    lines.append("")
    
    order = ['Added', 'Fixed', 'Changed', 'Removed']
    
    for category in order:
        if categories[category]:
            lines.append(f"### {category}")
            for commit in categories[category]:
                lines.append(f"- {commit}")
            lines.append("")
            
    return "\n".join(lines)

def main():
    if run_command("git rev-parse --is-inside-work-tree") != "true":
        print("Error: Must be run inside a git repository.", file=sys.stderr)
        sys.exit(1)
        
    last_tag = get_last_tag()
    commits = get_commits_since(last_tag)
    
    if not commits:
        print("No commits found to generate changelog.", file=sys.stderr)
        sys.exit(0)
        
    categories = categorize_commits(commits)
    changelog_content = generate_changelog(categories, last_tag)
    
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(changelog_content)
        
    print(f"Successfully generated CHANGELOG.md with {len(commits)} commits.")
    
if __name__ == "__main__":
    main()
