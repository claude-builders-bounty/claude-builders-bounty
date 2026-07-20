#!/usr/bin/env python3
import subprocess
import sys
import re
from datetime import datetime

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_last_tag():
    return run_cmd("git describe --tags --abbrev=0")

def get_commits_since(tag):
    cmd = "git log --pretty=format:'%s'"
    if tag:
        cmd = f"git log {tag}..HEAD --pretty=format:'%s'"
    output = run_cmd(cmd)
    if output:
        return output.split("\n")
    return []

def parse_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for commit in commits:
        commit = commit.strip().strip("'").strip('"')
        if not commit:
            continue
            
        # Match conventional commits: type(scope): message
        # or simple keywords
        lower_msg = commit.lower()
        if lower_msg.startswith("feat") or lower_msg.startswith("add"):
            categories["Added"].append(commit)
        elif lower_msg.startswith("fix") or lower_msg.startswith("bug"):
            categories["Fixed"].append(commit)
        elif lower_msg.startswith("refactor") or lower_msg.startswith("chore") or lower_msg.startswith("update") or lower_msg.startswith("change"):
            categories["Changed"].append(commit)
        elif lower_msg.startswith("remove") or lower_msg.startswith("del"):
            categories["Removed"].append(commit)
        else:
            # Default to changed
            categories["Changed"].append(commit)
            
    return categories

def generate_markdown(categories, tag):
    today = datetime.now().strftime("%Y-%m-%d")
    version = "Unreleased"
    if tag:
        # Assuming next version will just be dated
        version = f"Next Release ({today})"
    else:
        version = f"Initial Release ({today})"
        
    lines = [f"# CHANGELOG", "", f"## [{version}]"]
    
    for cat, items in categories.items():
        if items:
            lines.append(f"\n### {cat}")
            for item in items:
                # Remove prefixes like feat: or fix: for cleaner output
                cleaned = re.sub(r'^[a-zA-Z]+\s*(\([^)]+\))?:\s*', '', item, flags=re.IGNORECASE)
                lines.append(f"- {cleaned}")
                
    return "\n".join(lines)

def main():
    tag = get_last_tag()
    if not tag:
        print("No tags found. Generating changelog for all commits.")
        
    commits = get_commits_since(tag)
    if not commits:
        print("No commits found.")
        sys.exit(0)
        
    categories = parse_commits(commits)
    markdown = generate_markdown(categories, tag)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(markdown)
        
    print("CHANGELOG.md generated successfully!")
    print("\nSample Output:")
    print("-" * 20)
    print(markdown)

if __name__ == "__main__":
    main()
