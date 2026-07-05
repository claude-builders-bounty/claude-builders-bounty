#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history"""
import subprocess, re, sys
from datetime import datetime
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd()).stdout.strip()

def get_last_tag():
    tag = run(["git", "describe", "--tags", "--abbrev=0", "--always"])
    return tag if tag and tag != "HEAD" else None

def get_commits(since=None):
    if since:
        result = run(["git", "log", f"{since}..HEAD", "--oneline", "--format=%H%n%s%n%b---"])
    else:
        result = run(["git", "log", "--oneline", "--format=%H%n%s%n%b---"])
    entries = []
    for block in result.split("\n---\n"):
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if len(lines) >= 2:
            entries.append({"hash": lines[0][:8], "subject": lines[1], "body": "\n".join(lines[2:]) if len(lines) > 2 else ""})
    return entries

def categorize(commits):
    cats = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}
    keywords = {
        "Added": ["add", "feat", "feature", "create", "implement", "new"],
        "Fixed": ["fix", "bug", "patch", "hotfix", "resolve", "correct"],
        "Changed": ["update", "change", "refactor", "improve", "upgrade", "migrate"],
        "Removed": ["remove", "delete", "drop", "deprecate"],
    }
    for c in commits:
        msg = (c["subject"] + " " + c["body"]).lower()
        assigned = False
        for cat, kws in keywords.items():
            if any(k in msg for k in kws):
                cats[cat].append(c)
                assigned = True
                break
        if not assigned:
            cats["Other"].append(c)
    return cats

def format_changelog(cats, version, date):
    lines = [f"# Changelog\n", f"## [{version}] - {date}\n"]
    for cat in ["Added", "Changed", "Fixed", "Removed", "Other"]:
        items = cats[cat]
        if items:
            lines.append(f"### {cat}\n")
            for c in items:
                body = f"\n  {c['body']}" if c['body'] else ""
                lines.append(f"- {c['subject']} ({c['hash']}){body}")
            lines.append("")
    return "\n".join(lines)

def main():
    repo_path = Path.cwd()
    if not (repo_path / ".git").exists():
        print("Error: Not a git repository", file=sys.stderr)
        sys.exit(1)
    
    last_tag = get_last_tag()
    commits = get_commits(last_tag)
    if not commits:
        print("No new commits found.")
        sys.exit(0)
    
    cats = categorize(commits)
    version = last_tag or "unreleased"
    date = datetime.now().strftime("%Y-%m-%d")
    changelog = format_changelog(cats, version, date)
    
    output_path = repo_path / "CHANGELOG.md"
    output_path.write_text(changelog)
    print(f"✅ CHANGELOG.md generated ({len(commits)} commits)")

if __name__ == "__main__":
    main()
