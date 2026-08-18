#!/usr/bin/env python3
"""
CHANGELOG Generator

Automatically generates a structured CHANGELOG.md from git history.
Categorizes commits into: Added / Fixed / Changed / Removed
"""

import subprocess
import re
from datetime import datetime
from typing import List, Dict


def get_last_tag() -> str:
    """Get the most recent git tag."""
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


def get_commits_since_tag(tag: str = None) -> List[str]:
    """Get commit messages since the last tag."""
    if tag:
        ref = f"{tag}..HEAD"
    else:
        ref = "HEAD"
    
    try:
        result = subprocess.run(
            ["git", "log", ref, "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def categorize_commit(message: str) -> str:
    """Categorize a commit message based on conventional commits."""
    message_lower = message.lower()
    
    # Added patterns
    if any(word in message_lower for word in ['add', 'added', 'add:', 'feat:', 'feature', 'new', 'create', 'implement']):
        return 'Added'
    
    # Fixed patterns
    if any(word in message_lower for word in ['fix', 'fixed', 'fix:', 'bug', 'bugfix', 'resolve', 'correct', 'patch']):
        return 'Fixed'
    
    # Removed patterns
    if any(word in message_lower for word in ['remove', 'removed', 'remove:', 'delete', 'deleted', 'deprecate', 'deprecation']):
        return 'Removed'
    
    # Changed patterns (default)
    if any(word in message_lower for word in ['change', 'changed', 'change:', 'update', 'updated', 'modify', 'modified', 'refactor', 'improve', 'improved']):
        return 'Changed'
    
    # Default to Changed for uncategorized
    return 'Changed'


def generate_changelog(commits: List[str], version: str = "Unreleased") -> str:
    """Generate the CHANGELOG.md content."""
    categorized = {
        'Added': [],
        'Fixed': [],
        'Changed': [],
        'Removed': []
    }
    
    for commit in commits:
        category = categorize_commit(commit)
        categorized[category].append(commit)
    
    # Build changelog
    changelog = f"# Changelog\n\n"
    changelog += f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    for category in ['Added', 'Fixed', 'Changed', 'Removed']:
        if categorized[category]:
            changelog += f"### {category}\n\n"
            for commit in categorized[category]:
                changelog += f"- {commit}\n"
            changelog += "\n"
    
    if not any(categorized.values()):
        changelog += "No changes since last release.\n"
    
    return changelog


def main():
    """Main function to generate CHANGELOG."""
    print("📝 Generating CHANGELOG from git history...")
    
    # Get last tag
    last_tag = get_last_tag()
    if last_tag:
        print(f"📌 Last tag: {last_tag}")
        version = f"v{last_tag}"
    else:
        print("📌 No tags found, using all commits")
        version = "Unreleased"
    
    # Get commits
    commits = get_commits_since_tag(last_tag)
    print(f"📊 Found {len(commits)} commits")
    
    if not commits:
        print("⚠️  No commits found. CHANGELOG will be empty.")
    
    # Generate changelog
    changelog_content = generate_changelog(commits, version)
    
    # Write to file
    with open('CHANGELOG.md', 'w') as f:
        f.write(changelog_content)
    
    print(f"✅ CHANGELOG.md generated successfully!")
    print(f"📄 Version: {version}")
    print(f"📝 Commits processed: {len(commits)}")


if __name__ == "__main__":
    main()