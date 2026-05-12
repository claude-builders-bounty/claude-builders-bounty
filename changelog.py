#!/usr/bin/env python3
"""changelog.py — Generate a structured CHANGELOG.md from git history.
   Bounty: $50 — claude-builders-bounty/claude-builders-bounty#1"""

import subprocess, sys, re, os
from pathlib import Path

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
REPO = Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()

CATEGORIES = {
    "Added":   r"^(add|feat|feature|new|introduce|implement)\b",
    "Fixed":   r"^(fix|bug|patch|resolve|repair|correct|hotfix)\b",
    "Changed": r"^(change|update|refactor|modify|adjust|tweak|improve|enhance|upgrade|migrate|rework|revise|tune|optimize|clean)\b",
    "Removed": r"^(remove|drop|delete|deprecate|retire)\b",
}

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO).stdout.strip()

# Get latest tag baseline. If no tag exists, include the full history.
tag = run(["git", "describe", "--tags", "--abbrev=0"])
if tag:
    rev_args = [f"{tag}..HEAD"]
else:
    head = run(["git", "rev-parse", "--verify", "HEAD"])
    if not head:
        print("Error: No commits found.", file=sys.stderr)
        sys.exit(1)
    print("No tags found. Including all commits.")
    rev_args = []

# Collect commits
commits = run(["git", "log", *rev_args, "--pretty=format:%s", "--no-merges"])
buckets = {k: [] for k in CATEGORIES}

for line in commits.split("\n"):
    msg = line.strip()
    if not msg:
        continue
    lower = msg.lower()
    placed = False
    for cat, pattern in CATEGORIES.items():
        if re.search(pattern, lower):
            buckets[cat].append(msg)
            placed = True
            break
    if not placed:
        # Keep output within the requested four categories.
        buckets["Changed"].append(msg)

# Write output
output_path = Path(OUTPUT)
if not output_path.is_absolute():
    output_path = REPO / output_path

with open(output_path, "w") as f:
    f.write("# Changelog\n\n## [Unreleased]\n\n")
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        entries = buckets[cat]
        if entries:
            f.write(f"### {cat}\n\n")
            for e in entries:
                f.write(f"- {e}\n")
            f.write("\n")
            print(f"  ✓ {cat}: {len(entries)} entries")

print(f"\n✅ CHANGELOG written to {output_path}")
