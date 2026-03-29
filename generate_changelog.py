#!/usr/bin/env python3
"""
CHANGELOG Generator - Automatically generate structured CHANGELOG.md from git history
Categorizes commits into: Added / Fixed / Changed / Removed
"""

import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def get_git_tags() -> List[str]:
    """Get all git tags sorted by date (newest first)"""
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "--sort=-version:refname"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def get_commits_since_tag(tag: str = None) -> List[Dict]:
    """Get commits since the last tag (or all commits if no tag exists)"""
    try:
        if tag:
            commit_range = f"{tag}..HEAD"
        else:
            commit_range = "HEAD"
        
        result = subprocess.run(
            ["git", "log", commit_range, "--pretty=format:%H|%s|%b|%an|%ai"],
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 4)
            if len(parts) >= 2:
                commits.append({
                    'hash': parts[0][:7],
                    'subject': parts[1],
                    'body': parts[2] if len(parts) > 2 else '',
                    'author': parts[3] if len(parts) > 3 else 'Unknown',
                    'date': parts[4] if len(parts) > 4 else '',
                })
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Error getting commits: {e}", file=sys.stderr)
        return []


def categorize_commit(subject: str, body: str) -> str:
    """Categorize a commit into Added / Fixed / Changed / Removed"""
    text = (subject + " " + body).lower()
    
    # Check for keywords in order of specificity
    if any(keyword in text for keyword in ['fix:', 'fixed', 'bug fix', 'resolve', 'closes #', 'fixes #']):
        return 'Fixed'
    elif any(keyword in text for keyword in ['feat:', 'feature', 'add:', 'added', 'new']):
        return 'Added'
    elif any(keyword in text for keyword in ['remove:', 'removed', 'delete:', 'deleted', 'deprecat']):
        return 'Removed'
    elif any(keyword in text for keyword in ['refactor', 'improve', 'update', 'change', 'modif']):
        return 'Changed'
    else:
        return 'Changed'  # Default category


def format_commit_message(subject: str, hash: str) -> str:
    """Format a commit message for CHANGELOG"""
    # Remove common prefixes
    subject = re.sub(r'^(feat|fix|docs|style|refactor|perf|test|chore):\s*', '', subject)
    # Capitalize first letter if not already
    if subject and subject[0].islower():
        subject = subject[0].upper() + subject[1:]
    return f"- {subject} ([{hash}](https://github.com/claude-builders-bounty/claude-builders-bounty/commit/{hash} ))"


def generate_changelog(repo_path: str = ".") -> str:
    """Generate CHANGELOG.md content"""
    # Change to repo directory
    original_cwd = Path.cwd()
    try:
        repo = Path(repo_path).resolve()
        if not (repo / ".git").exists():
            print(f"Error: {repo} is not a git repository", file=sys.stderr)
            return ""
        
        import os
        os.chdir(repo)
        
        # Get tags
        tags = get_git_tags()
        
        # Get current version (from latest tag or use "Unreleased")
        latest_tag = tags[0] if tags else None
        
        # Get commits since last tag
        commits = get_commits_since_tag(latest_tag)
        
        if not commits:
            return "# CHANGELOG\n\nNo commits found since the last tag.\n"
        
        # Categorize commits
        categorized: Dict[str, List[str]] = {
            'Added': [],
            'Fixed': [],
            'Changed': [],
            'Removed': []
        }
        
        for commit in commits:
            category = categorize_commit(commit['subject'], commit['body'])
            formatted = format_commit_message(commit['subject'], commit['hash'])
            categorized[category].append(formatted)
        
        # Build CHANGELOG
        changelog = "# CHANGELOG\n\n"
        changelog += f"## [Unreleased]\n\n"
        
        for category in ['Added', 'Fixed', 'Changed', 'Removed']:
            if categorized[category]:
                changelog += f"### {category}\n\n"
                for item in sorted(set(categorized[category])):  # Remove duplicates
                    changelog += item + "\n"
                changelog += "\n"
        
        # Add historical tags if they exist
        if len(tags) > 1:
            changelog += "## Historical Releases\n\n"
            for tag in tags[:5]:  # Show last 5 tags
                changelog += f"- [{tag}](https://github.com/claude-builders-bounty/claude-builders-bounty/releases/tag/{tag} )\n"
        
        return changelog
    
    finally:
        os.chdir(original_cwd)


def main():
    """Main entry point"""
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    changelog = generate_changelog(repo_path)
    
    if changelog:
        # Write to CHANGELOG.md
        output_file = Path(repo_path) / "CHANGELOG.md"
        output_file.write_text(changelog)
        print(f"✅ CHANGELOG.md generated successfully at {output_file}")
        print(f"\nPreview:\n{changelog[:500]}...")
    else:
        print("❌ Failed to generate CHANGELOG.md", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
