#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history since last tag."""
import subprocess, sys, os
from datetime import datetime

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip()

changelog = f"# Changelog\n\n## [{datetime.now().strftime('%Y-%m-%d')}]\n\n"

last_tag = run("git describe --tags --abbrev=0 2>/dev/null || echo ''")
if not last_tag:
    # Get initial commit if no tags
    last_tag = run("git rev-list --max-parents=0 HEAD")
    if last_tag:
        cli = "git log --oneline"
    else:
        cli = "git log --oneline --since='1 month ago'"
else:
    cli = f"git log {last_tag}..HEAD --oneline"

log = run(cli)
categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
commits = log.split('\n') if log else []
for c in commits:
    c = c.split(' ', 1)[-1] if ' ' in c else c
    if c.startswith("add") or c.startswith("feat") or c.startswith("feature"):
        categories["Added"].append(c)
    elif c.startswith("fix") or c.startswith("bugfix") or c.startswith("hotfix"):
        categories["Fixed"].append(c)
    elif c.startswith("change") or c.startswith("refactor"):
        categories["Changed"].append(c)
    elif c.startswith("remove") or c.startswith("delete") or c.startswith("deprecate"):
        categories["Removed"].append(c)
    else:
        categories["Changed"].append(c)

for cat, items in categories.items():
    if items:
        changelog += f"### {cat}\n\n"
        for i in items:
            changelog += f"- {i}\n"
        changelog += "\n"

with open("CHANGELOG.md", "w") as f:
    f.write(changelog)
print(f"Generated CHANGELOG.md with {sum(len(v) for v in categories.values())} entries")
