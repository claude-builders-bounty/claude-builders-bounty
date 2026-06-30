#!/usr/bin/env python3
"""
CHANGELOG Generator from Git History
Bounty: claude-builders-bounty/claude-builders-bounty #1
Author: FanLi (范蠡)
"""

import subprocess
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Commit categorization keywords
CATEGORIES = {
    "Added": ["add", "create", "new", "implement", "feature", "introduce"],
    "Fixed": ["fix", "bug", "patch", "resolve", "correct", "repair"],
    "Changed": ["change", "update", "modify", "refactor", "improve", "enhance"],
    "Removed": ["remove", "delete", "drop", "deprecate", "clean"],
}

def get_last_tag() -> str:
    """Get the last git tag"""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_commits_since_tag(tag: str = None) -> list[dict]:
    """Get commits since tag (or all commits if no tag)"""
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"
    
    try:
        result = subprocess.run(
            ["git", "log", range_spec, "--pretty=format:%H|%ad|%s", "--date=short"],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append({
                    "hash": parts[0][:8],
                    "date": parts[1],
                    "message": parts[2]
                })
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Error getting commits: {e}")
        return []

def categorize_commit(message: str) -> str:
    """Categorize commit based on message keywords"""
    message_lower = message.lower()
    
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in message_lower:
                return category
    
    return "Changed"  # Default category

def generate_changelog(commits: list[dict]) -> str:
    """Generate formatted CHANGELOG content"""
    categorized = defaultdict(list)
    
    for commit in commits:
        category = categorize_commit(commit["message"])
        categorized[category].append(commit)
    
    # Build CHANGELOG
    changelog = ["# Changelog", "", f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    
    for category in ["Added", "Changed", "Fixed", "Removed"]:
        if category in categorized and categorized[category]:
            changelog.append(f"## {category}")
            changelog.append("")
            
            for commit in categorized[category]:
                changelog.append(f"- {commit['message']} ({commit['hash']}) - {commit['date']}")
            
            changelog.append("")
    
    return "\n".join(changelog)

def main():
    """Main entry point"""
    # Check if we're in a git repo
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository")
        return 1
    
    # Get last tag
    last_tag = get_last_tag()
    if last_tag:
        print(f"Generating CHANGELOG since tag: {last_tag}")
    else:
        print("No tags found, generating from all commits")
    
    # Get commits
    commits = get_commits_since_tag(last_tag)
    
    if not commits:
        print("No commits found")
        return 1
    
    print(f"Found {len(commits)} commits")
    
    # Generate CHANGELOG
    changelog = generate_changelog(commits)
    
    # Write to file
    output_file = Path("CHANGELOG.md")
    output_file.write_text(changelog)
    
    print(f"✅ CHANGELOG.md generated with {len(commits)} commits")
    print(f"📄 Output: {output_file.absolute()}")
    
    return 0

if __name__ == "__main__":
    exit(main())
