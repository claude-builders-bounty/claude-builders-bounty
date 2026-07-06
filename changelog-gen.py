#!/usr/bin/env python3
"""
changelog-gen - Generate structured CHANGELOG.md from git history.

Usage:
    ./changelog-gen.sh          # Generate CHANGELOG.md for current repo
    ./changelog-gen.sh --tag v1.0.0  # Generate with specific version
"""

import subprocess
import sys
import re
from datetime import datetime

def run_git(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=".")
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""

def categorize_commit(msg):
    """Categorize a commit message into Added/Fixed/Changed/Removed."""
    msg_lower = msg.lower()
    
    categories = {
        "Added": ["add", "create", "implement", "introduce", "new", "feat", "feature", "support"],
        "Fixed": ["fix", "bug", "hotfix", "patch", "resolve", "correct", "repair"],
        "Changed": ["update", "change", "refactor", "improve", "migrate", "upgrade", "bump", "chore", "perf"],
        "Removed": ["remove", "delete", "drop", "deprecate", "cleanup"],
    }
    
    # Try conventional commit format first
    conventional = re.match(r'^(feat|fix|refactor|chore|docs|test|perf|style|ci|build)(\(.+\))?:\s*(.*)', msg)
    if conventional:
        type_map = {
            "feat": "Added", "fix": "Fixed", "refactor": "Changed",
            "chore": "Changed", "docs": "Changed", "test": "Changed",
            "perf": "Changed", "style": "Changed", "ci": "Changed", "build": "Changed"
        }
        return type_map.get(conventional.group(1), "Changed"), conventional.group(3)
    
    # Fall back to keyword matching
    for category, keywords in categories.items():
        for kw in keywords:
            if msg_lower.startswith(kw):
                return category, msg
    
    return "Changed", msg

def generate_changelog(since_tag=None):
    """Generate changelog content."""
    # Get the last tag
    if not since_tag:
        since_tag = run_git(["git", "describe", "--tags", "--abbrev=0"])
    
    if since_tag:
        log = run_git(["git", "log", f"{since_tag}..HEAD", "--oneline", "--no-merges"])
        version = since_tag
    else:
        # No tags - get all commits
        log = run_git(["git", "log", "--oneline", "--no-merges", "-50"])
        version = "Unreleased"
    
    if not log:
        return f"# Changelog\n\n## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\nNo changes since last release."
    
    # Parse commits
    commits = []
    for line in log.split("\n"):
        if not line.strip():
            continue
        match = re.match(r'([a-f0-9]+)\s+(.*)', line)
        if match:
            sha, msg = match.group(1), match.group(2)
            category, clean_msg = categorize_commit(msg)
            commits.append((category, clean_msg, sha[:7]))
    
    # Build changelog
    lines = [f"# Changelog\n", f"", f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}", ""]
    
    categories_order = ["Added", "Changed", "Fixed", "Removed"]
    for cat in categories_order:
        items = [c for c in commits if c[0] == cat]
        if items:
            lines.append(f"### {cat}")
            for _, msg, sha in items:
                lines.append(f"- {msg} ({sha})")
            lines.append("")
    
    return "\n".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--tag", help="Generate changelog since this tag")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    args = parser.parse_args()
    
    changelog = generate_changelog(since_tag=args.tag)
    print(changelog)
    
    with open(args.output, "w") as f:
        f.write(changelog)
    print(f"\nWritten to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
