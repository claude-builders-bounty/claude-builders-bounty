#!/usr/bin/env python3
"""
CHANGELOG Generator - Generates structured CHANGELOG.md from git history.
Usage: python generate_changelog.py [--repo PATH] [--output FILE]
"""
import subprocess
import re
import sys
import argparse
from datetime import datetime
from collections import defaultdict

# Commit type patterns
CATEGORIES = {
    "Added": [
        r"^feat[:(]",
        r"^add[:(]",
        r"^new[:(]",
        r"^implement",
        r"^create",
    ],
    "Fixed": [
        r"^fix[:(]",
        r"^bugfix[:(]",
        r"^patch[:(]",
        r"^resolve",
        r"^correct",
    ],
    "Changed": [
        r"^refactor[:(]",
        r"^change[:(]",
        r"^update[:(]",
        r"^modify",
        r"^improve",
        r"^perf[:(]",
        r"^style[:(]",
    ],
    "Removed": [
        r"^remove[:(]",
        r"^delete[:(]",
        r"^deprecate[:(]",
        r"^drop[:(]",
    ],
}

def get_last_tag(repo_path="."):
    """Get the last git tag."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None

def get_commits_since_tag(tag=None, repo_path="."):
    """Get commits since a tag (or all commits if no tag)."""
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--pretty=format:%H|%s|%ai"]
    else:
        cmd = ["git", "log", "--pretty=format:%H|%s|%ai", "--max-count=500"]
    
    try:
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=30)
        commits = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 2)
                if len(parts) == 3:
                    commits.append({
                        "hash": parts[0][:8],
                        "message": parts[1],
                        "date": parts[2].split(" ")[0],
                    })
        return commits
    except Exception:
        return []

def categorize_commit(message):
    """Categorize a commit message."""
    msg_lower = message.lower()
    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return category
    return "Changed"  # Default category

def generate_changelog(repo_path=".", output_file="CHANGELOG.md"):
    """Generate CHANGELOG.md from git history."""
    tag = get_last_tag(repo_path)
    commits = get_commits_since_tag(tag, repo_path)
    
    if not commits:
        print("No commits found.")
        return
    
    # Group commits by category
    categorized = defaultdict(list)
    for commit in commits:
        category = categorize_commit(commit["message"])
        categorized[category].append(commit)
    
    # Generate changelog
    lines = []
    lines.append("# Changelog")
    lines.append("")
    
    version = tag if tag else "Unreleased"
    date = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"## [{version}] - {date}")
    lines.append("")
    
    category_order = ["Added", "Fixed", "Changed", "Removed"]
    for category in category_order:
        if category in categorized:
            lines.append(f"### {category}")
            lines.append("")
            for commit in categorized[category]:
                lines.append(f"- {commit['message']} ({commit['hash']})")
            lines.append("")
    
    # Write to file
    with open(output_file, "w") as f:
        f.write("\n".join(lines))
    
    print(f"Generated {output_file} with {len(commits)} commits")
    return "\n".join(lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--repo", default=".", help="Path to git repository")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    args = parser.parse_args()
    
    changelog = generate_changelog(args.repo, args.output)
    if changelog:
        print("\n" + changelog)
