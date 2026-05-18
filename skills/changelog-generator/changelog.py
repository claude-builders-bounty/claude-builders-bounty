#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

import argparse
import subprocess
import sys
import re
from pathlib import Path


def run(cmd, required=True):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: git not found. Install git and try again.", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        if required:
            print(f"Error: `{' '.join(cmd)}` failed:\n{result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        return ""
    return result.stdout.strip()


def get_commit_range():
    head = run(["git", "rev-parse", "HEAD"])
    tag = run(["git", "describe", "--tags", "--abbrev=0"], required=False)
    if tag:
        tag_commit = run(["git", "rev-list", "-n", "1", tag])
        if tag_commit == head:
            siblings = run(["git", "tag", "--sort=-creatordate"])
            tags = [t for t in siblings.split("\n") if t.strip() and t != tag]
            tag = tags[0] if tags else ""
    if not tag:
        tag = run(["git", "rev-list", "--max-parents=0", "HEAD"])
    return tag


def categorize(line):
    patterns = {
        "Added": r"^(add|feature|feat|new)",
        "Fixed": r"^(fix|bugfix|hotfix|patch)",
        "Changed": r"^(change|refactor|update|upgrade|bump|migrate|chore)",
        "Removed": r"^(remove|delete|deprecate|drop)",
    }
    for section, pattern in patterns.items():
        if re.search(pattern, line, re.IGNORECASE):
            return section
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--limit", type=int, default=0, help="Max commits to include (0 = all)")
    args = parser.parse_args()

    since = get_commit_range()
    raw = run(["git", "log", f"{since}..HEAD", "--pretty=format:%s"])
    lines = [l for l in raw.split("\n") if l.strip()]
    if args.limit > 0:
        lines = lines[:args.limit]

    changelog = ["# Changelog", ""]

    if not lines:
        changelog.append(f"No new commits since {since[:8]}.")
        changelog.append("")
    else:
        buckets = {}
        for line in lines:
            cat = categorize(line)
            buckets.setdefault(cat or "Uncategorized", []).append(line)

        for section in ["Added", "Fixed", "Changed", "Removed", "Uncategorized"]:
            items = buckets.get(section)
            if items:
                changelog.append(f"## {section}")
                for item in items:
                    changelog.append(f"- {item}")
                changelog.append("")

    Path(args.output).write_text("\n".join(changelog) + "\n")
    print(f"Generated {args.output} ({len(lines)} commits since {since[:8]})")


if __name__ == "__main__":
    main()
