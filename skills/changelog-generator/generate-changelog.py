#!/usr/bin/env python3
"""
generate-changelog.py
自动从 git 历史生成 CHANGELOG.md
用法: python3 generate-changelog.py [--repo /path/to/repo] [--output CHANGELOG.md]
"""
import subprocess
import argparse
import sys
import re
from datetime import datetime

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.returncode

def get_git_tags(repo_path):
    tags, _ = run("git tag --sort=-v:refname", cwd=repo_path)
    return tags.split("\n") if tags else []

def get_commits_since_tag(repo_path, tag=None):
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"
    commits, rc = run(f"git log {range_spec} --pretty=format:'%H|%s|%ae|%ad' --date=short", cwd=repo_path)
    if rc != 0 or not commits:
        # 无 tag，从头开始
        commits, _ = run("git log --pretty=format:'%H|%s|%ae|%ad' --date=short", cwd=repo_path)
    return [c.split("|") for c in commits.split("\n") if c]

def categorize(commit_msg):
    msg = commit_msg.lower()
    if msg.startswith("feat") or msg.startswith("add"):
        return "Added"
    elif msg.startswith("fix") or msg.startswith("bugfix"):
        return "Fixed"
    elif msg.startswith("refactor") or msg.startswith("chore") or msg.startswith("update"):
        return "Changed"
    elif msg.startswith("remove") or msg.startswith("delete") or msg.startswith("drop"):
        return "Removed"
    elif msg.startswith("docs"):
        return "Documentation"
    elif msg.startswith("test"):
        return "Testing"
    elif msg.startswith("perf"):
        return "Performance"
    elif msg.startswith("security"):
        return "Security"
    else:
        return "Changed"

def generate_changelog(repo_path):
    tags = get_git_tags(repo_path)
    current_tag = tags[0] if tags else None

    commits = get_commits_since_tag(repo_path, current_tag)

    categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Documentation": [], "Testing": [], "Performance": [], "Security": []}

    for commit in commits:
        if len(commit) < 2:
            continue
        sha, msg, author, date = commit[0], commit[1], commit[2] if len(commit) > 2 else "unknown", commit[3] if len(commit) > 3 else ""
        cat = categorize(msg)
        categories[cat].append((sha[:7], msg, date))

    # 生成 CHANGELOG
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Changelog\n", f"_Generated: {today}_\n"]

    if current_tag:
        lines.append(f"## [{current_tag}] - {today}\n")
    else:
        lines.append(f"## [Unreleased] - {today}\n")

    for cat in ["Added", "Fixed", "Changed", "Removed", "Documentation", "Testing", "Performance", "Security"]:
        items = categories[cat]
        if items:
            lines.append(f"### {cat}\n")
            for sha, msg, date in items:
                lines.append(f"- {msg} ({sha})")
            lines.append("")

    return "\n".join(lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CHANGELOG from git history")
    parser.add_argument("--repo", default=".", help="Repository path")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    args = parser.parse_args()

    changelog = generate_changelog(args.repo)
    print(changelog)

    if args.output:
        with open(args.output, "w") as f:
            f.write(changelog + "\n")
        print(f"\n✅ CHANGELOG written to {args.output}")
