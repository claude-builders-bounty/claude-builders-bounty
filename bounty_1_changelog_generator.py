#!/usr/bin/env python3
"""
Bounty #1: CHANGELOG Generator
Parses git commit messages in Conventional Commits format and generates
a structured CHANGELOG file.

Usage:
    python changelog_generator.py [--since <tag>] [--until <tag>] [--output <file>]

Example:
    python changelog_generator.py --since v1.0.0 --until v2.0.0 --output CHANGELOG.md
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG from git commit messages"
    )
    parser.add_argument(
        "--since",
        help="Generate CHANGELOG since this tag (inclusive)",
    )
    parser.add_argument(
        "--until",
        help="Generate CHANGELOG until this tag (exclusive)",
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--format",
        choices=["MARKDOWN", "JSON"],
        default="MARKDOWN",
        help="Output format (default: MARKDOWN)",
    )
    return parser.parse_args()


def run_git(*args):
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"Git error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_commits_since(since_tag):
    """Get commit messages since a given tag."""
    if since_tag:
        log = run_git(
            "log", f"--since={since_tag}", "--pretty=format:%s",
        )
    else:
        log = run_git("log", "--pretty=format:%s", "-100")
    return [line.strip() for line in log.split("\n") if line.strip()]


def parse_conventional_commit(commit_msg):
    """
    Parse a conventional commit message.
    
    Format: <type>(<scope>): <subject>
    Or: <type>: <subject>
    
    Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
    """
    pattern = r"^(\w+)((\([^)]+\))?)?: (.+)$"
    match = re.match(pattern, commit_msg)
    if not match:
        return None
    
    commit_type = match.group(1)
    scope = match.group(2).strip("()") if match.group(2) else None
    subject = match.group(4)
    
    # Map conventional commit types to categories
    type_map = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "docs": "Documentation",
        "style": "Styles",
        "refactor": "Refactoring",
        "perf": "Performance",
        "test": "Tests",
        "build": "Build",
        "ci": "CI/CD",
        "chore": "Chores",
    }
    
    category = type_map.get(commit_type, "Other")
    
    return {
        "type": commit_type,
        "scope": scope,
        "subject": subject,
        "category": category,
    }


def generate_changelog(commits, since_tag, until_tag):
    """Generate CHANGELOG content from commit messages."""
    # Categorize commits
    categories = defaultdict(list)
    for commit_msg in commits:
        parsed = parse_conventional_commit(commit_msg)
        if parsed:
            categories[parsed["category"]].append(parsed)
        else:
            # Non-conventional commits go in "Other"
            categories["Other"].append({
                "type": "other",
                "scope": None,
                "subject": commit_msg,
                "category": "Other",
            })
    
    # Sort commits within each category by type order
    type_order = {
        "feat": 1, "fix": 2, "docs": 3, "style": 4,
        "refactor": 5, "perf": 6, "test": 7,
        "build": 8, "ci": 9, "chore": 10,
    }
    
    lines = []
    lines.append("# Changelog")
    lines.append("")
    
    # Get the latest version/tag info
    if since_tag:
        lines.append(f"Generated between {since_tag} and future version")
    else:
        lines.append("Generated from git commit history")
    lines.append("")
    
    # Build the CHANGELOG entries
    for category_name in sorted(categories.keys()):
        commits_in_category = categories[category_name]
        if not commits_in_category:
            continue
        
        lines.append(f"## {category_name}")
        lines.append("")
        
        for commit in commits_in_category:
            scope_prefix = f"({commit['scope']})" if commit['scope'] else ""
            lines.append(f"- **{commit['type'].title()}**{scope_prefix}: {commit['subject']}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    args = parse_args()
    
    # Get commit messages
    commits = get_commits_since(args.since)
    
    # Generate CHANGELOG
    changelog_content = generate_changelog(commits, args.since, args.until)
    
    # Write to output file
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(changelog_content)
    
    print(f"CHANGELOG generated: {args.output}")
    print(f"Total commits processed: {len(commits)}")
    
    # Print summary by category
    categories_count = defaultdict(int)
    for commit_msg in commits:
        parsed = parse_conventional_commit(commit_msg)
        if parsed:
            categories_count[parsed["category"]] += 1
        else:
            categories_count["Other"] += 1
    
    print("\nCommit summary:")
    for category, count in sorted(categories_count.items()):
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()