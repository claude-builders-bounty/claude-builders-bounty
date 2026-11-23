#!/usr/bin/env python3
"""
Structured CHANGELOG.md Generator from Git History
Fetches commits since the latest git tag and auto-categorizes into:
Added, Fixed, Changed, Removed.
"""
import sys
import os
import subprocess
import re
from datetime import datetime

def run_cmd(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return result.stdout.strip()

def get_latest_tag():
    tag = run_cmd("git describe --tags --abbrev=0")
    return tag if tag else None

def get_commits_since_tag(tag=None):
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"
    log = run_cmd(f'git log {range_spec} --pretty=format:"%h%x09%s"')
    if not log:
        return []
    lines = log.splitlines()
    commits = []
    for line in lines:
        parts = line.split("\t", 1)
        if len(parts) == 2:
            commits.append({"hash": parts[0], "subject": parts[1]})
    return commits

def categorize_commits(commits):
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    patterns = {
        "Added": [r"^(feat|add|new|feature)\b", r"\badded?\b", r"\bimplement(ed)?\b"],
        "Fixed": [r"^(fix|bug|patch|resolve)\b", r"\bfixed?\b", r"\bresolv(e|ed)\b"],
        "Removed": [r"^(remove|delete|deprecate)\b", r"\bremoved?\b", r"\bdeleted?\b"],
        "Changed": [r"^(refactor|chore|perf|update|change|docs|style|test|build|ci)\b", r"\bupdated?\b", r"\bchanged?\b"]
    }

    for c in commits:
        sub = c["subject"]
        matched = False
        
        # Check Added
        for p in patterns["Added"]:
            if re.search(p, sub, re.IGNORECASE):
                categories["Added"].append(c)
                matched = True
                break
        if matched: continue

        # Check Fixed
        for p in patterns["Fixed"]:
            if re.search(p, sub, re.IGNORECASE):
                categories["Fixed"].append(c)
                matched = True
                break
        if matched: continue

        # Check Removed
        for p in patterns["Removed"]:
            if re.search(p, sub, re.IGNORECASE):
                categories["Removed"].append(c)
                matched = True
                break
        if matched: continue

        # Default to Changed
        categories["Changed"].append(c)

    return categories

def generate_markdown(categories, latest_tag=None, version_name="Unreleased"):
    today = datetime.now().strftime("%Y-%m-%d")
    md = [f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n"]
    header = f"## [{version_name}] - {today}"
    if latest_tag:
        header += f" (since {latest_tag})"
    md.append(header + "\n")

    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories[cat]
        if items:
            md.append(f"### {cat}\n")
            for it in items:
                md.append(f"- {it['subject']} (`{it['hash']}`)")
            md.append("")
    return "\n".join(md)

def main():
    tag = get_latest_tag()
    commits = get_commits_since_tag(tag)
    if not commits:
        print("No commits found to generate changelog.")
        sys.exit(0)

    cats = categorize_commits(commits)
    content = generate_markdown(cats, tag)

    out_file = "CHANGELOG.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated {out_file} successfully ({len(commits)} commits processed).")

if __name__ == "__main__":
    main()
