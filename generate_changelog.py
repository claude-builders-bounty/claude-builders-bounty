#!/usr/bin/env python3
import subprocess
import re
import sys
from collections import defaultdict
from datetime import datetime

def get_last_tag():
    """Fetches the latest git tag."""
    try:
        return subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], encoding="utf-8").strip()
    except subprocess.CalledProcessError:
        return None

def get_git_logs(since_tag=None):
    """Fetches git commit logs since the specified tag."""
    try:
        cmd = ["git", "log", "--pretty=format:%H%n%s%n%b%n---COMMIT-END---"]
        if since_tag:
            cmd.append(f"{since_tag}..HEAD")
        
        result = subprocess.check_output(cmd, encoding="utf-8")
        return result.split("---COMMIT-END---")
    except Exception as e:
        print(f"Error reading git logs: {e}")
        return []

def parse_commits(logs):
    """Categorizes commits into Added, Fixed, Changed, Removed."""
    categories = defaultdict(list)
    patterns = {
        "Added": r"feat(?:\(.*\))?:",
        "Fixed": r"fix(?:\(.*\))?:",
        "Changed": r"refactor(?:\(.*\))?:|perf(?:\(.*\))?:|style(?:\(.*\))?:",
        "Removed": r"removed?:"
    }

    for log in logs:
        lines = log.strip().split("\n")
        if len(lines) < 2:
            continue
        
        commit_hash = lines[0][:8]
        subject = lines[1]
        
        matched = False
        for cat, pattern in patterns.items():
            if re.match(pattern, subject, re.IGNORECASE):
                clean_subject = re.sub(pattern, "", subject, flags=re.IGNORECASE).strip()
                categories[cat].append(f"- {clean_subject} ([{commit_hash}])")
                matched = True
                break
        
        if not matched:
            categories["Other"].append(f"- {subject} ([{commit_hash}])")
            
    return categories

def generate_changelog(categories, tag_name=None):
    """Formats the categories into a markdown CHANGELOG."""
    since_info = f" since {tag_name}" if tag_name else ""
    output = [f"# CHANGELOG\n\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{since_info}\n"]
    
    order = ["Added", "Fixed", "Changed", "Removed", "Other"]
    
    for cat in order:
        if cat in categories and categories[cat]:
            output.append(f"## {cat}")
            output.extend(categories[cat])
            output.append("")
            
    return "\n".join(output)

def main():
    tag = get_last_tag()
    logs = get_git_logs(tag)
    
    if not logs or (len(logs) == 1 and not logs[0].strip()):
        print(f"No new commits found{' since ' + tag if tag else ''}.")
        sys.exit(0)
        
    categories = parse_commits(logs)
    changelog_content = generate_changelog(categories, tag)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(changelog_content)
        
    print(f"✅ CHANGELOG.md generated successfully{' since ' + tag if tag else ''}.")

if __name__ == "__main__":
    main()
