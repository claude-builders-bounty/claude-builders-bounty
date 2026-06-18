#!/usr/bin/env python3
"""
generate_changelog.py
Auto-generate a structured CHANGELOG.md from git history
Bounty: $50 — Claude Builders Bounty #1
Usage: python3 generate_changelog.py [output_file] [repo_path]
"""

import subprocess
import sys
import os
import re
from datetime import datetime
from pathlib import Path


def run_git(cmd, cwd=None):
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_commits(cwd=None):
    """Get commits formatted as hash|message|author|date."""
    since = run_git(["describe", "--tags", "--abbrev=0"], cwd)
    
    if since:
        log_output = run_git(
            ["log", f"{since}..HEAD", "--pretty=format:%H|%s|%an|%ad", "--date=short"],
            cwd,
        )
        if log_output:
            return log_output.split("\n"), since
    
    # Fallback: all commits
    log_output = run_git(
        ["log", "--pretty=format:%H|%s|%an|%ad", "--date=short", "HEAD"],
        cwd,
    )
    if log_output:
        return log_output.split("\n"), since or "(beginning)"
    
    return [], ""


def categorize(message):
    """Categorize a commit message."""
    msg_lower = message.lower()
    
    # Conventional commits
    if re.match(r'^feat(\([^)]*\))?:', message):
        return "added"
    if re.match(r'^fix(\([^)]*\))?:', message):
        return "fixed"
    if re.match(r'^chore(\([^)]*\))?:|^refactor(\([^)]*\))?:|^perf(\([^)]*\))?:', message):
        return "changed"
    if re.match(r'^docs(\([^)]*\))?:', message):
        return "changed"
    if re.match(r'^style(\([^)]*\))?:', message):
        return "changed"
    if re.match(r'^revert(\([^)]*\))?:|^remove(\([^)]*\))?:', message):
        return "removed"
    
    # Semantic prefixes
    if re.match(r'^(feat|feature|add|new|implement|create|introduce)\b', msg_lower):
        return "added"
    if re.match(r'^(fix|bugfix|bug|hotfix|patch|resolve|correct)\b', msg_lower):
        return "fixed"
    if re.match(r'^(change|update|refactor|improve|modify|upgrade|migrate|redesign)\b', msg_lower):
        return "changed"
    if re.match(r'^(remove|delete|drop|deprecate|cleanup)\b', msg_lower):
        return "removed"
    
    return "other"


def format_entry(commit, cwd=None):
    """Format a single commit entry."""
    parts = commit.split("|", 3)
    if len(parts) < 2:
        return None, None
    
    msg = parts[1]
    short_hash = parts[0][:7]
    author = parts[2] if len(parts) > 2 else "unknown"
    date = parts[3] if len(parts) > 3 else ""
    
    # Clean up message
    msg_clean = msg.split(".")[0] + "."
    if len(msg_clean) > 100:
        msg_clean = msg_clean[:97] + "..."
    
    # Get repo URL for hyperlink
    repo_url = ""
    if cwd:
        remote = run_git(["remote", "get-url", "origin"], cwd)
        m = re.search(r'[:]([^:]+)\.git$', remote)
        if m:
            repo_url = f"https://github.com/{m.group(1)}"
    
    if repo_url:
        entry = f"- {msg_clean} ([{short_hash}]({repo_url}/commit/{parts[0]}))"
    else:
        entry = f"- {msg_clean} ({short_hash})"
    
    category = categorize(msg)
    return category, entry


def generate(output="CHANGELOG.md", repo_path="."):
    """Generate CHANGELOG.md."""
    cwd = os.path.abspath(repo_path) if repo_path else None
    
    # Verify git repo
    if not os.path.exists(os.path.join(cwd, ".git")) if cwd else False:
        if not run_git(["rev-parse", "--git-dir"], cwd):
            print("❌ Not in a git repository.")
            return False
    
    commits, since_ref = get_commits(cwd)
    
    if not commits:
        print("❌ No commits found.")
        return False
    
    print(f"🔍 Found {len(commits)} commit(s) since {since_ref}")
    
    # Categorize
    categories = {"added": [], "fixed": [], "changed": [], "removed": [], "other": []}
    
    for commit in commits:
        if not commit.strip():
            continue
        category, entry = format_entry(commit, cwd)
        if category and entry:
            categories[category].append(entry)
    
    # Get remote info
    remote_url = run_git(["remote", "get-url", "origin"], cwd)
    current_tag = run_git(["describe", "--tags", "--abbrev=0"], cwd) or "0.0.0"
    short_head = run_git(["rev-parse", "--short", "HEAD"], cwd)
    
    # Generate content
    lines = [
        "# Changelog",
        "",
        "## [Unreleased]",
        "",
        f"> Generated on {datetime.now().strftime('%Y-%m-%d')} from commit history.",
        "> Auto-categorized by [generate_changelog.py](generate_changelog.py)",
        "",
        "---",
        "",
        f"**Since:** `{since_ref}` → **Current:** `{short_head}`",
        f"**Latest tag:** `{current_tag}`",
        "",
    ]
    
    labels = [
        ("added", "✨ Added"),
        ("fixed", "🐛 Fixed"),
        ("changed", "🔄 Changed"),
        ("removed", "🗑️ Removed"),
        ("other", "📦 Other"),
    ]
    
    for key, label in labels:
        if categories[key]:
            lines.append(f"### {label}")
            lines.extend(categories[key])
            lines.append("")
    
    lines.extend([
        "---",
        "_Generated by [Claude Builders Bounty #1]"
        "(https://github.com/claude-builders-bounty/"
        "claude-builders-bounty/issues/1)_",
        "",
    ])
    
    content = "\n".join(lines)
    
    with open(output, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Summary
    counts = {k: len(v) for k, v in categories.items()}
    print(f"✅ CHANGELOG generated → {output}")
    print(f"\n📋 Summary:")
    print(f"   ✨ Added:    {counts['added']}")
    print(f"   🐛 Fixed:   {counts['fixed']}")
    print(f"   🔄 Changed: {counts['changed']}")
    print(f"   🗑️ Removed:  {counts['removed']}")
    print(f"   📦 Other:   {counts['other']}")
    
    return True


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
    repo = sys.argv[2] if len(sys.argv) > 2 else "."
    generate(output, repo)
