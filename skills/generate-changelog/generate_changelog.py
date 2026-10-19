#!/usr/bin/env python3
"""
Automated Git History to CHANGELOG.md Generator for Claude Code
Parses commits since the last git tag, categorizes into Keep a Changelog sections,
and generates structured Markdown.
"""
import sys
import os
import re
import subprocess
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional

CATEGORY_MAP = {
    "feat": "Added",
    "add": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "patch": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "update": "Changed",
    "chore": "Changed",
    "docs": "Changed",
    "style": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "revert": "Changed",
    "deprecate": "Removed",
    "remove": "Removed",
    "delete": "Removed",
}

def get_git_tag_range() -> Tuple[Optional[str], str]:
    """
    Returns (latest_tag, revision_range)
    """
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        return tag, f"{tag}..HEAD"
    except Exception:
        return None, "HEAD"

def get_commits(rev_range: str) -> List[Dict[str, str]]:
    cmd = ["git", "log", rev_range, "--pretty=format:%h|%s|%an|%ad", "--date=short"]
    try:
        output = subprocess.check_output(cmd).decode("utf-8", errors="replace")
    except Exception as e:
        sys.stderr.write(f"Error reading git log: {e}\n")
        return []
    
    commits = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3]
            })
    return commits

def categorize_commit(subject: str) -> Tuple[str, str]:
    """
    Categorizes commit message based on Conventional Commits and keywords.
    Returns (category, clean_subject)
    """
    # 1. Match conventional commits: type(scope): message or type: message
    m = re.match(r"^([a-zA-Z]+)(?:\([^\)]+\))?!?:\s*(.+)$", subject)
    if m:
        ctype = m.group(1).lower()
        clean_msg = m.group(2).strip()
        cat = CATEGORY_MAP.get(ctype, "Changed")
        return cat, clean_msg

    # 2. Heuristic fallback based on initial words
    sub_lower = subject.lower()
    if any(sub_lower.startswith(w) for w in ["add", "added", "new", "implement", "support"]):
        return "Added", subject
    if any(sub_lower.startswith(w) for w in ["fix", "fixed", "resolve", "bug", "patch"]):
        return "Fixed", subject
    if any(sub_lower.startswith(w) for w in ["remove", "removed", "delete", "deprecate"]):
        return "Removed", subject

    return "Changed", subject

def build_changelog(version: str, commits: List[Dict[str, str]], base_tag: Optional[str] = None) -> str:
    sections: Dict[str, List[str]] = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Removed": []
    }

    for c in commits:
        cat, msg = categorize_commit(c["subject"])
        entry = f"- {msg} ([`{c['hash']}`](https://github.com/commits/{c['hash']})) - @{c['author']}"
        sections[cat].append(entry)

    today = datetime.now().strftime("%Y-%m-%d")
    header = f"## [{version}] - {today}"
    if base_tag:
        header += f" (Changes since `{base_tag}`)"
    
    lines = [header, ""]
    for cat_name in ["Added", "Changed", "Fixed", "Removed"]:
        items = sections[cat_name]
        if items:
            lines.append(f"### {cat_name}")
            lines.extend(items)
            lines.append("")

    return "\n".join(lines).strip()

def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("--version", "-v", default="Unreleased", help="Version header for this release (default: Unreleased)")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing to file")
    parser.add_argument("--all", action="store_true", help="Include all commits from project root instead of since last tag")
    args = parser.parse_args()

    latest_tag, rev_range = get_git_tag_range()
    if args.all or not latest_tag:
        rev_range = "HEAD"
        latest_tag = None

    commits = get_commits(rev_range)
    if not commits:
        sys.stderr.write("No new commits found.\n")
        sys.exit(0)

    changelog_section = build_changelog(args.version, commits, latest_tag)

    if args.stdout:
        print(changelog_section)
        return

    # Write or update CHANGELOG.md
    output_path = args.output
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        # Insert below top header if present
        if existing_content.startswith("# Changelog"):
            parts = existing_content.split("\n\n", 1)
            new_content = parts[0] + "\n\n" + changelog_section + "\n\n" + (parts[1] if len(parts) > 1 else "")
        else:
            new_content = "# Changelog\n\n" + changelog_section + "\n\n" + existing_content
    else:
        new_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\nThe format is based on [Keep a Changelog](https://keepachangelog.com/).\n\n{changelog_section}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Successfully wrote structured CHANGELOG to: {output_path} ({len(commits)} commits processed)")

if __name__ == "__main__":
    main()
