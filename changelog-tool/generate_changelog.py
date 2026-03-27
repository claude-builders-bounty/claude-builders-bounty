#!/usr/bin/env python3
"""Auto-generate structured CHANGELOG.md from git history since last tag."""
import subprocess, re, sys, os
from datetime import datetime

def run(cmd):
    return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()

def get_last_tag():
    tags = run("git tag --sort=-creatordate").split("\n")
    return tags[0] if tags and tags[0] else None

def get_commits(since_ref):
    if since_ref:
        log = run(f'git log {since_ref}..HEAD --pretty=format:"%s||%h||%an||%ad" --date=short')
    else:
        log = run('git log --pretty=format:"%s||%h||%an||%ad" --date=short')
    commits = []
    for line in log.split("\n"):
        if "||" in line:
            parts = line.split("||")
            commits.append({"msg": parts[0], "hash": parts[1], "author": parts[2], "date": parts[3]})
    return commits

def categorize(msg):
    m = msg.lower()
    prefixes = [
        ("feat", "Added"), ("add", "Added"), ("new", "Added"), ("implement", "Added"), ("create", "Added"),
        ("fix", "Fixed"), ("bug", "Fixed"), ("patch", "Fixed"), ("resolve", "Fixed"), ("repair", "Fixed"),
        ("change", "Changed"), ("update", "Changed"), ("improve", "Changed"), ("refactor", "Changed"), ("rename", "Changed"),
        ("remove", "Removed"), ("delete", "Removed"), ("drop", "Removed"), ("deprecate", "Removed"),
    ]
    for kw, cat in prefixes:
        if kw in m:
            return cat
    return "Changed"

def generate():
    last_tag = get_last_tag()
    commits = get_commits(last_tag)
    if not commits:
        print("No new commits since last tag.")
        return

    categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for c in commits:
        cat = categorize(c["msg"])
        categories[cat].append(c)

    today = datetime.now().strftime("%Y-%m-%d")
    tag_range = f"{last_tag}...HEAD" if last_tag else "HEAD"
    md = f"# Changelog\n\n## [{today}] {tag_range}\n\n"

    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        if categories[cat]:
            md += f"### {cat}\n\n"
            for c in categories[cat]:
                md += f"- {c['msg']} ({c['hash']})\n"
            md += "\n"

    # Prepend to existing or create new
    changelog = "CHANGELOG.md"
    if os.path.exists(changelog):
        with open(changelog) as f:
            existing = f.read()
        md += "\n" + existing
    with open(changelog, "w") as f:
        f.write(md)
    print(f"✅ CHANGELOG.md generated ({len(commits)} commits)")

if __name__ == "__main__":
    generate()
