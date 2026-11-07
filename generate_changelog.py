#!/usr/bin/env python3
import subprocess
import sys
import re

def get_latest_tag():
    try:
        tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], stderr=subprocess.DEVNULL).decode().strip()
        return tag
    except subprocess.CalledProcessError:
        return None

def get_commits(since_tag=None):
    cmd = ["git", "log", "--pretty=format:%s"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    output = subprocess.check_output(cmd).decode().strip()
    return output.split("\n") if output else []

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for commit in commits:
        commit = commit.strip()
        if not commit:
            continue
            
        lower_c = commit.lower()
        if re.match(r'^(feat|add)\b', lower_c) or "add" in lower_c:
            categories["Added"].append(commit)
        elif re.match(r'^(fix|bug|patch)\b', lower_c) or "fix" in lower_c:
            categories["Fixed"].append(commit)
        elif re.match(r'^(remove|delete|drop|del)\b', lower_c) or "remov" in lower_c:
            categories["Removed"].append(commit)
        else:
            categories["Changed"].append(commit)
            
    return categories

def generate_markdown(categories, tag):
    lines = [f"# Changelog"]
    if tag:
        lines.append(f"\n## Changes since tag: {tag}")
    else:
        lines.append(f"\n## All Changes")
        
    for category in ["Added", "Fixed", "Changed", "Removed"]:
        if categories[category]:
            lines.append(f"\n### {category}")
            for commit in categories[category]:
                lines.append(f"- {commit}")
                
    return "\n".join(lines)

if __name__ == "__main__":
    tag = get_latest_tag()
    commits = get_commits(tag)
    cats = categorize_commits(commits)
    md = generate_markdown(cats, tag)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(md)
        
    print("Successfully generated CHANGELOG.md!")
