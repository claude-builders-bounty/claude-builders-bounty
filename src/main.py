#!/usr/bin/env python3
"""generate_changelog.py
Utility to generate a structured CHANGELOG from git history.

Features:
- Detects repository root.
- Finds the most recent tag (or uses the initial commit).
- Collects commits between the tag and HEAD.
- Parses conventional commit prefixes (feat, fix, docs, refactor, perf, test, chore).
- Groups entries by type and renders a markdown file.

Usage:
  python3 generate_changelog.py [--output CHANGELOG.md] [--template TEMPLATE.md]

Environment:
  OPTIONAL: CHangelog_TOKEN – token for future payment handling (not used here).
"""
import argparse
import os
import subprocess
import sys
from collections import defaultdict

def run_git(args, cwd=None):
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Git error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()

def get_repo_root():
    return run_git(["rev-parse", "--show-toplevel"])

def get_latest_tag():
    tags = run_git(["tag", "--sort=-creatordate"]).splitlines()
    return tags[0] if tags else None

def get_commits(since_tag=None):
    if since_tag:
        rev_range = f"{since_tag}..HEAD"
    else:
        rev_range = "HEAD"
    log = run_git(["log", rev_range, "--pretty=%H%x09%s"])
    commits = []
    for line in log.splitlines():
        sha, subject = line.split("\t", 1)
        commits.append((sha, subject))
    return commits

import re

def parse_commit(subject):
    """
    Parses conventional commit formats:
    - feat(scope): description
    - fix!: description
    - docs: description
    """
    pattern = r"^(\w+)(?:\(([^)]+)\))?(!?): (.+)$"
    match = re.match(pattern, subject.strip())
    if match:
        typ, scope, breaking, desc = match.groups()
        # If scope is present, we could optionally include it in desc or return separately
        return typ, desc
    return "misc", subject.strip()

def group_commits(commits):
    groups = defaultdict(list)
    for sha, subject in commits:
        typ, desc = parse_commit(subject)
        groups[typ].append((sha[:7], desc))
    return groups

def render(groups, version, date):
    lines = [f"## {version} – {date}\n"]
    order = ["feat", "fix", "docs", "refactor", "perf", "test", "chore", "misc"]
    for typ in order:
        if typ in groups:
            lines.append(f"### {typ}\n")
            for sha, desc in groups[typ]:
                lines.append(f"- {desc} ({sha})\n")
            lines.append("\n")
    return "".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG from git history")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file")
    parser.add_argument("--template", help="Optional markdown template with {entries} placeholder")
    args = parser.parse_args()

    root = get_repo_root()
    os.chdir(root)
    tag = get_latest_tag()
    version = tag if tag else "Unreleased"
    date = run_git(["show", "-s", "--format=%ad", "--date=short", "HEAD"])
    commits = get_commits(since_tag=tag)
    groups = group_commits(commits)
    entries_md = render(groups, version, date)

    if args.template and os.path.isfile(args.template):
        with open(args.template, "r", encoding="utf-8") as f:
            tmpl = f.read()
        content = tmpl.replace("{entries}", entries_md)
    else:
        content = "# Changelog\n\n" + entries_md

    with open(args.output, "w", encoding="utf-8") as out:
        out.write(content)
    print(f"CHANGELOG written to {args.output}")

if __name__ == "__main__":
    main()
