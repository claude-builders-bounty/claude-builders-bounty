#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

import subprocess
import sys
import re
from pathlib import Path

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"


def run(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: git not found. Make sure git is installed.", file=sys.stderr)
        sys.exit(1)


def get_commit_range():
    head = run(["git", "rev-parse", "HEAD"])
    tag = run(["git", "describe", "--tags", "--abbrev=0"])
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


since = get_commit_range()
raw = run(["git", "log", f"{since}..HEAD", "--pretty=format:%s"])
lines = [l for l in raw.split("\n") if l.strip()]

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

Path(OUTPUT).write_text("\n".join(changelog) + "\n")
print(f"Generated {OUTPUT} ({len(lines)} commits since {since[:8]})")
