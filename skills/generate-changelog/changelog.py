#!/usr/bin/env python3
"""
generate-changelog: Generate structured CHANGELOG.md from git history.

Usage:
    python3 changelog.py [--output CHANGELOG.md] [--since-tag v1.0.0]

Works by:
1. Detecting last git tag (or use --since-tag)
2. Fetching all commits since that tag
3. Auto-categorizing commits into Added/Fixed/Changed/Removed/Other
4. Writing CHANGELOG.md in Keep a Changelog format
"""

import argparse
import subprocess
import re
import sys
from datetime import datetime
from pathlib import Path

# Default category mappings (prefix -> section)
DEFAULT_CATEGORIES = {
    "feat": "Added",
    "feat:": "Added",
    "add": "Added",
    "add:": "Added",
    "feature": "Added",
    "feature:": "Added",
    "fix": "Fixed",
    "fix:": "Fixed",
    "bug": "Fixed",
    "bug:": "Fixed",
    "hotfix": "Fixed",
    "hotfix:": "Fixed",
    "refactor": "Changed",
    "refactor:": "Changed",
    "chore": "Changed",
    "chore:": "Changed",
    "update": "Changed",
    "update:": "Changed",
    "change": "Changed",
    "change:": "Changed",
    "improve": "Changed",
    "improve:": "Changed",
    "remove": "Removed",
    "remove:": "Removed",
    "delete": "Removed",
    "delete:": "Removed",
    "drop": "Removed",
    "drop:": "Removed",
    "docs": "Other",
    "docs:": "Other",
    "test": "Other",
    "test:": "Other",
    "style": "Other",
    "style:": "Other",
    "perf": "Other",
    "perf:": "Other",
    "ci": "Other",
    "ci:": "Other",
    "build": "Other",
    "build:": "Other",
}

def run_git(*args):
    """Run git command and return output."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def get_last_tag():
    """Get the last git tag."""
    tags = run_git("tag", "--sort=-v:refname")
    if not tags:
        return None
    return tags.split("\n")[0]

def get_commits_since_tag(tag):
    """Get all commits since the given tag."""
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"
    
    log = run_git("log", range_spec, "--pretty=format:%H|%s|%an|%ad", "--date=short")
    if not log:
        return []
    
    commits = []
    for line in log.split("\n"):
        parts = line.split("|")
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0][:8],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3]
            })
    return commits

def categorize_commit(subject, categories=None):
    """Categorize a commit based on its prefix."""
    if categories is None:
        categories = DEFAULT_CATEGORIES
    
    subject_lower = subject.lower().strip()
    
    # Check for conventional commit prefix (e.g., "feat: add x")
    match = re.match(r'^(\w+)[:!]?\s*(.*)', subject)
    if match:
        prefix = match.group(1).lower()
        if prefix in categories:
            return categories[prefix]
    
    # Check for full prefix with colon
    for prefix, section in categories.items():
        if subject_lower.startswith(prefix.lower()):
            return section
    
    return "Other"

def generate_changelog(commits, version="Unreleased", date=None):
    """Generate CHANGELOG.md content."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Categorize commits
    categorized = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Other": []
    }
    
    for commit in commits:
        section = categorize_commit(commit["subject"])
        categorized[section].append(commit)
    
    # Generate markdown
    lines = []
    lines.append("# Changelog\n")
    lines.append("## [" + version + "] - " + date + "\n")
    
    # Added
    if categorized["Added"]:
        lines.append("### Added\n")
        for commit in categorized["Added"]:
            lines.append(f"- {commit['subject']}\n")
        lines.append("")
    
    # Fixed
    if categorized["Fixed"]:
        lines.append("### Fixed\n")
        for commit in categorized["Fixed"]:
            lines.append(f"- {commit['subject']}\n")
        lines.append("")
    
    # Changed
    if categorized["Changed"]:
        lines.append("### Changed\n")
        for commit in categorized["Changed"]:
            lines.append(f"- {commit['subject']}\n")
        lines.append("")
    
    # Removed
    if categorized["Removed"]:
        lines.append("### Removed\n")
        for commit in categorized["Removed"]:
            lines.append(f"- {commit['subject']}\n")
        lines.append("")
    
    # Other
    if categorized["Other"]:
        lines.append("### Other\n")
        for commit in categorized["Other"]:
            lines.append(f"- {commit['subject']}\n")
        lines.append("")
    
    return "".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--output", "-o", default="CHANGELOG.md",
                        help="Output file (default: CHANGELOG.md)")
    parser.add_argument("--since-tag", "-t", default=None,
                        help="Tag to use as starting point (default: last tag)")
    parser.add_argument("--version", "-v", default="Unreleased",
                        help="Version string for changelog header (default: Unreleased)")
    args = parser.parse_args()
    
    # Check if inside a git repo
    if run_git("rev-parse", "--git-dir") is None:
        print("Error: Not inside a git repository", file=sys.stderr)
        sys.exit(1)
    
    # Get last tag
    tag = args.since_tag or get_last_tag()
    if tag:
        print(f"Using tag: {tag}")
        commits = get_commits_since_tag(tag)
    else:
        print("No tags found, using all commits")
        commits = get_commits_since_tag(None)
    
    if not commits:
        print("No commits found since tag")
        sys.exit(0)
    
    print(f"Found {len(commits)} commits")
    
    # Generate changelog
    content = generate_changelog(commits, version=args.version)
    
    # Write output
    output_path = Path(args.output)
    output_path.write_text(content, encoding="utf-8")
    
    print(f"Wrote {args.output} ({len(content)} bytes)")

if __name__ == "__main__":
    main()
