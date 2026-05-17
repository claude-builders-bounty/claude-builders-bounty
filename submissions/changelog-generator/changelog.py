#!/usr/bin/env python3
"""
changelog.py — Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py [--repo PATH] [--output FILE] [--from-tag TAG] [--to-ref REF]

Dependencies: git (must be installed and available in PATH)
"""

import argparse
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime


CATEGORIES = OrderedDict([
    ("Added", ["add", "feat", "feature", "implement", "create", "new", "+"]),
    ("Changed", ["change", "update", "refactor", "improve", "migrate", "bump", "upgrade", "deprecate"]),
    ("Fixed", ["fix", "bug", "hotfix", "patch", "correct", "resolve", "~"]),
    ("Removed", ["remove", "delete", "drop", "deprecate", "cleanup", "strip", "-"]),
])

CONVENTIONAL_PREFIX = re.compile(
    r'^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?\s*:\s*(?P<subject>.+)',
    re.IGNORECASE
)


def run_git(cmd, cwd=None):
    """Run a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, cwd=cwd, timeout=30
        )
        if result.returncode != 0:
            return None
        return result.stdout.rstrip("\n")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_last_tag(repo_path):
    """Get the most recent git tag, sorted by version. Returns None if no tags."""
    # Try semantic version sort
    tags = run_git(["git", "tag", "--sort=-version:refname"], cwd=repo_path)
    if not tags:
        return None
    first_tag = tags.split("\n")[0] if tags else None
    return first_tag


def get_repo_name(repo_path):
    """Get the repo name from git remote."""
    remote_url = run_git(["git", "remote", "get-url", "origin"], cwd=repo_path)
    if not remote_url:
        return "unknown-repo"
    # Extract owner/repo from git@github.com:owner/repo.git or https://github.com/owner/repo.git
    match = re.search(r'[:/]([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return "unknown-repo"


def get_commits_since_tag(repo_path, from_tag, to_ref="HEAD"):
    """Get commits between from_tag and to_ref (default HEAD)."""
    if from_tag:
        range_spec = f"{from_tag}..{to_ref}"
    else:
        range_spec = to_ref

    log = run_git(
        ["git", "log", range_spec, "--pretty=format:%H|%s|%an"],
        cwd=repo_path
    )
    if not log:
        return []
    return [line.split("|", 2) for line in log.strip().split("\n")]


def categorize_commit(subject):
    """Return the category for a commit subject line."""
    subject_lower = subject.lower()
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in subject_lower:
                return category
    return "Changed"  # Default


def parse_conventional_commit(subject):
    """Parse a conventional commit subject. Returns (type, scope, subject)."""
    match = CONVENTIONAL_PREFIX.match(subject)
    if match:
        return match.group("type"), match.group("scope"), match.group("subject")
    return None, None, subject


def format_commit_hash(hash_str, repo_name):
    """Format commit hash as a markdown link."""
    return f"[`{hash_str[:7]}`](https://github.com/{repo_name}/commit/{hash_str})"


def generate_changelog(repo_path, output_file=None, from_tag=None, to_ref="HEAD"):
    """Generate CHANGELOG.md content."""
    repo_name = get_repo_name(repo_path)
    last_tag = from_tag or get_last_tag(repo_path)
    commits = get_commits_since_tag(repo_path, last_tag, to_ref)

    lines = []
    lines.append("# Changelog\n")
    lines.append(f"> {repo_name}\n")

    if last_tag:
        lines.append(f"## [{last_tag}] — {datetime.now().strftime('%Y-%m-%d')}\n")
    else:
        lines.append(f"## Unreleased — {datetime.now().strftime('%Y-%m-%d')}\n")

    categorized = OrderedDict([(cat, []) for cat in CATEGORIES.keys()])

    for commit_hash, subject, author in commits:
        # Skip merge commits
        if subject.startswith("Merge "):
            continue
        # Skip commits that are just updating changelogs
        if "changelog" in subject.lower() and ("update" in subject.lower() or "regenerate" in subject.lower()):
            continue

        category = categorize_commit(subject)
        commit_link = format_commit_hash(commit_hash, repo_name)
        categorized[category].append((commit_link, subject))

    emoji_map = {
        "Added": "✨",
        "Changed": "🔄",
        "Fixed": "🐛",
        "Removed": "🗑️",
    }

    for category in CATEGORIES.keys():
        entries = categorized[category]
        if entries:
            lines.append(f"### {emoji_map[category]} {category}\n")
            for link, subject in entries:
                lines.append(f"- {subject} ({link})")
            lines.append("")

    content = "\n".join(lines)

    if output_file:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, "w") as f:
            f.write(content)
        print(f"CHANGELOG written to {output_file}")

    return content


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--repo", default=".", help="Path to git repository")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--from-tag", default=None, help="Start from a specific tag")
    parser.add_argument("--to-ref", default="HEAD", help="End reference (default: HEAD)")
    args = parser.parse_args()

    abs_repo = os.path.abspath(args.repo)
    if not os.path.exists(os.path.join(abs_repo, ".git")):
        print(f"Error: {abs_repo} is not a git repository")
        sys.exit(1)

    generate_changelog(abs_repo, args.output, args.from_tag, args.to_ref)


if __name__ == "__main__":
    main()
