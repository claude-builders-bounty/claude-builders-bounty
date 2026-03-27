#!/usr/bin/env python3
"""
CHANGELOG Generator from Git History
Usage: python generate_changelog.py [--output CHANGELOG.md]
"""

import subprocess
import re
import sys
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Optional


def run_git_command(cmd: List[str]) -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ['git'] + cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_repo_url() -> str:
    """Get the GitHub repository URL."""
    remote_url = run_git_command(['remote', 'get-url', 'origin'])
    if not remote_url:
        return "https://github.com/local/repo"
    
    # Convert git@github.com:user/repo.git to https://github.com/user/repo
    match = re.search(r'github\.com[/:]([^/]+/[^.]+)', remote_url)
    if match:
        return f"https://github.com/{match.group(1)}"
    return "https://github.com/local/repo"


def get_tags() -> List[str]:
    """Get all tags sorted by version (descending)."""
    tags = run_git_command(['tag', '--sort=-v:refname']).split('\n')
    return [t for t in tags if t]


def categorize_commit(message: str) -> str:
    """Categorize a commit based on its message prefix."""
    prefixes = {
        'feat': 'Added',
        'feature': 'Added',
        'fix': 'Fixed',
        'docs': 'Documentation',
        'style': 'Changed',
        'refactor': 'Changed',
        'perf': 'Performance',
        'test': 'Testing',
        'build': 'Build',
        'ci': 'CI/CD',
        'chore': 'Maintenance',
    }
    
    for prefix, category in prefixes.items():
        if message.lower().startswith(prefix):
            return category
    
    return 'Other'


def format_commit(hash: str, message: str, repo_url: str) -> str:
    """Format a commit for the changelog."""
    # Remove conventional commit prefix
    clean_message = re.sub(r'^(feat|feature|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?:\s*', '', message, flags=re.IGNORECASE)
    
    # Capitalize first letter
    if clean_message:
        clean_message = clean_message[0].upper() + clean_message[1:]
    
    short_hash = hash[:7]
    return f"- {clean_message} ([`{short_hash}`]({repo_url}/commit/{hash}))"


def get_commits(ref_range: str = "") -> List[Tuple[str, str]]:
    """Get commits with their hashes and messages."""
    cmd = ['log', '--pretty=format:%H|%s', '--no-merges']
    if ref_range:
        cmd.append(ref_range)
    
    output = run_git_command(cmd)
    commits = []
    
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|', 1)
            if len(parts) == 2:
                commits.append((parts[0], parts[1]))
    
    return commits


def get_tag_date(tag: str) -> str:
    """Get the date of a tag."""
    output = run_git_command(['log', '-1', '--format=%ai', tag])
    if output:
        return output.split(' ')[0]
    return "Unknown"


def generate_changelog(output_file: str = "CHANGELOG.md"):
    """Generate the changelog from git history."""
    repo_url = get_repo_url()
    tags = get_tags()
    
    lines = [
        "# Changelog",
        "",
        "> All notable changes to this project will be documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
    ]
    
    if not tags:
        # No tags - all commits are unreleased
        lines.append("## [Unreleased]")
        lines.append("")
        
        commits = get_commits()
        categories = defaultdict(list)
        
        for hash, message in commits:
            category = categorize_commit(message)
            categories[category].append((hash, message))
        
        for category in ['Added', 'Changed', 'Fixed', 'Documentation', 'Performance', 'Testing', 'Build', 'CI/CD', 'Maintenance', 'Other']:
            if categories[category]:
                lines.append(f"### {category}")
                for hash, message in categories[category]:
                    lines.append(format_commit(hash, message, repo_url))
                lines.append("")
    else:
        # Process unreleased commits
        latest_tag = tags[0]
        unreleased_commits = get_commits(f"{latest_tag}..HEAD")
        
        if unreleased_commits:
            lines.append("## [Unreleased]")
            lines.append("")
            
            categories = defaultdict(list)
            for hash, message in unreleased_commits:
                category = categorize_commit(message)
                categories[category].append((hash, message))
            
            for category in ['Added', 'Changed', 'Fixed', 'Documentation', 'Performance', 'Testing', 'Build', 'CI/CD', 'Maintenance', 'Other']:
                if categories[category]:
                    lines.append(f"### {category}")
                    for hash, message in categories[category]:
                        lines.append(format_commit(hash, message, repo_url))
                    lines.append("")
        
        # Process each tagged version
        prev_tag = None
        for tag in tags:
            tag_date = get_tag_date(tag)
            version = tag.lstrip('v')
            
            lines.append(f"## [{version}] - {tag_date}")
            lines.append("")
            
            # Get commits for this version
            if prev_tag:
                commits = get_commits(f"{prev_tag}..{tag}")
            else:
                commits = get_commits(tag)
            
            if commits:
                categories = defaultdict(list)
                for hash, message in commits:
                    category = categorize_commit(message)
                    categories[category].append((hash, message))
                
                for category in ['Added', 'Changed', 'Fixed', 'Documentation', 'Performance', 'Testing', 'Build', 'CI/CD', 'Maintenance', 'Other']:
                    if categories[category]:
                        lines.append(f"### {category}")
                        for hash, message in categories[category]:
                            lines.append(format_commit(hash, message, repo_url))
                        lines.append("")
            
            prev_tag = tag
    
    # Add links section
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"[Unreleased]: {repo_url}/compare/HEAD..HEAD")
    
    prev_tag = None
    for tag in tags:
        version = tag.lstrip('v')
        if prev_tag:
            prev_version = prev_tag.lstrip('v')
            lines.append(f"[{version}]: {repo_url}/compare/{prev_tag}..{tag}")
        else:
            lines.append(f"[{version}]: {repo_url}/releases/tag/{tag}")
        prev_tag = tag
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Generated by [generate-changelog](https://github.com/ljapptest-art/generate-changelog)_")
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ CHANGELOG generated: {output_file}")


if __name__ == "__main__":
    output_file = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == '--output' else "CHANGELOG.md"
    generate_changelog(output_file)
