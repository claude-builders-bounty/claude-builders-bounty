#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

import subprocess, sys, re, os
from datetime import datetime

def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()

def get_commits(from_tag, to_ref):
    if from_tag:
        return run(f"git log {from_tag}..{to_ref} --pretty=format:'%s'").split('\n')
    return run(f"git log {to_ref} --pretty=format:'%s'").split('\n')

def categorize(commits):
    cats = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}
    for c in commits:
        c = c.strip()
        if not c:
            continue
        if re.match(r'^feat', c, re.I):
            cats["Added"].append(c)
        elif re.match(r'^fix', c, re.I):
            cats["Fixed"].append(c)
        elif re.match(r'^(refactor|perf|style)', c, re.I):
            cats["Changed"].append(c)
        elif re.match(r'^(revert|remove)', c, re.I):
            cats["Removed"].append(c)
        else:
            cats["Other"].append(c)
    return cats

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    while not os.path.isdir(".git"):
        os.chdir("..")
        if os.path.dirname(os.getcwd()) == os.getcwd():
            print("Not a git repository", file=sys.stderr)
            sys.exit(1)
    
    tags = run("git tag --sort=-version:refname").split('\n')
    latest_tag = tags[0] if tags[0] else None
    prev_tag = tags[1] if len(tags) > 1 and tags[1] else None
    
    commits = get_commits(prev_tag, "HEAD" if not prev_tag else latest_tag)
    cats = categorize(commits)
    
    version = latest_tag or "Unreleased"
    date = datetime.now().strftime("%Y-%m-%d")
    
    lines = [f"# Changelog", f"", f"## [{version}] - {date}"]
    
    for label in ["Added", "Fixed", "Changed", "Removed"]:
        if cats[label]:
            lines.append(f"")
            lines.append(f"### {label}")
            for c in cats[label]:
                clean = re.sub(r'^(feat|fix|refactor|perf|style|revert|remove)\s*[:\(]?\s*', '', c, flags=re.I)
                lines.append(f"- {clean}")
    
    if cats["Other"]:
        lines.append(f"")
        lines.append(f"### Other")
        for c in cats["Other"]:
            lines.append(f"- {c}")
    
    changelog_path = "CHANGELOG.md"
    existing = ""
    if os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            existing = f.read()
    
    with open(changelog_path, "w") as f:
        f.write('\n'.join(lines) + '\n')
        if existing:
            f.write('\n' + existing)
    
    print(f"CHANGELOG.md generated ({len(commits)} commits)")

if __name__ == "__main__":
    main()
