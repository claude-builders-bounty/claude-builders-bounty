#!/usr/bin/env python3
"""
generate-changelog.py
Auto-generate a structured CHANGELOG.md from git history.

Usage:
    python3 generate-changelog.py [--repo PATH] [--output FILE]

Categories (auto-detected from commit message):
    Added    → feat:, add, introduce, new, implement
    Fixed    → fix:, bugfix, resolve, patch, hotfix
    Changed  → refactor:, update, modify, improve, enhance, perf:
    Removed  → remove:, delete, drop, deprecate, clean
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_git(args, cwd=None):
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"git error: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def get_last_tag(repo_path):
    """Return the most recent git tag, or None."""
    out = run_git(["describe", "--tags", "--abbrev=0"], cwd=repo_path)
    return out if out else None


def get_commits_since(tag, repo_path):
    """Return list of (hash, subject, date) tuples since tag."""
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"

    out = run_git(
        ["log", range_spec, "--pretty=format:%H|%s|%ad", "--date=short"],
        cwd=repo_path,
    )
    commits = []
    for line in out.splitlines():
        if "|" not in line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append(parts)
    return commits


def categorize_commit(subject):
    """Categorize a commit subject into Added/Fixed/Changed/Removed."""
    s = subject.lower()

    # Conventional commit prefixes
    if re.search(r"^(feat|feature)\b", s):
        return "Added"
    if re.search(r"^fix\b", s):
        return "Fixed"
    if re.search(r"^(refactor|perf|chore|style|docs|test)\b", s):
        return "Changed"
    if re.search(r"^(remove|delete|drop|revert)\b", s):
        return "Removed"

    # Keyword fallback
    if any(k in s for k in ("add ", "introduce", "new ", "implement", "create")):
        return "Added"
    if any(k in s for k in ("fix", "bugfix", "resolve", "patch", "hotfix", "correct")):
        return "Fixed"
    if any(k in s for k in ("remove", "delete", "drop", "deprecate", "clean")):
        return "Removed"
    if any(k in s for k in ("update", "modify", "improve", "enhance", "refactor", "change", "upgrade")):
        return "Changed"

    # Default
    return "Changed"


def generate_changelog(commits, repo_name, tag):
    """Build markdown changelog from categorized commits."""
    categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}

    for hsh, subject, date in commits:
        cat = categorize_commit(subject)
        categories[cat].append((hsh, subject, date))

    lines = []
    lines.append(f"# Changelog\n")
    lines.append(f"All notable changes to `{repo_name}` will be documented in this file.\n")

    today = datetime.now().strftime("%Y-%m-%d")
    tag_label = f"[{tag} → HEAD]" if tag else "[unreleased]"
    lines.append(f"## {tag_label} — {today}\n")

    for cat in ("Added", "Changed", "Fixed", "Removed"):
        items = categories[cat]
        if not items:
            continue
        lines.append(f"### {cat}\n")
        for hsh, subject, date in items:
            short_hash = hsh[:7]
            lines.append(f"- {subject} (`{short_hash}`)\n")
        lines.append("")

    if not any(categories.values()):
        lines.append("_No changes found._\n")

    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--repo", default=".", help="Path to git repository (default: .)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--since", help="Override: tag/commit to start from")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing file")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    if not (repo_path / ".git").exists():
        print(f"Error: {repo_path} is not a git repository.", file=sys.stderr)
        sys.exit(1)

    # Determine start point
    tag = args.since or get_last_tag(str(repo_path))
    commits = get_commits_since(tag, str(repo_path))

    if not commits:
        print("No commits found since the specified reference.")
        sys.exit(0)

    repo_name = repo_path.name
    changelog = generate_changelog(commits, repo_name, tag)

    if args.dry_run:
        print(changelog)
    else:
        output_path = repo_path / args.output
        output_path.write_text(changelog, encoding="utf-8")
        print(f"✅ CHANGELOG written to {output_path}")
        print(f"   Commits processed: {len(commits)}")
        if tag:
            print(f"   Since tag: {tag}")


if __name__ == "__main__":
    main()
