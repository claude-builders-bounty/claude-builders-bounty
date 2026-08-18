#!/usr/bin/env python3
"""
Git Changelog Generator for Claude Code
Generates a structured CHANGELOG.md from git history following Keep a Changelog standards.
"""

import os
import re
import subprocess
import sys
import argparse
from datetime import datetime
from collections import defaultdict

CATEGORY_MAPPING = {
    'Added': ['feat', 'feature', 'add', 'create', 'implement'],
    'Fixed': ['fix', 'bug', 'patch', 'resolve', 'hotfix'],
    'Changed': ['refactor', 'perf', 'change', 'update', 'modify', 'improve'],
    'Removed': ['remove', 'delete', 'deprecate', 'drop'],
    'Security': ['security', 'sec', 'cve', 'vuln'],
    'Documentation': ['docs', 'doc']
}

def run_git(cmd, cwd=None):
    """Run a git command and return stripped output."""
    try:
        res = subprocess.run(
            ['git'] + cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""

def get_latest_tag(cwd=None):
    """Get the most recent git tag or None."""
    tags = run_git(['tag', '--sort=-creatordate'], cwd=cwd)
    if tags:
        return tags.splitlines()[0]
    return None

def get_commits(since_tag=None, cwd=None):
    """Fetch commits with hash, author, date, and subject."""
    range_arg = f"{since_tag}..HEAD" if since_tag else "HEAD"
    fmt = "%H%x09%h%x09%an%x09%ad%x09%s"
    output = run_git(['log', range_arg, f'--pretty=format:{fmt}', '--date=short'], cwd=cwd)
    
    commits = []
    if not output:
        return commits

    for line in output.splitlines():
        parts = line.split('\t')
        if len(parts) >= 5:
            full_hash, short_hash, author, date, subject = parts[0], parts[1], parts[2], parts[3], parts[4]
            commits.append({
                'full_hash': full_hash,
                'short_hash': short_hash,
                'author': author,
                'date': date,
                'subject': subject
            })
    return commits

def categorize_commit(subject):
    """Categorize a commit message into Keep a Changelog categories."""
    sub_lower = subject.lower().strip()
    
    # Check conventional commits syntax: feat(scope): subject or fix: subject
    conv_match = re.match(r'^([a-zA-Z]+)(?:\([^\)]+\))?:\s*(.+)$', subject)
    prefix = conv_match.group(1).lower() if conv_match else None
    clean_msg = conv_match.group(2) if conv_match else subject

    if prefix:
        for cat, keywords in CATEGORY_MAPPING.items():
            if prefix in keywords:
                return cat, clean_msg

    # Fallback to keyword search
    for cat, keywords in CATEGORY_MAPPING.items():
        for kw in keywords:
            if re.search(rf'\b{kw}\b', sub_lower):
                return cat, subject

    return 'Changed', subject

def build_changelog(version="Unreleased", since_tag=None, cwd=None):
    """Build formatted Markdown changelog string."""
    commits = get_commits(since_tag, cwd=cwd)
    today = datetime.now().strftime("%Y-%m-%d")
    
    sections = defaultdict(list)
    for c in commits:
        cat, clean_msg = categorize_commit(c['subject'])
        sections[cat].append({
            'msg': clean_msg,
            'hash': c['short_hash'],
            'author': c['author']
        })

    order = ['Added', 'Fixed', 'Changed', 'Removed', 'Security', 'Documentation']
    
    lines = [
        f"## [{version}] - {today}",
        ""
    ]
    
    if since_tag:
        lines.append(f"> Changes since `{since_tag}` ({len(commits)} commits)")
        lines.append("")
    else:
        lines.append(f"> Initial changelog release ({len(commits)} commits)")
        lines.append("")

    if not commits:
        lines.append("_No commits found in this range._")
        lines.append("")
        return "\n".join(lines)

    for cat in order:
        if cat in sections and sections[cat]:
            lines.append(f"### {cat}")
            for item in sections[cat]:
                lines.append(f"- {item['msg']} (`{item['hash']}`) - @{item['author']}")
            lines.append("")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git history.")
    parser.add_argument("--version", default="Unreleased", help="Release version title (default: Unreleased)")
    parser.add_argument("--since", default=None, help="Git tag or commit to start from (default: auto-detect latest tag)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("--prepend", action="store_true", help="Prepend to existing CHANGELOG.md instead of overwriting")
    parser.add_argument("--stdout", action="store_true", help="Print changelog to stdout without writing file")
    args = parser.parse_args()

    since_tag = args.since or get_latest_tag()
    content = build_changelog(version=args.version, since_tag=since_tag)

    if args.stdout:
        print(content)
        return

    if args.prepend and os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            existing = f.read()
        full_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n{content}\n\n" + re.sub(r"^# Changelog[^\n]*\n+", "", existing)
    else:
        full_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n{content}"

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"✅ Generated changelog written to {args.output}")

if __name__ == "__main__":
    main()
