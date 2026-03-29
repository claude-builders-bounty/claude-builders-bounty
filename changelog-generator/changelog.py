#!/usr/bin/env python3
"""
changelog.py - Generate structured CHANGELOG from git history
Usage: python3 changelog.py [since_tag] [output_file]
"""

import subprocess
import re
from datetime import datetime
import sys

def get_last_tag():
    """Get the last git tag or fallback to HEAD~20."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "HEAD~20"

def get_commits_since(tag):
    """Fetch commits since the specified tag."""
    try:
        result = subprocess.run(
            ["git", "log", f"{tag}..HEAD", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True
        )
        return [c for c in result.stdout.strip().split("\n") if c.strip()]
    except subprocess.CalledProcessError:
        return []

def categorize_commit(message):
    """Categorize commit message by keywords."""
    msg = message.lower()
    
    # Check for conventional commit format first
    if msg.startswith("feat"):
        return "added"
    elif msg.startswith("fix"):
        return "fixed"
    elif msg.startswith("refactor") or msg.startswith("chore"):
        return "changed"
    elif msg.startswith("perf"):
        return "performance"
    elif msg.startswith("security"):
        return "security"
    
    # Keyword-based categorization
    if re.search(r'\b(feat|add|new)\b', msg):
        return "added"
    elif re.search(r'\b(fix|bug|patch|resolve)\b', msg):
        return "fixed"
    elif re.search(r'\b(change|update|modify|refactor|improve)\b', msg):
        return "changed"
    elif re.search(r'\b(remove|delete|deprecate)\b', msg):
        return "removed"
    elif re.search(r'\b(security|vuln|cve|exploit)\b', msg):
        return "security"
    elif re.search(r'\b(perf|optimize|speed|faster)\b', msg):
        return "performance"
    else:
        return "changed"  # default category

def generate_changelog(since=None, output="CHANGELOG.md"):
    """Generate CHANGELOG.md from git history."""
    if since is None:
        since = get_last_tag()
    
    print(f"📝 Fetching commits since {since}...")
    commits = get_commits_since(since)
    
    if not commits:
        print("⚠️  No commits found!")
        return
    
    categories = {
        "added": [],
        "changed": [],
        "fixed": [],
        "removed": [],
        "security": [],
        "performance": []
    }
    
    for commit in commits:
        cat = categorize_commit(commit)
        categories[cat].append(commit)
    
    # Write CHANGELOG
    with open(output, "w") as f:
        f.write("# CHANGELOG\n\n")
        f.write(f"## [Unreleased] - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        category_titles = [
            ("Added", "added"),
            ("Changed", "changed"),
            ("Fixed", "fixed"),
            ("Removed", "removed"),
            ("Security", "security"),
            ("Performance", "performance")
        ]
        
        for title, key in category_titles:
            items = sorted(set(categories[key]))
            if items:
                f.write(f"### {title}\n")
                for commit in items:
                    f.write(f"- {commit}\n")
                f.write("\n")
    
    print(f"✅ CHANGELOG generated: {output}")
    
    # Print summary
    total = sum(len(set(v)) for v in categories.values())
    print(f"\n📊 Summary:")
    print(f"   Total commits: {total}")
    for title, key in category_titles:
        count = len(set(categories[key]))
        if count > 0:
            print(f"   {title}: {count}")

if __name__ == "__main__":
    since = sys.argv[1] if len(sys.argv) > 1 else None
    output = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    
    try:
        generate_changelog(since, output)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
