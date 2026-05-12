#!/usr/bin/env python3
import subprocess
import sys
import re
from datetime import datetime

def get_last_tag():
    try:
        tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], stderr=subprocess.DEVNULL).decode().strip()
        return tag
    except:
        return None

def get_commits(since_tag=None):
    cmd = ["git", "log", "--pretty=format:%s"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    
    try:
        output = subprocess.check_output(cmd).decode().strip()
        if not output:
            return []
        return output.split("\n")
    except:
        return []

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }
    
    for msg in commits:
        low_msg = msg.lower()
        if re.match(r"^(feat|add|new)", low_msg):
            categories["Added"].append(msg)
        elif re.match(r"^(fix|bug|patch)", low_msg):
            categories["Fixed"].append(msg)
        elif re.match(r"^(remove|del)", low_msg):
            categories["Removed"].append(msg)
        else:
            categories["Changed"].append(msg)
            
    return categories

def generate_markdown(categories):
    date_str = datetime.now().strftime("%Y-%m-%d")
    output = f"# CHANGELOG\n\n## [{date_str}]\n"
    
    for cat, msgs in categories.items():
        if msgs:
            output += f"\n### {cat}\n"
            for m in msgs:
                output += f"- {m}\n"
                
    return output

def main():
    last_tag = get_last_tag()
    commits = get_commits(last_tag)
    
    if not commits:
        print("No new commits found since last tag (or no tag found).")
        return

    categories = categorize_commits(commits)
    markdown = generate_markdown(categories)
    
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(markdown)
    
    print("Successfully generated CHANGELOG.md")

if __name__ == "__main__":
    main()
