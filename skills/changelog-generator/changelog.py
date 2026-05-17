#!/usr/bin/env python3
"""
changelog.py — Generate structured CHANGELOG.md from git history.
Usage: python3 changelog.py [--since TAG] [--output FILE]
"""

import subprocess, sys, re, os
from datetime import datetime
from collections import defaultdict

def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()

def get_last_tag():
    """Get the most recent git tag."""
    try:
        return run("git describe --tags --abbrev=0 2>/dev/null") or None
    except:
        return None

def get_commits_since(tag):
    """Get all commits since a given tag."""
    if tag:
        # Check if tag exists in history; if not, get all commits
        result = run(f'git merge-base --is-ancestor {tag} HEAD 2>/dev/null && echo yes || echo no')
        if result == 'yes':
            log = run(f'git log {tag}..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short')
            if not log:
                log = run(f'git log --pretty=format:"%h|%s|%an|%ad" --date=short -n 50')
        else:
            log = run(f'git log --pretty=format:"%h|%s|%an|%ad" --date=short -n 50')
    else:
        log = run('git log --pretty=format:"%h|%s|%an|%ad" --date=short -n 50')
    return log.split('\n') if log else []

def categorize(message):
    """Auto-categorize a commit message."""
    msg_lower = message.lower()
    
    # Conventional commits
    if re.match(r'^(feat|add|new|implement)', msg_lower):
        return 'Added'
    if re.match(r'^(fix|bug|hotfix|patch|resolve)', msg_lower):
        return 'Fixed'
    if re.match(r'^(refactor|change|update|modify|improve|enhance|tweak|adjust)', msg_lower):
        return 'Changed'
    if re.match(r'^(remove|delete|drop|deprecate|revert)', msg_lower):
        return 'Removed'
    if re.match(r'^(docs|doc|readme)', msg_lower):
        return 'Documentation'
    if re.match(r'^(test|tests|spec)', msg_lower):
        return 'Tests'
    if re.match(r'^(chore|ci|build|deps|release|version|bump)', msg_lower):
        return 'Chores'
    
    # Keyword fallback
    if any(w in msg_lower for w in ['add', 'new', 'introduce', 'create']):
        return 'Added'
    if any(w in msg_lower for w in ['fix', 'bug', 'patch', 'resolve', 'crash', 'error', 'broken']):
        return 'Fixed'
    if any(w in msg_lower for w in ['remove', 'delete', 'drop', 'deprecated']):
        return 'Removed'
    
    return 'Changed'

def generate_changelog(since_tag=None, output_file="CHANGELOG.md"):
    """Generate changelog and write to file."""
    tag = since_tag or get_last_tag()
    commits = get_commits_since(tag)
    
    if not commits:
        print("No commits found.")
        return
    
    # Parse and categorize
    groups = defaultdict(list)
    for line in commits:
        parts = line.split('|', 3)
        if len(parts) < 4:
            continue
        sha, message, author, date = parts
        category = categorize(message)
        groups[category].append((sha, message, author, date))
    
    # Read existing changelog if any
    existing = ""
    if os.path.exists(output_file):
        with open(output_file) as f:
            existing = f.read()
    
    # Build new entry
    today = datetime.now().strftime("%Y-%m-%d")
    version = f"## [{today}]"
    if tag:
        version = f"## [{today}] — since {tag}"
    
    # Category order
    order = ['Added', 'Fixed', 'Changed', 'Removed', 'Documentation', 'Tests', 'Chores']
    
    lines = []
    lines.append(version)
    lines.append("")
    
    has_content = False
    for cat in order:
        if cat not in groups:
            continue
        has_content = True
        lines.append(f"### {cat}")
        lines.append("")
        for sha, msg, author, date in groups[cat]:
            # Clean up message
            clean_msg = re.sub(r'^(feat|fix|chore|docs|refactor|test|style|build|ci|perf|revert)(\(.*?\))?:\s*', '', msg)
            lines.append(f"- {clean_msg} ({sha}, {author})")
        lines.append("")
    
    if not has_content:
        print("No categorizable commits found since last tag.")
        return
    
    # Write output
    full = "\n".join(lines)
    if existing:
        # Insert after the first ## header
        header_match = re.search(r'^##\s', existing, re.MULTILINE)
        if header_match:
            pos = header_match.start()
            full = existing[:pos] + full + "\n" + existing[pos:]
        else:
            full = full + "\n" + existing
    else:
        full = "# Changelog\n\n" + full
    
    with open(output_file, 'w') as f:
        f.write(full + "\n")
    
    print(f"✅ CHANGELOG.md generated ({len(commits)} commits, {sum(len(v) for v in groups.values())} categorized)")
    for cat in order:
        if cat in groups:
            print(f"   {cat}: {len(groups[cat])} commits")
    print(f"   → {output_file}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git history")
    p.add_argument("--since", help="Tag or commit to start from (default: last tag)")
    p.add_argument("--output", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    args = p.parse_args()
    
    if not os.path.exists(".git"):
        print("❌ Error: Not in a git repository.")
        sys.exit(1)
    
    generate_changelog(since_tag=args.since, output_file=args.output)
