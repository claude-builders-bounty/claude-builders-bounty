#!/usr/bin/env python3
import subprocess
import re
import datetime
import sys

#generates a changelog.md from git history

#default file name
OUTPUT_FILE = "CHANGELOG.md"

def get_last_tag():
    #get the last tag, if any
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"], 
            stderr=subprocess.DEVNULL, 
            text=True
        ).strip()
        return tag
    except subprocess.CalledProcessError:
        return None

def get_commits(tag):
    log_range = f"{tag}..HEAD" if tag else ""
    cmd = ["git", "log", "--pretty=format:- %s"]
    if log_range:
        cmd.insert(2, log_range)
    
    try:
        output = subprocess.check_output(cmd, text=True).strip()
        if not output:
            return []
        return output.split('\n')
    except subprocess.CalledProcessError:
        return []

def generate_changelog():
    tag = get_last_tag()
    if tag:
        print(f"Generating changelog since tag: {tag}")
    else:
        print("No tags found. Generating changelog from all commits.")

    commits = get_commits(tag)

    #arrays for categorized commits
    categories = {
        "Added": [],
        "Fixed": [],
        "Removed": [],
        "Changed": []
    }

    #process each commit message
    for commit in commits:
        if not commit.strip():
            continue
            
        #lowercase the message for easier matching
        lower_msg = commit.lower()
        
        #categorize based on keywords
        if re.match(r'^-\s*(feat|add|new)', lower_msg):
            categories["Added"].append(commit)
        elif re.match(r'^-\s*(fix|bug|patch)', lower_msg):
            categories["Fixed"].append(commit)
        elif re.match(r'^-\s*(remove|del|drop)', lower_msg):
            categories["Removed"].append(commit)
        else:
            #default to changed for everything else
            categories["Changed"].append(commit)

    #write to changelog.md
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Changelog\n\n")
        
        #add current date
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        f.write(f"## [Unreleased] - {today}\n\n")

        for cat in ["Added", "Fixed", "Changed", "Removed"]:
            if categories[cat]:
                f.write(f"### {cat}\n")
                for msg in categories[cat]:
                    f.write(f"{msg}\n")
                f.write("\n")

    print(f"{OUTPUT_FILE} generated successfully!")

if __name__ == "__main__":
    generate_changelog()
