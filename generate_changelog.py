#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.

Usage:
    python generate_changelog.py
    python generate_changelog.py --output CHANGELOG.md
    python generate_changelog.py --since v1.0.0
"""

import subprocess
import re
import argparse
from datetime import datetime
from collections import defaultdict


def run_git_command(cmd):
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_last_tag():
    """Get the most recent git tag."""
    tags = run_git_command("git tag --sort=-creatordate")
    if tags:
        return tags.split("\n")[0]
    return None


def get_commits_since(tag=None):
    """Get commits since the last tag or all commits."""
    if tag:
        cmd = f'git log {tag}..HEAD --pretty=format:"%H|%s|%ad" --date=short'
    else:
        cmd = 'git log --pretty=format:"%H|%s|%ad" --date=short'
    
    output = run_git_command(cmd)
    commits = []
    
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append({
                    "hash": parts[0][:7],
                    "message": parts[1],
                    "date": parts[2]
                })
    
    return commits


def categorize_commit(message):
    """Categorize a commit based on conventional commit format."""
    message_lower = message.lower()
    
    # Check for conventional commit prefixes
    if re.match(r"^(feat|add|new)", message_lower):
        return "Added"
    elif re.match(r"^(fix|bug|hotfix)", message_lower):
        return "Fixed"
    elif re.match(r"^(change|update|modify|refactor|improve)", message_lower):
        return "Changed"
    elif re.match(r"^(remove|delete|drop|deprecate)", message_lower):
        return "Removed"
    elif re.match(r"^(doc|readme|comment)", message_lower):
        return "Documentation"
    elif re.match(r"^(test|testing)", message_lower):
        return "Tests"
    elif re.match(r"^(security|vuln|cve)", message_lower):
        return "Security"
    else:
        # Default categorization based on keywords
        if any(word in message_lower for word in ["add", "introduce", "create", "implement"]):
            return "Added"
        elif any(word in message_lower for word in ["fix", "resolve", "correct", "patch"]):
            return "Fixed"
        elif any(word in message_lower for word in ["update", "change", "modify", "refactor", "upgrade"]):
            return "Changed"
        elif any(word in message_lower for word in ["remove", "delete", "drop", "clean"]):
            return "Removed"
        else:
            return "Changed"  # Default category


def generate_changelog(commits, version=None):
    """Generate a structured CHANGELOG.md content."""
    if not version:
        version = f"v{datetime.now().strftime('%Y.%m.%d')}"
    
    # Categorize commits
    categories = defaultdict(list)
    for commit in commits:
        category = categorize_commit(commit["message"])
        categories[category].append(commit)
    
    # Build changelog
    lines = []
    lines.append("# Changelog")
    lines.append("")
    lines.append("All notable changes to this project will be documented in this file.")
    lines.append("")
    lines.append(f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    
    # Order of categories
    category_order = ["Added", "Changed", "Fixed", "Removed", "Security", "Documentation", "Tests"]
    
    for category in category_order:
        if category in categories and categories[category]:
            lines.append(f"### {category}")
            lines.append("")
            for commit in categories[category]:
                lines.append(f"- {commit['message']} ({commit['hash']})")
            lines.append("")
    
    # Add footer
    lines.append("---")
    lines.append("")
    lines.append("*This changelog was automatically generated from git history.*")
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)"
    )
    parser.add_argument(
        "--since",
        "-s",
        help="Generate changelog since specific tag (default: last tag)"
    )
    parser.add_argument(
        "--version",
        "-v",
        help="Version number for this release"
    )
    
    args = parser.parse_args()
    
    # Check if we're in a git repository
    if not run_git_command("git rev-parse --git-dir"):
        print("Error: Not a git repository. Please run this script from a git project.")
        return 1
    
    # Determine starting point
    if args.since:
        tag = args.since
    else:
        tag = get_last_tag()
    
    # Get commits
    commits = get_commits_since(tag)
    
    if not commits:
        print("No commits found since the specified tag.")
        return 0
    
    print(f"Found {len(commits)} commits since {tag or 'beginning'}")
    
    # Generate changelog
    changelog = generate_changelog(commits, args.version)
    
    # Write to file
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(changelog)
    
    print(f"✅ Changelog generated: {args.output}")
    print(f"   Categories: {', '.join(set(categorize_commit(c['message']) for c in commits))}")
    
    return 0


if __name__ == "__main__":
    exit(main())
