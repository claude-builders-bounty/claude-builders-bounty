#!/usr/bin/env python3
"""
generate_changelog.py — Generate a structured CHANGELOG.md from git history.

Usage:
    python generate_changelog.py              # since last tag
    python generate_changelog.py v1.2.0       # since specific tag
    python generate_changelog.py v1.2.0 v1.3.0  # between two tags
"""

import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path

CATEGORY_RULES = [
    ("Added",   [r"^feat", r"^add", r"^new", r"\badd\b", r"\bnew feature\b"]),
    ("Fixed",   [r"^fix", r"^bug", r"^hotfix", r"^patch", r"\bfix\b", r"\bbug\b"]),
    ("Changed", [r"^refactor", r"^perf", r"^update", r"^change", r"^improve",
                 r"^style", r"^chore", r"\bupdate\b", r"\bimprove\b", r"\brefactor\b"]),
    ("Removed", [r"^remove", r"^delete", r"^deprecate", r"\bremove\b", r"\bdelete\b"]),
]

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def get_last_tag():
    try:
        return run(["git", "describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None

def get_commits(since, until=None):
    fmt = "%H\x1F%s\x1F%an\x1F%ad"
    if since and until:
        range_spec = f"{since}..{until}"
    elif since:
        range_spec = f"{since}..HEAD"
    else:
        range_spec = "HEAD"
    try:
        output = run(["git", "log", range_spec, f"--format={fmt}", "--date=short"])
    except subprocess.CalledProcessError:
        return []
    if not output:
        return []
    commits = []
    for line in output.splitlines():
        parts = line.split("\x1F")
        if len(parts) == 4:
            sha, subject, author, date = parts
            commits.append({"sha": sha[:8], "subject": subject.strip(), "author": author.strip(), "date": date.strip()})
    return commits

def categorize(subject):
    lower = subject.lower()
    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, lower):
                return category
    return "Changed"

def format_entry(commit):
    subject = re.sub(r"^[a-z]+(\([^)]+\))?:\s*", "", commit["subject"], flags=re.IGNORECASE)
    subject = subject[0].upper() + subject[1:] if subject else commit["subject"]
    return f"- {subject} ([`{commit['sha']}`])"

def generate_changelog(since_tag, until_tag=None):
    commits = get_commits(since_tag, until_tag)
    if not commits:
        return "No commits found in the specified range.\n"
    buckets = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for commit in commits:
        buckets[categorize(commit["subject"])].append(format_entry(commit))
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"## [Unreleased] - {today}"
    if since_tag:
        header += f"\n\n> Changes since `{since_tag}`"
    lines = [header, ""]
    for section in ["Added", "Fixed", "Changed", "Removed"]:
        if buckets[section]:
            lines.append(f"### {section}")
            lines.extend(buckets[section])
            lines.append("")
    return "\n".join(lines)

def main():
    args = sys.argv[1:]
    since_tag = None
    until_tag = None
    if len(args) == 0:
        since_tag = get_last_tag()
    elif len(args) == 1:
        since_tag = args[0]
    elif len(args) == 2:
        since_tag, until_tag = args
    else:
        print("Usage: python generate_changelog.py [since-tag] [until-tag]")
        sys.exit(1)
    new_section = generate_changelog(since_tag, until_tag)
    output_path = Path("CHANGELOG.md")
    existing = ""
    if output_path.exists():
        content = output_path.read_text(encoding="utf-8")
        parts = re.split(r"\n(?=## )", content, maxsplit=1)
        if len(parts) > 1:
            existing = "\n" + parts[1]
    header = "# Changelog\n\nAll notable changes to this project will be documented here.\n\n"
    output_path.write_text(header + new_section + existing, encoding="utf-8")
    print(f"Done. CHANGELOG.md written.")

if __name__ == "__main__":
    main()
