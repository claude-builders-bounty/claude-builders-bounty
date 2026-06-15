#!/usr/bin/env python3
"""changelog.py — Generate structured CHANGELOG.md from git history.
Usage: python changelog.py [--since TAG] [--output CHANGELOG.md]
"""
import subprocess, sys, os, re
from datetime import datetime

def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd(), timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except:
        return ""

# Parse args
since = None
output = "CHANGELOG.md"
args = sys.argv[1:]
for i, a in enumerate(args):
    if a == "--since" and i+1 < len(args):
        since = args[i+1]
    elif a == "--output" and i+1 < len(args):
        output = args[i+1]

# Get repo info
repo = os.path.basename(run(["git", "rev-parse", "--show-toplevel"]) or os.getcwd().split(os.sep)[-1])
if not since:
    since = run(["git", "describe", "--tags", "--abbrev=0"]) or run(["git", "rev-list", "--max-parents=0", "HEAD"])

# Get commits
commits_raw = run(["git", "log", f"{since}..HEAD", "--pretty=format:%s"])
commits = [c.strip() for c in commits_raw.split('\n') if c.strip()]

# Categorize
CATS = {
    "feat": "Added", "fix": "Fixed", "refactor": "Changed",
    "perf": "Changed", "revert": "Removed", "docs": "Changed",
    "style": "Changed", "test": "Changed", "chore": "Changed"
}
buckets = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
for c in commits:
    m = re.match(r'^(\w+)', c)
    cat = CATS.get(m.group(1), "Changed") if m else "Changed"
    buckets[cat].append(f"- {c}")

# Generate
tag = run(["git", "tag", "-l", "--sort=-creatordate"])
tag_name = tag.split('\n')[0] if tag else "Unreleased"
date = datetime.now().strftime("%Y-%m-%d")

lines = [
    f"# {repo} Changelog",
    "",
    f"## {tag_name} — {date}",
    ""
]
for section in ["Added", "Fixed", "Changed", "Removed"]:
    if buckets[section]:
        lines.append(f"### {section}")
        lines.extend(buckets[section])
        lines.append("")

open(output, "w").write("\n".join(lines))
print(f"Generated: {output} ({len(commits)} commits)")

# Print sample
for s in ["Added", "Fixed"]:
    if buckets[s]:
        print(f"\n{s}:")
        for item in buckets[s][:5]:
            print(f"  {item}")
