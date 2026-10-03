#!/usr/bin/env python3
"""
Generate a structured CHANGELOG from git history.

Usage:
    python scripts/generate_changelog.py [--output FILE] [--since DATE] [--until DATE]

The script outputs a markdown changelog with sections for features, fixes, and others.
"""

import argparse
import subprocess
import sys
from collections import defaultdict

def get_git_log(since=None, until=None):
    cmd = ["git", "log", "--pretty=format:%H|%ad|%s", "--date=short"]
    if since:
        cmd.append(f"--since={since}")
    if until:
        cmd.append(f"--until={until}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip().splitlines()

def parse_commits(lines):
    commits = []
    for line in lines:
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        commit_hash, date_str, subject = parts
        commits.append({"hash": commit_hash, "date": date_str, "subject": subject})
    return commits

def categorize_commits(commits):
    categories = defaultdict(list)
    for c in commits:
        if c["subject"].startswith("feat:"):
            categories["Features"].append(c)
        elif c["subject"].startswith("fix:"):
            categories["Bug Fixes"].append(c)
        else:
            categories["Other"].append(c)
    return categories

def format_changelog(categories):
    lines = ["# Changelog", ""]
    for section, commits in categories.items():
        if not commits:
            continue
        lines.append(f"## {section}")
        lines.append("")
        for c in commits:
            lines.append(f"- {c['subject']} ({c['hash'][:7]}) - {c['date']}")
        lines.append("")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG from git history.")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--since", help="Include commits since this date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Include commits until this date (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        raw_log = get_git_log(args.since, args.until)
    except subprocess.CalledProcessError as e:
        print(f"Error running git: {e}", file=sys.stderr)
        sys.exit(1)

    commits = parse_commits(raw_log)
    categories = categorize_commits(commits)
    changelog = format_changelog(categories)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(changelog)
    else:
        print(changelog)

if __name__ == "__main__":
    main()
