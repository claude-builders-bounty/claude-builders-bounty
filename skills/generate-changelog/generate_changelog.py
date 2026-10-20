#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History
Complies with Keep a Changelog (https://keepachangelog.com/en/1.0.0/)
and Conventional Commits specification.
"""

import subprocess
import sys
import re
import argparse
from datetime import datetime
from collections import defaultdict

CATEGORIES = {
    "Added": [
        r"^feat(\(.*\))?:",
        r"^add\b",
        r"^create\b",
        r"^new\b",
        r"^implement\b"
    ],
    "Fixed": [
        r"^fix(\(.*\))?:",
        r"^bug(\(.*\))?:",
        r"^patch\b",
        r"^resolve\b",
        r"^close\b"
    ],
    "Changed": [
        r"^change(\(.*\))?:",
        r"^refactor(\(.*\))?:",
        r"^update\b",
        r"^perf(\(.*\))?:",
        r"^style(\(.*\))?:",
        r"^chore(\(.*\))?:",
        r"^build(\(.*\))?:",
        r"^ci(\(.*\))?:"
    ],
    "Removed": [
        r"^remove\b",
        r"^delete\b",
        r"^deprecate\b",
        r"^revert(\(.*\))?:"
    ]
}

def run_git(args):
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""
    except FileNotFoundError:
        print("Error: git command not found in PATH.", file=sys.stderr)
        sys.exit(1)

def get_latest_tag():
    return run_git(["describe", "--tags", "--abbrev=0"])

def get_commit_range(since_tag=None):
    if since_tag:
        return f"{since_tag}..HEAD"
    latest_tag = get_latest_tag()
    if latest_tag:
        return f"{latest_tag}..HEAD"
    return "HEAD"

def fetch_commits(commit_range):
    format_spec = "%H|%h|%an|%s"
    if ".." in commit_range:
        output = run_git(["log", f"--pretty=format:{format_spec}", commit_range])
    else:
        output = run_git(["log", f"--pretty=format:{format_spec}"])
    
    commits = []
    if not output:
        return commits
        
    for line in output.splitlines():
        parts = line.strip().split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "short_hash": parts[1],
                "author": parts[2],
                "subject": parts[3]
            })
    return commits

def categorize_commit(subject):
    clean_sub = subject.strip()
    
    # Check Conventional Commits prefix and semantic verbs
    for category, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, clean_sub, re.IGNORECASE):
                # Clean prefix for nicer changelog presentation if conventional commit
                cleaned = re.sub(r"^(feat|fix|bug|perf|refactor|style|chore|build|ci|docs|remove|deprecate|revert)(\([^\)]+\))?!?:?\s*", "", clean_sub, flags=re.IGNORECASE)
                # Capitalize first letter
                if cleaned:
                    cleaned = cleaned[0].upper() + cleaned[1:]
                else:
                    cleaned = clean_sub
                return category, cleaned
                
    return "Changed", clean_sub

def generate_markdown(commits, version="Unreleased", since_tag=None):
    grouped = defaultdict(list)
    for c in commits:
        category, cleaned_subject = categorize_commit(c["subject"])
        grouped[category].append(f"- {cleaned_subject} ([`{c['short_hash']}`]({c['short_hash']})) by @{c['author']}")

    today = datetime.now().strftime("%Y-%m-%d")
    header_version = f"## [{version}] - {today}"
    if since_tag:
        header_version += f" (since {since_tag})"

    lines = [
        header_version,
        ""
    ]

    order = ["Added", "Fixed", "Changed", "Removed"]
    has_entries = False

    for cat in order:
        entries = grouped.get(cat, [])
        if entries:
            has_entries = True
            lines.append(f"### {cat}")
            lines.extend(entries)
            lines.append("")

    if not has_entries:
        lines.append("- No user-facing changes recorded in this revision range.")
        lines.append("")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git history.")
    parser.add_argument("--since", help="Git tag or commit to start from (defaults to latest tag or repository start)")
    parser.add_argument("--version", default="Unreleased", help="Version name for the changelog header")
    parser.add_argument("--output", default="CHANGELOG.md", help="Filepath to write or prepend to")
    parser.add_argument("--stdout", action="store_true", help="Print changelog directly to stdout")
    args = parser.parse_args()

    commit_range = get_commit_range(args.since)
    since_tag = args.since or get_latest_tag()
    commits = fetch_commits(commit_range)

    if not commits:
        print(f"Notice: No commits found in range '{commit_range}'.")
        return

    content = generate_markdown(commits, version=args.version, since_tag=since_tag)

    if args.stdout:
        print(content)
        return

    # Check if existing CHANGELOG.md exists
    existing = ""
    try:
        with open(args.output, "r", encoding="utf-8") as f:
            existing = f.read()
    except FileNotFoundError:
        pass

    if existing:
        # Prepend after main title if present
        title_match = re.search(r"^(#\s+Changelog\s*\n+|#\s+.*\n+)", existing, re.IGNORECASE)
        if title_match:
            title_part = title_match.group(0)
            rest = existing[len(title_part):].lstrip()
            final_content = f"{title_part}\n{content}\n{rest}"
        else:
            final_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{content}\n{existing}"
    else:
        final_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n{content}"

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"Successfully generated and updated {args.output} ({len(commits)} commits processed).")

if __name__ == "__main__":
    main()
