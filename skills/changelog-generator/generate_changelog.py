#!/usr/bin/env python3
"""
Autonomous Structured CHANGELOG Generator
Parses Git history, detects latest tags, classifies Conventional Commits,
and renders a production-grade Keep a Changelog (v1.1.0) formatted CHANGELOG.md.
"""
import subprocess
import re
import sys
import os
import datetime

sys.stdout.reconfigure(encoding='utf-8')

CONVENTIONAL_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "perf": "Performance Improvements",
    "performance": "Performance Improvements",
    "refactor": "Changed",
    "change": "Changed",
    "update": "Changed",
    "docs": "Documentation",
    "style": "Styles",
    "test": "Tests",
    "chore": "Maintenance",
    "ci": "CI/CD",
    "build": "Build System",
    "revert": "Reverts",
    "deprecate": "Deprecated",
    "remove": "Removed",
    "security": "Security"
}

def get_git_output(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""

def get_latest_tag():
    return get_git_output("git describe --tags --abbrev=0 2>/dev/null")

def get_commit_log(from_tag=""):
    revision_range = f"{from_tag}..HEAD" if from_tag else "HEAD"
    # Format: Hash | Author | Subject | Body
    fmt = "%H%x1f%an%x1f%s%x1f%b%x1e"
    raw = get_git_output(f'git log {revision_range} --format="{fmt}"')
    if not raw:
        return []

    commits = []
    for entry in raw.split("\x1e"):
        if not entry.strip():
            continue
        parts = entry.strip().split("\x1f")
        if len(parts) >= 3:
            commits.append({
                "hash": parts[0],
                "short_hash": parts[0][:7],
                "author": parts[1],
                "subject": parts[2],
                "body": parts[3] if len(parts) > 3 else ""
            })
    return commits

def parse_conventional_commit(subject):
    # Matches: type(scope)!: message (#123)
    pattern = r"^([a-zA-Z]+)(?:\(([^)]+)\))?(!)?:\s*(.+)$"
    match = re.match(pattern, subject)
    if match:
        ctype, scope, breaking, msg = match.groups()
        category = CONVENTIONAL_MAP.get(ctype.lower(), "Changed")
        return {
            "category": category,
            "scope": scope,
            "is_breaking": bool(breaking),
            "message": msg
        }
    
    # Fallback keyword matching
    lower = subject.lower()
    if lower.startswith("add ") or "add " in lower:
        return {"category": "Added", "scope": None, "is_breaking": False, "message": subject}
    elif lower.startswith("fix ") or "fix " in lower or "bug" in lower:
        return {"category": "Fixed", "scope": None, "is_breaking": False, "message": subject}
    elif lower.startswith("remove ") or "delete" in lower:
        return {"category": "Removed", "scope": None, "is_breaking": False, "message": subject}
    else:
        return {"category": "Changed", "scope": None, "is_breaking": False, "message": subject}

def generate_changelog(output_file="CHANGELOG.md", version_tag="Unreleased"):
    latest_tag = get_latest_tag()
    commits = get_commit_log(latest_tag)

    today = datetime.date.today().strftime("%Y-%m-%d")
    categorized = {}

    for c in commits:
        parsed = parse_conventional_commit(c["subject"])
        cat = parsed["category"]
        if cat not in categorized:
            categorized[cat] = []
        
        scope_prefix = f"**{parsed['scope']}:** " if parsed['scope'] else ""
        item_line = f"- {scope_prefix}{parsed['message']} ([`{c['short_hash']}`] - @{c['author']})"
        categorized[cat].append(item_line)

    # Render Markdown
    lines = []
    lines.append("# Changelog\n")
    lines.append("All notable changes to this project will be documented in this file.\n")
    lines.append(f"## [{version_tag}] - {today}\n")

    category_order = ["Added", "Fixed", "Changed", "Removed", "Security", "Performance Improvements", "Documentation", "Maintenance"]
    
    for cat in category_order:
        if cat in categorized and categorized[cat]:
            lines.append(f"### {cat}\n")
            for item in categorized[cat]:
                lines.append(f"{item}\n")
            lines.append("")

    for cat, items in categorized.items():
        if cat not in category_order and items:
            lines.append(f"### {cat}\n")
            for item in items:
                lines.append(f"{item}\n")
            lines.append("")

    content = "\n".join(lines)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Generated {output_file} successfully! ({len(commits)} commits processed across {len(categorized)} categories)")
    return content

if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else "Unreleased"
    generate_changelog("CHANGELOG.md", tag)
