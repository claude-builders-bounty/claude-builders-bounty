#!/usr/bin/env python3
import subprocess
import re
import sys
from collections import defaultdict
from datetime import datetime

# Improved patterns for wider coverage
PATTERNS = {
    "Added": r"^(?:feat|add|new)(?:\(.*\))?:",
    "Fixed": r"^(?:fix|bugfix|patch)(?:\(.*\))?:",
    "Changed": r"^(?:refactor|perf|style|docs|chore|upd|change)(?:\(.*\))?:",
    "Removed": r"^(?:remove|del|deprecate)(?:\(.*\))?:"
}

def get_last_tag():
    """Fetches the latest git tag."""
    try:
        # Get latest tag on current branch
        return subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], 
                                       stderr=subprocess.STDOUT, encoding="utf-8").strip()
    except subprocess.CalledProcessError:
        return None

def get_git_logs(since_tag=None):
    """Fetches git commit logs since the specified tag."""
    try:
        cmd = ["git", "log", "--pretty=format:%H%n%s%n%b%n---COMMIT-END---"]
        if since_tag:
            cmd.append(f"{since_tag}..HEAD")
        
        result = subprocess.check_output(cmd, encoding="utf-8")
        return [c.strip() for c in result.split("---COMMIT-END---") if c.strip()]
    except Exception as e:
        print(f"Error reading git logs: {e}")
        return []

def parse_commits(logs):
    """Categorizes commits into Added, Fixed, Changed, Removed."""
    categories = defaultdict(list)

    for log in logs:
        lines = log.split("\n")
        if len(lines) < 2:
            continue
        
        commit_hash = lines[0][:8]
        subject = lines[1]
        
        matched = False
        for cat, pattern in PATTERNS.items():
            if re.match(pattern, subject, re.IGNORECASE):
                # Clean the subject (remove the prefix)
                clean_subject = re.sub(pattern, "", subject, flags=re.IGNORECASE).strip()
                # Capitalize first letter
                if clean_subject:
                    clean_subject = clean_subject[0].upper() + clean_subject[1:]
                categories[cat].append(f"- {clean_subject} ([{commit_hash}])")
                matched = True
                break
        
        if not matched:
            categories["Other"].append(f"- {subject} ([{commit_hash}])")
            
    return categories

def generate_markdown(categories, tag_name=None):
    """Formats the categories into a markdown CHANGELOG."""
    now_str = datetime.now().strftime('%Y-%m-%d')
    since_info = f" since {tag_name}" if tag_name else " (Full History)"
    
    header = f"# CHANGELOG\n\nGenerated on {now_str}{since_info}\n"
    sections = []
    
    order = ["Added", "Fixed", "Changed", "Removed", "Other"]
    
    for cat in order:
        if cat in categories and categories[cat]:
            sections.append(f"## {cat}")
            sections.extend(categories[cat])
            sections.append("")
            
    return header + "\n" + "\n".join(sections)

def main():
    # Ensure we are in a git repo
    try:
        subprocess.check_call(["git", "rev-parse", "--is-inside-work-tree"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("❌ Error: Not a git repository.")
        sys.exit(1)

    tag = get_last_tag()
    logs = get_git_logs(tag)
    
    if not logs:
        print(f"No new commits found{' since ' + tag if tag else ''}.")
        sys.exit(0)
        
    categories = parse_commits(logs)
    markdown = generate_markdown(categories, tag)
    
    with open("CHANGELOG.md", "w") as f:
        f.write(markdown)
        
    print(f"✅ CHANGELOG.md generated successfully{' since ' + tag if tag else ''}.")

if __name__ == "__main__":
    main()
