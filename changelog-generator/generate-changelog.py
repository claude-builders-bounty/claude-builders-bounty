#!/usr/bin/env python3
"""
generate-changelog.py — Generates a structured CHANGELOG.md from git history.
Usage: ./generate-changelog.py [--since <tag>] [--output <file>] [--repo <path>]
"""

import argparse, os, re, subprocess, sys
from datetime import date
from pathlib import Path


def run_git(args, cwd=None):
    result = subprocess.run(["git"]+args, capture_output=True, text=True, cwd=cwd or os.getcwd())
    if result.returncode != 0:
        print(f"git error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def get_last_tag(repo=None):
    tags = run_git(["tag", "--sort=-creatordate"], repo)
    lines = [t for t in tags.strip().split("\n") if t]
    return lines[0] if lines else None


def get_commits(since, repo=None):
    spec = f"{since}..HEAD" if since else "HEAD"
    fmt = "%H|%h|%s|%an|%ad"
    out = run_git(["log", spec, f"--format={fmt}", "--date=short"], repo)
    commits = []
    for line in out.strip().split("\n"):
        if not line: continue
        parts = line.split("|", 4)
        if len(parts) >= 4:
            commits.append({"hash": parts[0], "short_hash": parts[1], "message": parts[2], "author": parts[3], "date": parts[4] if len(parts)>4 else ""})
    return commits


def categorize(msg):
    m = msg.lower()
    if re.search(r'^(feat|add|introduce|implement|create|new)\b', m): return "Added"
    if re.search(r'^(fix|bug|hotfix|resolve|patch|correct)\b', m): return "Fixed"
    if re.search(r'^(change|update|modify|refactor|improve|enhance|optimize)\b', m): return "Changed"
    if re.search(r'^(remove|delete|drop|deprecate|revert|undo)\b', m): return "Removed"
    if any(k in m for k in ["add","added","introduce","implement","new","feature","support for"]): return "Added"
    if any(k in m for k in ["fix","fixed","bug","resolve","patch","correct","error","crash","broken"]): return "Fixed"
    if any(k in m for k in ["update","updated","change","changed","refactor","improve","optimize","upgrade","enhance"]): return "Changed"
    if any(k in m for k in ["remove","removed","delete","deleted","drop","revert","deprecate","clean up","cleanup"]): return "Removed"
    return "Changed"


def parse_merge(msg):
    m = re.search(r'#(\d+)', msg)
    pr = m.group(1) if m else None
    clean = re.sub(r'^Merge.*?from\s+\S+\s*-*\s*', '', msg).strip() or msg
    return pr, clean


def group_commits(commits):
    cats = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}
    for c in commits:
        if c["message"].startswith(("Merge branch","Merge pull request")):
            pr, clean = parse_merge(c["message"])
            if clean and clean != c["message"]:
                c["message"] = clean; c["pr_number"] = pr
            else:
                continue
        cats[categorize(c["message"])].append(c)
    return {k:v for k,v in cats.items() if v}


def generate(cats, tag, version=None, url=None):
    today = date.today().isoformat()
    header = f"## [{'Unreleased' if not version else version}] - {today}"
    lines = [
        "# Changelog","",
        "All notable changes to this project will be documented in this file.", "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).","",
        header, ""
    ]
    for cat in ["Added","Fixed","Changed","Removed","Other"]:
        if cat not in cats: continue
        lines.append(f"### {cat}"); lines.append("")
        for c in cats[cat]:
            msg = c["message"]
            if c.get("pr_number") and url:
                msg = f"{msg} ([#{c['pr_number']}]({url}/pull/{c['pr_number']}))"
            lines.append(f"- {msg}")
        lines.append("")
    if tag and url:
        lines.append(f"[Unreleased]: {url}/compare/{tag}...HEAD"); lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    p.add_argument("--since","-s", help="Start tag (default: last git tag)")
    p.add_argument("--output","-o", default="CHANGELOG.md", help="Output file")
    p.add_argument("--repo","-r", default=".", help="Git repo path")
    p.add_argument("--url","-u", help="GitHub URL for PR linking")
    p.add_argument("--version","-v", help="Version for header (default: Unreleased)")
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"Not a git repo: {repo}", file=sys.stderr); sys.exit(1)

    since = args.since or get_last_tag(repo)
    print(f"Scanning since: {since or 'start of history'}")
    commits = get_commits(since, repo)
    print(f"Found {len(commits)} commits")
    if not commits:
        print("No commits found."); return

    cats = group_commits(commits)
    md = generate(cats, since, version=args.version, url=args.url)
    Path(args.output).write_text(md)
    print(f"Wrote {args.output} ({len(md)} chars)")


if __name__ == "__main__":
    main()
