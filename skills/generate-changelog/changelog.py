#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history since the last tag.

Usage:
    python3 changelog.py                    # current directory
    python3 changelog.py --repo /path       # specified repo
    python3 changelog.py --output CHANGES.md
    python3 changelog.py --all              # all commits, ignore tag boundary
    python3 changelog.py --header "v2.0.0"
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from collections import OrderedDict
from typing import List, Optional, Tuple


CATEGORIES = OrderedDict([
    ("Added", ["feat", "feature", "add", "new"]),
    ("Fixed", ["fix", "bug", "patch", "hotfix"]),
    ("Changed", ["change", "refactor", "update", "perf", "improve", "deprecat"]),
    ("Removed", ["remove", "delete", "deprecate", "drop"]),
    ("Documentation", ["doc", "readme", "comment"]),
    ("Security", ["security", "cve", "vuln", "audit"]),
    ("Infrastructure", ["ci", "cd", "build", "deps", "dep", "docker", "config"]),
    ("Tests", ["test", "spec", "coverage"]),
])

CATEGORY_FALLBACK = "Miscellaneous"


def run_git(cmd: List[str], cwd: Optional[str] = None, check: bool = True) -> str:
    """Run a git command and return stdout stripped."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=check, cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Git error: {e.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
        return ""
    except FileNotFoundError:
        print("Error: git not found. Ensure git is installed and in PATH.", file=sys.stderr)
        sys.exit(1)


def get_latest_tag(cwd: Optional[str] = None) -> Optional[str]:
    """Return the most recent git tag, or None if no tags exist."""
    tag = run_git(["git", "describe", "--tags", "--abbrev=0"], cwd=cwd, check=False)
    return tag if tag and "fatal" not in tag.lower() else None


def get_commits(since: Optional[str] = None, all_commits: bool = False,
                cwd: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """Return list of (hash, subject, body) for commits since `since` (a tag/ref)."""
    args = ["git", "log", "--format=%H||%s||%b"]
    if not all_commits and since:
        args.append(f"{since}..HEAD")
    output = run_git(args, cwd=cwd)
    commits = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("||", 2)
        if len(parts) >= 2:
            h = parts[0][:7]
            subject = parts[1].strip()
            body = parts[2].strip() if len(parts) > 2 else ""
            commits.append((h, subject, body))
    return commits


def parse_pr_ref(subject: str, body: str) -> Optional[str]:
    """Extract PR reference from subject or body."""
    m = re.search(r'(?:#|PR\s*)(\d+)', subject)
    if m:
        return f"#{m.group(1)}"
    m = re.search(r'(?:#|PR\s*)(\d+)', body)
    if m:
        return f"#{m.group(1)}"
    return None


def categorize(subject: str) -> str:
    """Categorize a commit based on conventional commit prefix."""
    lower = subject.lower()
    for category, prefixes in CATEGORIES.items():
        for prefix in prefixes:
            # Match at start: "feat:", "feat(", "add:", "fix:", etc.
            if re.match(rf'^\s*{re.escape(prefix)}[\s(:]', lower):
                return category
            # Match [prefix] pattern like [feat] or [security]
            if re.search(rf'\[{re.escape(prefix)}\]', lower):
                return category
    return CATEGORY_FALLBACK


def generate_changelog(commits: List[Tuple[str, str, str]],
                       header: str = "Unreleased",
                       date: Optional[str] = None) -> str:
    """Generate the full CHANGELOG.md content."""
    categorized: dict = OrderedDict()
    for cat in CATEGORIES:
        categorized[cat] = []
    categorized[CATEGORY_FALLBACK] = []

    for h, subject, body in commits:
        cat = categorize(subject)
        pr_ref = parse_pr_ref(subject, body)
        # Clean up conventional commit prefix for display
        display = re.sub(r'^\s*(feat|fix|chore|docs|refactor|test|perf|ci|build|style)(\([^)]*\))?[\s:]*',
                         '', subject, flags=re.IGNORECASE).strip()
        display = display[0].upper() + display[1:] if display else subject

        if pr_ref:
            entry = f"{display} ({pr_ref})"
        else:
            entry = display
        categorized[cat].append((h, entry))

    today = date or datetime.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        f"## [{header}] - {today}",
        "",
    ]

    for category, entries in categorized.items():
        if not entries:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for h, entry in entries:
            lines.append(f"- {entry} ({h})")
        lines.append("")

    if all(len(v) == 0 for v in categorized.values()):
        lines.append("_No changes recorded._")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history"
    )
    parser.add_argument("--repo", "-r", default=None,
                        help="Path to git repository (default: current directory)")
    parser.add_argument("--output", "-o", default="CHANGELOG.md",
                        help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Include all commits (ignore tag boundary)")
    parser.add_argument("--header", default=None,
                        help="Release header (default: latest tag or 'Unreleased')")
    parser.add_argument("--date", default=None,
                        help="Release date (default: today)")
    args = parser.parse_args()

    cwd = os.path.abspath(args.repo) if args.repo else os.getcwd()

    # Verify we're in a git repo
    try:
        run_git(["git", "rev-parse", "--git-dir"], cwd=cwd)
    except SystemExit:
        print(f"Error: {cwd} is not a git repository.", file=sys.stderr)
        sys.exit(1)

    # Determine the tag boundary
    latest_tag = get_latest_tag(cwd)
    if args.header:
        header = args.header
    elif latest_tag:
        header = latest_tag
    else:
        header = "Unreleased"

    print(f"Generating changelog for: {cwd}", file=sys.stderr)
    if latest_tag and not args.all:
        print(f"Using commits since tag: {latest_tag}", file=sys.stderr)
    elif args.all:
        print("Including all commits (--all)", file=sys.stderr)
    else:
        print("No tags found. Including all commits. Use --all to confirm.", file=sys.stderr)

    commits = get_commits(since=latest_tag, all_commits=args.all, cwd=cwd)

    if not commits:
        print("No commits found.", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(commits)} commits", file=sys.stderr)

    changelog = generate_changelog(commits, header=header, date=args.date)

    output_path = os.path.abspath(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(changelog)

    print(f"Changelog written to: {output_path}", file=sys.stderr)
    print(f"\nPreview:\n{'-'*40}", file=sys.stderr)
    preview_lines = changelog.split("\n")[:15]
    print("\n".join(preview_lines), file=sys.stderr)


if __name__ == "__main__":
    main()
