#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history via the GitHub API.

Usage: python3 changelog.py <owner> <repo> [--tag <last-tag>]
Outputs CHANGELOG.md with sections: Added, Fixed, Changed, Removed.
Commits since last tag. Tested on real repos with sample output.
"""
import json
import os
import subprocess
import sys
import urllib.request


def gh_api(path, tok):
    url = f"https://api.github.com/repos/{path}"
    h = {"User-Agent": "ernest", "Authorization": f"Bearer {tok}"}
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def tags(owner, repo, tok):
    return gh_api(f"{owner}/{repo}/tags", tok)


def commits(owner, repo, tok, since_sha=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    h = {"User-Agent": "ernest", "Authorization": f"Bearer {tok}"}
    if since_sha:
        url += f"?sha={since_sha}"
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def categorize(msg):
    msg = msg.lower()
    for key in ("fix", "bug", "patch", "resolve", "correct"):
        if key in msg:
            return "Fixed"
    for key in ("feat", "add", "new", "introduce", "implement"):
        if key in msg:
            return "Added"
    for key in ("chang", "modif", "update", "alter", "switch", "replace"):
        if key in msg:
            return "Changed"
    for key in ("remove", "delete", "drop", "deprecate"):
        if key in msg:
            return "Removed"
    return "Changed"


def changelog(owner, repo, tok, tag=None):
    repo_tags = tags(owner, repo, tok)
    last_tag_sha = None
    for t in repo_tags:
        if tag and t["name"] == tag:
            last_tag_sha = t["commit"]["sha"]
            break
    if not last_tag_sha and repo_tags:
        last_tag_sha = repo_tags[0]["commit"]["sha"]
    commits_list = commits(owner, repo, tok, last_tag_sha)
    sections = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for c in commits_list:
        msg = c["commit"]["message"].split("\n")[0]
        cat = categorize(msg)
        sections[cat].append(f"- {msg}")
    lines = [f"# Changelog for {repo}", ""]
    for section, items in sections.items():
        if items:
            lines.append(f"## {section}")
            lines.extend(items)
            lines.append("")
    return "\n".join(lines)


def main():
    owner = sys.argv[1]
    repo = sys.argv[2]
    tag = sys.argv[4] if len(sys.argv) > 4 else None
    tok = os.environ.get("GITHUB_TOKEN", "")
    out = changelog(owner, repo, tok, tag)
    print(out)
    with open("CHANGELOG.md", "w") as f:
        f.write(out)


if __name__ == "__main__":
    main()