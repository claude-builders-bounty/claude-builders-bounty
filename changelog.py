#!/usr/bin/env python3
"""
CHANGELOG Generator — Generates a structured CHANGELOG.md from git history.

Usage:
    python3 changelog.py [--output CHANGELOG.md] [--repo /path/to/repo]

Categories commits by conventional commits prefixes:
    Added      — feat, feature
    Fixed      — fix, bugfix
    Changed    — refactor, perf, chore
    Removed    — removed features
"""
import argparse
import subprocess
import re
import os
from collections import defaultdict
from datetime import datetime

CATEGORIES = {
    "Added": ["feat", "feature"],
    "Fixed": ["fix", "bugfix", "bug"],
    "Changed": ["refactor", "perf", "chore", "style", "deps"],
    "Removed": ["remove", "revert"],
}

COMMIT_PATTERN = re.compile(
    r'^(?P<type>[a-zA-Z]+)(\([^)]*\))?!?:\s*(?P<message>.+)$'
)

def get_tags(repo_path):
    """Get all tags sorted by version (semver)."""
    result = subprocess.run(
        ["git", "tag", "--sort=-version:refname"],
        capture_output=True, text=True, cwd=repo_path, timeout=10
    )
    tags = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
    return tags

def get_first_commit(repo_path):
    """Get the first commit hash."""
    result = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        capture_output=True, text=True, cwd=repo_path, timeout=10
    )
    return result.stdout.strip()

def get_commits(repo_path, since="", until="HEAD"):
    """Get commits in a range."""
    if since:
        rev_range = f"{since}..{until}"
    else:
        rev_range = until
    
    result = subprocess.run(
        ["git", "log", rev_range, "--oneline", "--no-decorate"],
        capture_output=True, text=True, cwd=repo_path, timeout=10
    )
    commits = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append((parts[0], parts[1]))
    return commits

def categorize_commit(message):
    """Categorize a commit message."""
    m = COMMIT_PATTERN.match(message)
    if m:
        commit_type = m.group("type").lower()
        commit_msg = m.group("message").strip()
        for category, prefixes in CATEGORIES.items():
            if commit_type in prefixes:
                return category, commit_msg
    return "Changed", message

def generate_changelog(repo_path=".", output="CHANGELOG.md"):
    """Generate changelog."""
    tags = get_tags(repo_path)
    changelog = []
    
    changelog.append("# Changelog")
    changelog.append("")
    
    # Unreleased section first
    if tags:
        unreleased_since = tags[0]
    else:
        unreleased_since = ""
    
    unreleased = get_commits(repo_path, since=unreleased_since, until="HEAD")
    if unreleased:
        changelog.append("## [Unreleased]")
        changelog.append("")
        categorized = defaultdict(list)
        for _, msg in unreleased:
            cat, clean_msg = categorize_commit(msg)
            categorized[cat].append(f"- {clean_msg}")
        for cat in ["Added", "Fixed", "Changed", "Removed"]:
            if categorized[cat]:
                changelog.append(f"### {cat}")
                changelog.extend(categorized[cat])
                changelog.append("")
    
    # Tagged releases
    for i, tag in enumerate(tags):
        next_tag = tags[i + 1] if i + 1 < len(tags) else ""
        since = next_tag if next_tag else ""
        commits = get_commits(repo_path, since=since, until=tag)
        
        if not commits and not since:
            commits = get_commits(repo_path, since=get_first_commit(repo_path), until=tag)
        
        changelog.append(f"## [{tag}]")
        changelog.append("")
        
        categorized = defaultdict(list)
        for _, msg in commits:
            cat, clean_msg = categorize_commit(msg)
            categorized[cat].append(f"- {clean_msg}")
        
        if not any(categorized.values()):
            changelog.append("- Initial release")
            changelog.append("")
        else:
            for cat in ["Added", "Fixed", "Changed", "Removed"]:
                if categorized[cat]:
                    changelog.append(f"### {cat}")
                    changelog.extend(categorized[cat])
                    changelog.append("")
    
    with open(os.path.join(repo_path, output), "w") as f:
        f.write("\n".join(changelog))
    
    print(f"✅ Generated {output} with {len(changelog)} lines")

def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    parser.add_argument("--repo", default=".", help="Path to git repository (default: current dir)")
    args = parser.parse_args()
    generate_changelog(repo_path=args.repo, output=args.output)

if __name__ == "__main__":
    main()
