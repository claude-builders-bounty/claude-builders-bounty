#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

import subprocess
import sys
import re
from pathlib import Path

OUTPUT = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

last_tag = run(["git", "describe", "--tags", "--abbrev=0"])
if not last_tag:
    last_tag = run(["git", "rev-list", "--max-parents=0", "HEAD"])

log = run(["git", "log", f"{last_tag}..HEAD", "--pretty=format:%s"])

CATEGORIES = {
    "Added": r"^(add|feature|feat|new)",
    "Fixed": r"^(fix|bugfix|hotfix|patch)",
    "Changed": r"^(change|refactor|update|upgrade|bump|migrate)",
    "Removed": r"^(remove|delete|deprecate|drop)",
}

changelog = ["# Changelog", ""]

for section, pattern in CATEGORIES.items():
    matches = [l for l in log.split("\n") if re.search(pattern, l, re.IGNORECASE)]
    if matches:
        changelog.append(f"## {section}")
        for m in matches:
            changelog.append(f"- {m}")
        changelog.append("")

# Uncategorized
uncategorized = [l for l in log.split("\n") if not any(re.search(p, l, re.IGNORECASE) for p in CATEGORIES.values())]
if uncategorized:
    changelog.append("## Uncategorized")
    for m in uncategorized:
        changelog.append(f"- {m}")
    changelog.append("")

Path(OUTPUT).write_text("\n".join(changelog) + "\n")
print(f"Generated {OUTPUT} with {len(log.split(chr(10)))} commits")
