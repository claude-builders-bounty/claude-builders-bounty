#!/usr/bin/env python3
"""
CHANGELOG Generator for Claude Code (SKILL.md + script)

Generates structured CHANGELOG.md from git history.
Usage: /generate-changelog [--since <tag>] [--output CHANGELOG.md]
       bash changelog.sh [--since <tag>] [--output CHANGELOG.md]
       python3 changelog.py [--since <tag>] [--output CHANGELOG.md]
"""

import subprocess, re, sys, os, argparse
from datetime import datetime
from pathlib import Path

def run_git(*args):
    result = subprocess.run(["git"] + list(args), capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"⚠️ Git error: {result.stderr.strip()}")
        return None
    return result.stdout.strip()

def get_tags():
    """Get all tags sorted by version"""
    tags = run_git("tag", "--sort=-v:refname")
    if not tags:
        return []
    return [t.strip() for t in tags.split("\n") if t.strip()]

def get_commits_since(since_ref=None):
    """Get commits since a git ref"""
    if since_ref:
        log = run_git("log", f"{since_ref}..HEAD", "--oneline", "--format=%H|%s")
    else:
        log = run_git("log", "HEAD", "--oneline", "--format=%H|%s", "--max-count=200")
    
    if not log:
        return []
    
    commits = []
    for line in log.split("\n"):
        if "|" in line:
            sha, msg = line.split("|", 1)
            commits.append({"sha": sha[:8], "message": msg})
    return commits

def categorize_commit(msg):
    """Categorize commit message into Added/Fixed/Changed/Removed."""
    msg_lower = msg.lower()
    
    # Patterns for Added
    if any(k in msg_lower for k in ["add", "new", "feat", "feature", "create", "introduce",
                                      "implement", "support", "allow", "enable"]):
        return "Added"
    # Patterns for Fixed
    if any(k in msg_lower for k in ["fix", "bug", "patch", "hotfix", "resolve", "correct",
                                      "repair", "workaround", "avoid crash"]):
        return "Fixed"
    # Patterns for Removed
    if any(k in msg_lower for k in ["remov", "delete", "drop", "deprecat", "unused", 
                                      "cleanup", "revert"]):
        return "Removed"
    # Patterns for Changed
    if any(k in msg_lower for k in ["change", "update", "refactor", "improve", "migrat",
                                      "bump", "upgrade", "downgrade", "modify", "rename",
                                      "replace", "rewrite", "simplify", "optimize"]):
        return "Changed"
    # Patterns for Documentation
    if any(k in msg_lower for k in ["doc", "readme", "comment", "typo", "license"]):
        return "Documentation"
    # Patterns for Security
    if any(k in msg_lower for k in ["security", "cve", "vulnerab", "xss", "csrf", "injection"]):
        return "Security"
    # Patterns for Performance
    if any(k in msg_lower for k in ["perf", "speed", "fast", "slow", "latency", "memory"]):
        return "Performance"
    
    return "Changed"  # default

def generate_changelog(since_tag=None, output_file="CHANGELOG.md"):
    """Generate structured CHANGELOG.md."""
    
    repo_name = run_git("remote", "get-url", "origin")
    if repo_name:
        # Extract org/repo from URL
        m = re.search(r'[:/]([^/]+/[^/.]+)', repo_name)
        if m:
            repo_name = m.group(1)
        else:
            repo_name = "this-repo"
    else:
        repo_name = "this-repo"
    
    # Get version info
    tags = get_tags()
    latest_tag = tags[0] if tags else None
    
    # Determine the range
    if since_tag:
        range_desc = f"since {since_tag}"
        commits = get_commits_since(since_tag)
    elif latest_tag:
        range_desc = f"{latest_tag} → HEAD"
        commits = get_commits_since(latest_tag)
    else:
        range_desc = "initial commits"
        commits = get_commits_since(None)
    
    if not commits:
        print("No commits found in the specified range.")
        return
    
    # Categorize
    categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": [],
                   "Documentation": [], "Security": [], "Performance": []}
    for c in commits:
        cat = categorize_commit(c["message"])
        if cat in categories:
            categories[cat].append(c)
    
    # Build changelog
    today = datetime.now().strftime("%Y-%m-%d")
    version = latest_tag or "0.1.0"
    
    lines = []
    lines.append(f"# Changelog")
    lines.append(f"")
    lines.append(f"## [{version}] — {today}")
    lines.append(f"")
    
    for cat_name, cat_commits in categories.items():
        if not cat_commits:
            continue
        icon = {"Added": "🚀", "Fixed": "🐛", "Changed": "🔄", "Removed": "🗑️",
                "Documentation": "📝", "Security": "🔒", "Performance": "⚡"}.get(cat_name, "•")
        lines.append(f"### {icon} {cat_name}")
        for c in cat_commits:
            # Clean up conventional commit prefixes
            msg = c["message"]
            for prefix in ["feat:", "fix:", "docs:", "chore:", "refactor:", "perf:",
                           "test:", "ci:", "build:", "style:", "revert:" ]:
                if msg.lower().startswith(prefix):
                    msg = msg[len(prefix):].strip()
                    break
            lines.append(f"- {c['sha']} {msg}")
        lines.append("")
    
    lines.append("---")
    lines.append(f"*Generated by [changelog-generator](https://github.com/{repo_name}) on {today}*")
    
    content = "\n".join(lines)
    
    # Write output
    output = Path(output_file)
    if output.exists():
        # Prepend to existing changelog
        existing = output.read_text(encoding="utf-8")
        # Keep the header, prepend new entries after it
        parts = existing.split("\n", 2)
        if len(parts) >= 2 and parts[0].startswith("#"):
            content = "\n".join(parts[:2]) + "\n\n" + content.split("\n\n", 1)[1] if "\n\n" in content else content
    else:
        output.write_text(content, encoding="utf-8")
        print(f"✅ Changelog written to {output_file} ({len(commits)} commits)")
    
    # Also print
    print(content)
    return content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--since", help="Git tag or ref to start from")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file")
    args = parser.parse_args()
    generate_changelog(args.since, args.output)
