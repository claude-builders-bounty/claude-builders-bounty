#!/usr/bin/env python3
import subprocess
import sys
import re
from datetime import datetime

def get_git_logs(since_tag=None):
    cmd = ["git", "log", "--pretty=format:%s"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Error fetching git logs: {e.stderr}")
        sys.exit(1)

def categorize_commits(commits):
    categories = {
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Refactors": [],
        "Other": []
    }
    
    for commit in commits:
        commit = commit.strip()
        if not commit:
            continue
            
        if re.match(r"^(feat|feature)", commit, re.I):
            categories["Features"].append(commit)
        elif re.match(r"^(fix|bugfix)", commit, re.I):
            categories["Bug Fixes"].append(commit)
        elif re.match(r"^(docs|doc)", commit, re.I):
            categories["Documentation"].append(commit)
        elif re.match(r"^(refactor|style)", commit, re.I):
            categories["Refactors"].append(commit)
        else:
            categories["Other"].append(commit)
            
    return categories

def generate_markdown(categories):
    date_str = datetime.now().strftime("%Y-%m-%d")
    md = f"## [Unreleased] - {date_str}\n\n"
    
    for cat, items in categories.items():
        if items:
            md += f"### {cat}\n"
            for item in items:
                # Clean up prefixes if they exist
                clean_item = re.sub(r"^(feat|fix|docs|refactor|style|other):\s*", "", item, flags=re.I)
                md += f"- {clean_item}\n"
            md += "\n"
            
    return md

def main():
    since = None
    if len(sys.argv) > 1:
        since = sys.argv[1]
        
    commits = get_git_logs(since)
    categories = categorize_commits(commits)
    markdown = generate_markdown(categories)
    
    print(markdown)

if __name__ == "__main__":
    main()
