#!/usr/bin/env python3
"""
Automated Git Changelog Generator
Generates structured Keep-a-Changelog format markdown from git commit history.
"""

import subprocess
import argparse
import re
import os
import sys
from datetime import datetime
from collections import defaultdict

def run_git(cmd):
    """Run a git command and return stripped stdout string."""
    try:
        res = subprocess.run(
            ["git"] + cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def get_latest_tag():
    """Retrieve the most recent tag in repository."""
    tag = run_git(["describe", "--tags", "--abbrev=0"])
    if not tag:
        # Fallback to latest tag in tag list if describe fails
        tags = run_git(["tag", "--sort=-creatordate"]).splitlines()
        if tags:
            tag = tags[0].strip()
    return tag

def get_commit_range(since_ref=None):
    """Determine the git revision range."""
    if since_ref:
        return f"{since_ref}..HEAD"
    latest_tag = get_latest_tag()
    if latest_tag:
        return f"{latest_tag}..HEAD", latest_tag
    return "HEAD", None

def get_commits(rev_range):
    """Fetch structured commit logs within revision range."""
    raw_log = run_git(["log", rev_range, "--pretty=format:%H|%h|%an|%s"])
    if not raw_log:
        return []
    
    commits = []
    for line in raw_log.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "full_hash": parts[0],
                "short_hash": parts[1],
                "author": parts[2],
                "subject": parts[3].strip()
            })
    return commits

def categorize_commit(subject):
    """
    Categorize commit message into: Added / Fixed / Changed / Removed
    based on Conventional Commits standards.
    """
    sub_lower = subject.lower()
    
    # Conventional commit prefixes like feat:, feat(scope):, etc.
    if re.match(r'^(feat|feature|add)(\(.*?\))?!?:', sub_lower):
        return "Added"
    if re.match(r'^(fix|bugfix|hotfix|patch)(\(.*?\))?!?:', sub_lower):
        return "Fixed"
    if re.match(r'^(remove|deprecate|delete)(\(.*?\))?!?:', sub_lower):
        return "Removed"
    if re.match(r'^(chore|refactor|perf|docs|style|test|build|ci|change|update)(\(.*?\))?!?:', sub_lower):
        return "Changed"

    # Keyword based classification fallback
    if any(k in sub_lower for k in ["add ", "added ", "introduce ", "implement "]):
        return "Added"
    if any(k in sub_lower for k in ["fix ", "fixed ", "bug ", "resolve "]):
        return "Fixed"
    if any(k in sub_lower for k in ["remove ", "removed ", "delete ", "deprecated "]):
        return "Removed"

    return "Changed"

def clean_commit_message(subject):
    """Strip standard conventional commit prefixes for cleaner bullet points."""
    cleaned = re.sub(r'^(feat|feature|fix|bugfix|chore|refactor|perf|docs|style|test|build|ci|add|remove|update)(\(.*?\))?!?:?\s*', '', subject, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned or subject

def generate_markdown(commits, version="Unreleased", baseline_tag=None):
    """Build formatted Markdown string for changelog entry."""
    categorized = defaultdict(list)
    for c in commits:
        category = categorize_commit(c["subject"])
        msg = clean_commit_message(c["subject"])
        author_str = f"by @{c['author']}" if c['author'] else ""
        categorized[category].append(f"- {msg} ([`{c['short_hash']}`]) {author_str}".strip())

    date_str = datetime.now().strftime("%Y-%m-%d")
    lines = [f"## [{version}] - {date_str}"]
    if baseline_tag:
        lines.append(f"> Changes since tag `{baseline_tag}`\n")
    else:
        lines.append("> Changes from repository root\n")

    section_order = ["Added", "Changed", "Fixed", "Removed"]
    for section in section_order:
        items = categorized.get(section, [])
        if items:
            lines.append(f"### {section}")
            lines.extend(items)
            lines.append("")

    return "\n".join(lines).strip() + "\n"

def update_changelog_file(file_path, new_entry):
    """Update or create CHANGELOG.md file, inserting new release block."""
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"
    
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(header + new_entry)
        return

    with open(file_path, "r", encoding="utf-8") as f:
        existing = f.read()

    # Prepend new entry under main header if present
    if "# Changelog" in existing:
        parts = existing.split("# Changelog", 1)
        sub_parts = parts[1].split("\n\n## ", 1)
        if len(sub_parts) == 2:
            new_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{new_entry}\n\n## {sub_parts[1]}"
        else:
            new_content = f"{existing.rstrip()}\n\n{new_entry}"
    else:
        new_content = f"{header}{new_entry}\n\n{existing}"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("--since", help="Git reference (tag/branch/commit) to start log from. Defaults to latest tag.")
    parser.add_argument("--version", default="Unreleased", help="Version header name (default: Unreleased).")
    parser.add_argument("--output", default="CHANGELOG.md", help="Destination file path (default: CHANGELOG.md).")
    parser.add_argument("--dry-run", action="store_true", help="Print output to stdout without writing to file.")
    args = parser.parse_args()

    if args.since:
        rev_range = f"{args.since}..HEAD"
        baseline_tag = args.since
    else:
        baseline_tag = get_latest_tag()
        rev_range = f"{baseline_tag}..HEAD" if baseline_tag else "HEAD"

    commits = get_commits(rev_range)
    if not commits:
        print(f"[!] No new commits found for range: {rev_range}")
        sys.exit(0)

    markdown = generate_markdown(commits, version=args.version, baseline_tag=baseline_tag)

    if args.dry_run:
        print(markdown)
    else:
        update_changelog_file(args.output, markdown)
        print(f"✓ Changelog successfully written to {args.output} ({len(commits)} commits processed).")

if __name__ == "__main__":
    main()
