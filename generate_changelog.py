#!/usr/bin/env python3
"""generate_changelog.py - Generate a structured CHANGELOG.md from git history."""
import subprocess
import sys
import os
import re
from datetime import datetime

def run_git(repo_path, *args):
    """Run a git command in the given repo path."""
    result = subprocess.run(
        ["git"] + list(args),
        cwd=repo_path,
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.returncode

def get_commits(repo_path, since_tag=None):
    """Fetch commits from git log."""
    if since_tag:
        range_spec = f"{since_tag}..HEAD"
    else:
        # Try to find the latest tag
        tags, rc = run_git(repo_path, "tag", "--sort=-version:refname")
        if rc == 0 and tags:
            latest_tag = tags.split("\n")[0]
            range_spec = f"{latest_tag}..HEAD"
        else:
            range_spec = "HEAD"

    # Fetch commits: hash|subject|date
    fmt = "%h|%s|%ad"
    args = ["log", f"--pretty=format:{fmt}", "--date=short"]
    if range_spec != "HEAD":
        args.append(range_spec)
    
    output, rc = run_git(repo_path, *args)
    if rc != 0 or not output:
        return []
    
    commits = []
    for line in output.split("\n"):
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({
                "hash": parts[0],
                "subject": parts[1],
                "date": parts[2]
            })
    return commits

def categorize_commit(commit):
    """Categorize a commit based on conventional commit format."""
    subject = commit["subject"]
    
    # Match conventional commit: type(scope): description or type: description
    match = re.match(r'^([a-zA-Z]+)(\([^)]*\))?!?:\s*(.*)', subject)
    if match:
        commit_type = match.group(1).lower()
        clean_subject = match.group(3)
    else:
        commit_type = "other"
        clean_subject = subject
    
    # Handle revert
    if clean_subject.startswith("Revert "):
        clean_subject = "Reverted: " + clean_subject[7:]
    
    return commit_type, clean_subject

CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "perf": "Performance Improvements",
    "refactor": "Changed",
    "change": "Changed",
    "style": "Changed",
    "remove": "Removed",
    "del": "Removed",
    "rm": "Removed",
    "docs": "Documentation",
    "doc": "Documentation",
    "test": "Chores",
    "chore": "Chores",
    "build": "Chores",
    "ci": "Chores",
}

def main():
    if len(sys.argv) < 4:
        print("Usage: generate_changelog.py [repo_path] [since_tag] [output_file]", file=sys.stderr)
        sys.exit(1)
    
    repo_path = os.path.abspath(sys.argv[1])
    since_tag = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else ""
    output_file = os.path.abspath(sys.argv[3])
    
    commits = get_commits(repo_path, since_tag)
    if not commits:
        print("No commits found.")
        sys.exit(0)
    
    # Categorize
    categories = {}
    for cat in CATEGORY_MAP.values():
        categories[cat] = []
    categories["Other Changes"] = []
    
    for commit in commits:
        commit_type, clean_subject = categorize_commit(commit)
        category = CATEGORY_MAP.get(commit_type, "Other Changes")
        link = f"[{commit['hash']}](`git show {commit['hash']}`)"
        entry = f"- {link} {clean_subject} ({commit['date']})"
        categories[category].append(entry)
    
    # Get current version
    desc, rc = run_git(repo_path, "describe", "--tags", "--always")
    version = desc if rc == 0 and desc else "HEAD"
    
    # Write CHANGELOG.md
    lines = [
        "# Changelog",
        "",
        f"## {version}",
        "",
        "---",
        "",
    ]
    
    for cat in ["Added", "Fixed", "Changed", "Performance Improvements", 
                 "Removed", "Documentation", "Chores", "Other Changes"]:
        if categories[cat]:
            lines.append(f"### {cat}")
            lines.extend(categories[cat])
            lines.append("")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"CHANGELOG.md generated at: {output_file}")
    print(f"Categorized {len(commits)} commits into {sum(1 for v in categories.values() if v)} sections")

if __name__ == "__main__":
    main()
