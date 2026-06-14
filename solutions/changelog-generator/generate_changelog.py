#!/usr/bin/env python3
"""
generate_changelog.py — Auto-generate CHANGELOG.md from git history
Usage: python3 generate_changelog.py [--repo PATH] [--output CHANGELOG.md] [--since TAG]

Generates a structured CHANGELOG.md by categorizing commits since the last git tag.
Categories: Added, Fixed, Changed, Removed, Deprecated, Security, Performance
"""

import subprocess
import re
import os
import sys
from datetime import datetime
from typing import List, Dict


def run_git(cmd: List[str], cwd: str = ".") -> str:
    """Run a git command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_last_tag(cwd: str = ".") -> str:
    """Get the most recent git tag, or 'HEAD' if none exist."""
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    return tag if tag else None


def get_commits_since(since: str, cwd: str = ".") -> List[Dict[str, str]]:
    """Get all commits since a given ref, with hash, subject, body."""
    if since:
        log_range = f"{since}..HEAD"
    else:
        log_range = "--all"

    raw = run_git(
        ["log", log_range, "--pretty=format:%H||%s||%an||%ai", "--reverse"],
        cwd=cwd,
    )
    if not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        parts = line.split("||", 3)
        if len(parts) >= 3:
            commits.append({
                "hash": parts[0][:7],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3] if len(parts) > 3 else "",
            })
    return commits


def categorize_commit(subject: str) -> str:
    """Categorize a commit by its subject line using Conventional Commits prefixes."""
    s = subject.lower().strip()

    # Commit type patterns — ordered by priority
    patterns = [
        (r"^feat(\(.+?\))?!?:", "Added"),
        (r"^fix(\(.+?\))?!?:", "Fixed"),
        (r"^perf(\(.+?\))?!?:", "Performance"),
        (r"^security", "Security"),
        (r"^refactor(\(.+?\))?!?:", "Changed"),
        (r"^style(\(.+?\))?!?:", "Changed"),
        (r"^revert", "Removed"),
        (r"^remove", "Removed"),
        (r"^deprecate", "Deprecated"),
        (r"^chore(\(.+?\))?!?:", "Changed"),
        (r"^docs(\(.+?\))?!?:", "Documentation"),
        (r"^test(\(.+?\))?!?:", "Testing"),
        (r"^ci(\(.+?\))?!?:", "CI/CD"),
        (r"^build(\(.+?\))?!?:", "Build"),
        # Fallback keyword matching
        (r"\b(?:add|new|create|implement|introduce)\b", "Added"),
        (r"\b(?:fix|bug|patch|hotfix|correct|resolve)\b", "Fixed"),
        (r"\b(?:remove|delete|drop|deprecate|phase.out)\b", "Removed"),
        (r"\b(?:refactor|rewrite|redesign|restructure)\b", "Changed"),
        (r"\b(?:upgrade|update|bump|migrate)\b", "Changed"),
    ]

    for pattern, category in patterns:
        if re.search(pattern, s):
            return category

    # Commits that don't match any known pattern → "Changed"
    return "Changed"


def format_changelog(
    commits: List[Dict[str, str]],
    version: str = None,
    repo_url: str = None,
) -> str:
    """Format commits into a CHANGELOG.md following Keep a Changelog convention."""
    if not commits:
        return "# Changelog\n\nNo commits found since the last tag.\n"

    # Categorize
    categories: Dict[str, List[Dict]] = {}
    for c in commits:
        cat = categorize_commit(c["subject"])
        categories.setdefault(cat, []).append(c)

    # Build header
    today = datetime.now().strftime("%Y-%m-%d")
    header = f"# Changelog\n\n"
    if version:
        header += f"## [{version}] - {today}\n"
    else:
        header += f"## [Unreleased] - {today}\n"
    if repo_url:
        header += f"\n> Auto-generated from [git history]({repo_url})\n"

    lines = [header]

    # Category order
    order = ["Added", "Fixed", "Changed", "Removed", "Deprecated",
             "Security", "Performance", "Documentation", "Testing", "CI/CD", "Build"]

    for cat in order:
        items = categories.pop(cat, [])
        if items:
            lines.append(f"\n### {cat}\n")
            for c in items:
                scope = ""
                m = re.match(r"^\w+(\([^)]+\))?!?: (.+)", c["subject"])
                if m:
                    desc = m.group(2)
                else:
                    desc = c["subject"]
                link = f"[`{c['hash']}`]({repo_url}/commit/{c['hash']})" if repo_url else f"`{c['hash']}`"
                lines.append(f"- {desc.capitalize()} ({link})")

    # Any remaining uncategorized
    for cat, items in categories.items():
        lines.append(f"\n### {cat}\n")
        for c in items:
            link = f"[`{c['hash']}`]({repo_url}/commit/{c['hash']})" if repo_url else f"`{c['hash']}`"
            lines.append(f"- {c['subject'].capitalize()} ({link})")

    return "\n".join(lines) + "\n"


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from git history"
    )
    parser.add_argument(
        "--repo", "-r",
        default=".",
        help="Path to the git repository (default: current dir)",
    )
    parser.add_argument(
        "--output", "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--since", "-s",
        default=None,
        help="Generate changelog since this ref (default: last tag)",
    )
    parser.add_argument(
        "--version", "-v",
        default=None,
        help="Version number for this release",
    )
    parser.add_argument(
        "--repo-url", "-u",
        default=None,
        help="Repository URL for commit links",
    )

    args = parser.parse_args()

    # Determine the starting point
    since = args.since or get_last_tag(args.repo)
    if since:
        print(f"ℹ️  Generating changelog since: {since}")
    else:
        print("ℹ️  No tags found — generating changelog from all commits")

    # Fetch commits
    commits = get_commits_since(since, args.repo)
    print(f"ℹ️  Found {len(commits)} commits")

    if not commits:
        print("⚠️  No commits found. Nothing to generate.")
        sys.exit(0)

    # Auto-detect repo URL if not provided
    repo_url = args.repo_url
    if not repo_url:
        remote = run_git(["remote", "get-url", "origin"], cwd=args.repo)
        if remote:
            # Convert SSH/HTTPS to web URL
            remote = remote.replace("git@", "https://").replace(".git", "")
            remote = remote.replace("github.com:", "github.com/")
            if remote.startswith("https://"):
                repo_url = remote

    # Generate
    changelog = format_changelog(commits, args.version, repo_url)

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(changelog)

    print(f"✅  CHANGELOG written to {args.output}")
    print(f"📝  Preview:\n")
    # Show first 15 lines as preview
    preview_lines = changelog.split("\n")[:15]
    for line in preview_lines:
        print(f"   {line}")


if __name__ == "__main__":
    main()
