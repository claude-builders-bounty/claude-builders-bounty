#!/usr/bin/env python3
"""Structured CHANGELOG.md generator from git history.

Auto-categorizes commits using Conventional Commits prefixes.
Zero dependencies — stdlib only.

Usage:
    python generate_changelog.py [--repo /path/to/repo] [--output CHANGELOG.md] [--since TAG]
"""
import subprocess
import sys
import os
import re
from datetime import date, datetime
from pathlib import Path

CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "refactor": "Changed",
    "style": "Changed",
    "perf": "Changed",
    "revert": "Removed",
    "remove": "Removed",
    "deprecate": "Removed",
    # Optional extra categories
    "docs": "Documentation",
    "test": "Testing",
    "ci": "CI/CD",
    "build": "Build",
    "chore": "Maintenance",
}

FALLBACK_CATEGORY = "Changed"

SKIP_PREFIXES = {"merge", "release", "version", "bump", "wip"}


def run_git(repo_path, *args):
    result = subprocess.run(
        ["git", "-C", repo_path, *args],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        sys.stderr.write(f"git error: {result.stderr.strip()}\n")
        return ""
    return result.stdout.strip()


def get_latest_tag(repo_path):
    """Get most recent git tag."""
    tags = run_git(repo_path, "tag", "--sort=-creatordate").split("\n")
    return tags[0] if tags and tags[0] else None


def get_commits_since(repo_path, since_ref):
    """Get commit list since given ref."""
    fmt = "%H||%s||%an||%ad"
    if since_ref:
        commits = run_git(repo_path, "log", f"{since_ref}..HEAD", f"--format={fmt}", "--date=short")
    else:
        commits = run_git(repo_path, "log", f"--format={fmt}", "--date=short")
    return [c for c in commits.split("\n") if c.strip()]


def categorize_commit(subject):
    """Categorize a single commit by its conventional prefix."""
    subject_lower = subject.strip().lower()

    # Check conventional commit: type(scope): description
    match = re.match(r"^(\w[\w-]*)(?:\([^)]*\))?!?:\s*(.+)", subject_lower)
    if match:
        ptype, desc = match.group(1), match.group(2)
        if ptype in SKIP_PREFIXES:
            return None
        category = CATEGORY_MAP.get(ptype, FALLBACK_CATEGORY)
        return (category, subject.strip())

    # Fallback: keyword matching
    if any(kw in subject_lower for kw in ["add ", "added ", "implement", "introduce", "new "]):
        return ("Added", subject.strip())
    if any(kw in subject_lower for kw in ["fix ", "fixes ", "fixed ", "bug", "patch", "resolve"]):
        return ("Fixed", subject.strip())
    if any(kw in subject_lower for kw in ["remove", "delete", "drop", "deprecate"]):
        return ("Removed", subject.strip())
    if any(kw in subject_lower for kw in ["refactor", "change", "update", "modify", "tweak", "adjust"]):
        return ("Changed", subject.strip())

    # Skip merge commits
    if subject_lower.startswith("merge") or "merge pull request" in subject_lower:
        return None

    return (FALLBACK_CATEGORY, subject.strip())


def generate_changelog(repo_path, since_tag=None):
    """Generate structured CHANGELOG from git history."""
    if since_tag is None:
        since_tag = get_latest_tag(repo_path)

    commits = get_commits_since(repo_path, since_tag)

    # Group by category
    categorized = {}
    for line in commits:
        if "||" not in line:
            continue
        sha, subject, author, date_str = line.split("||", 3)
        result = categorize_commit(subject)
        if result is None:
            continue
        category, desc = result
        categorized.setdefault(category, []).append(
            f"{desc} ([`{sha[:7]}`](https://github.com/.../commit/{sha[:7]}))"
        )

    # Determine version header
    today = date.today().isoformat()
    if since_tag:
        version_header = f"## [{since_tag}] - {today}"
        unreleased_header = "## [Unreleased]"
    else:
        version_header = ""
        unreleased_header = f"## [Unreleased] — {today}"

    # Build markdown
    lines = ["# Changelog", ""]
    lines.append(unreleased_header)
    lines.append("")

    category_order = ["Added", "Fixed", "Changed", "Removed", "Documentation", "Testing", "CI/CD", "Build", "Maintenance"]
    for cat in category_order:
        if cat in categorized:
            lines.append(f"### {cat}")
            for entry in categorized[cat]:
                lines.append(f"- {entry}")
            lines.append("")

    if version_header:
        lines.append(version_header)
        lines.append("")
        lines.append(f"_Generated from commits after `{since_tag}`._")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git history")
    parser.add_argument("--repo", default=".", help="Path to git repository (default: .)")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    parser.add_argument("--since", default=None, help="Git ref to start from (default: latest tag, or first commit)")
    args = parser.parse_args()

    repo = str(Path(args.repo).resolve())
    changelog = generate_changelog(repo, args.since)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(changelog + "\n")

    print(f"✅ CHANGELOG written to {args.output} ({len(changelog.splitlines())} lines)")


if __name__ == "__main__":
    main()
