#!/usr/bin/env python3
"""
CHANGELOG Generator — Bounty #1
Generates structured CHANGELOG.md from git history since the latest tag.
Auto-categorizes commits into Added / Fixed / Changed / Removed.
"""
import subprocess, sys, re, os
from datetime import datetime

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def get_latest_tag():
    tags = run("git tag --sort=-creatordate").split("
")
    return tags[0] if tags and tags[0] else None

def get_commits_since(tag):
    if tag:
        return run(f'git log {tag}..HEAD --pretty=format:"%s|%h|%an|%ad" --date=short').split("
")
    return run('git log --pretty=format:"%s|%h|%an|%ad" --date=short').split("
")

CATEGORY_MAP = {
    "Added": ["feat", "add", "added", "implement", "create", "new", "introduce"],
    "Fixed": ["fix", "fixed", "bug", "resolve", "patch", "hotfix", "correct"],
    "Changed": ["change", "update", "refactor", "improve", "enhance", "modify", "tweak", "adjust", "rename", "move"],
    "Removed": ["remove", "delete", "drop", "deprecate", "obsolete", "cleanup"],
}

def categorize(commit_msg):
    msg_lower = commit_msg.lower()
    msg_parts = msg_lower.split(":")
    prefix = msg_parts[0].strip() if len(msg_parts) > 1 else ""
    
    # Conventional commits
    conventional = {"feat": "Added", "fix": "Fixed", "perf": "Changed", 
                    "refactor": "Changed", "style": "Changed", "docs": "Changed",
                    "test": "Changed", "chore": "Changed", "ci": "Changed",
                    "revert": "Removed", "remove": "Removed"}
    if prefix in conventional:
        return conventional[prefix]
    
    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in prefix or (kw in msg_lower and msg_lower.index(kw) < 30):
                return category
    return "Changed"

def generate_changelog(since_tag=None, output_file="CHANGELOG.md", stdout=False):
    tag = since_tag or get_latest_tag()
    commits = get_commits_since(tag)
    
    if not commits or commits == [""]:
        print("No commits found.")
        return
    
    categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for line in commits:
        if "|" not in line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        msg, sha, author, date = parts
        cat = categorize(msg)
        # Clean the message
        clean_msg = re.sub(r"^(feat|fix|chore|docs|style|refactor|perf|test|ci|revert|build)(\(.+\))?:\s*", "", msg, flags=re.IGNORECASE)
        categories[cat].append((clean_msg, sha[:7], author, date))
    
    today = datetime.now().strftime("%Y-%m-%d")
    tag_display = tag if tag else "initial"
    
    lines = [
        f"# Changelog",
        f"",
        f"## [{tag_display}] — {today}",
        f"",
    ]
    
    for category, entries in categories.items():
        if not entries:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for msg, sha, author, date in entries:
            lines.append(f"- {msg} ({sha}, {author}, {date})")
        lines.append("")
    
    output = "
".join(lines)
    
    if stdout:
        print(output)
    else:
        with open(output_file, "w") as f:
            f.write(output)
        print(f"CHANGELOG.md generated with {sum(len(v) for v in categories.values())} commits across {sum(1 for v in categories.values() if v)} categories.")
        print(f"  Added: {len(categories['Added'])} | Fixed: {len(categories['Fixed'])} | Changed: {len(categories['Changed'])} | Removed: {len(categories['Removed'])}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    p.add_argument("--since", help="Tag to start from (default: latest tag)")
    p.add_argument("--stdout", action="store_true", help="Print to stdout instead of file")
    p.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file")
    args = p.parse_args()
    generate_changelog(since_tag=args.since, output_file=args.output, stdout=args.stdout)
