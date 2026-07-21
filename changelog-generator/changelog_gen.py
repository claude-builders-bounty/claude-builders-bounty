#!/usr/bin/env python3
"""
changelog-gen — Generate structured CHANGELOG.md from git history.

Parses conventional commits and outputs a Keep a Changelog format.
Works standalone or as a Claude Code skill.

Usage:
    python3 changelog_gen.py                      # All commits since last tag
    python3 changelog_gen.py --since v1.0.0       # Since specific tag
    python3 changelog_gen.py --output CHANGELOG.md # Write to file
    python3 changelog_gen.py --append              # Prepend to existing CHANGELOG.md
    python3 changelog_gen.py --github owner/repo   # Link commits to GitHub
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ── Conventional Commit Parser ─────────────────────────────────────────────────

# Pattern: type(scope)!: description
COMMIT_PATTERN = re.compile(
    r"^(?P<type>[a-zA-Z]+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<description>.+)$"
)

# Mapping: conventional commit type → CHANGELOG category
TYPE_MAP = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "docs": "Changed",
    "style": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "test": "Changed",
    "revert": "Removed",
}

CATEGORY_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


# ── Git helpers ────────────────────────────────────────────────────────────────

def run_git(*args: str) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def get_latest_tag() -> str | None:
    """Get the most recent tag, or None if no tags exist."""
    try:
        return run_git("describe", "--tags", "--abbrev=0")
    except RuntimeError:
        return None


def get_commits(since: str | None = None) -> list[dict]:
    """Get commits since a ref. Falls back to full history if no tag exists."""
    fmt = "%H%n%s%n%b%n%an%n%aI%n---END---"
    if since:
        range_spec = f"{since}..HEAD"
    else:
        # No tag found — get all commits (fallback)
        range_spec = "HEAD~100..HEAD"  # Last 100 commits as fallback

    try:
        raw = run_git("log", range_spec, f"--pretty=format:{fmt}", "--no-merges")
    except RuntimeError:
        return []

    if not raw:
        return []

    commits = []
    for block in raw.split("---END---"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n", 4)
        if len(lines) < 5:
            continue
        commits.append({
            "hash": lines[0].strip(),
            "subject": lines[1].strip(),
            "body": lines[2].strip(),
            "author": lines[3].strip(),
            "date": lines[4].strip(),
        })

    return commits


def get_tags() -> list[tuple[str, str]]:
    """Get all tags with their dates, sorted newest first."""
    try:
        raw = run_git("tag", "--sort=-creatordate", "--format=%(refname:short)|%(creatordate:short)")
    except RuntimeError:
        return []

    tags = []
    for line in raw.split("\n"):
        if "|" in line:
            name, date = line.split("|", 1)
            tags.append((name.strip(), date.strip()))
    return tags


# ── Commit categorization ──────────────────────────────────────────────────────

def parse_commit(subject: str) -> tuple[str, str | None, bool, str]:
    """Parse a conventional commit subject. Returns (type, scope, breaking, description)."""
    m = COMMIT_PATTERN.match(subject)
    if m:
        return (
            m.group("type").lower(),
            m.group("scope"),
            bool(m.group("breaking")),
            m.group("description"),
        )
    # Fallback: treat as "Other"
    return ("other", None, False, subject)


def categorize_commits(commits: list[dict]) -> dict[str, list[dict]]:
    """Group commits into CHANGELOG categories."""
    categories: dict[str, list[dict]] = defaultdict(list)

    for commit in commits:
        ctype, scope, breaking, description = parse_commit(commit["subject"])

        # Breaking changes always go first
        if breaking or (commit["body"] and "BREAKING CHANGE" in commit["body"]):
            category = "Changed"
            prefix = "**BREAKING** "
        else:
            category = TYPE_MAP.get(ctype, "Changed")
            prefix = ""

        # Format the entry
        if scope:
            entry = f"{prefix}**{scope}:** {description}"
        else:
            entry = f"{prefix}{description}"

        commit["entry"] = entry
        commit["category"] = category
        categories[category].append(commit)

    return dict(categories)


# ── Output formatting ──────────────────────────────────────────────────────────

def format_changelog(
    categories: dict[str, list[dict]],
    version: str | None = None,
    date: str | None = None,
    github_repo: str | None = None,
) -> str:
    """Format categorized commits into Keep a Changelog Markdown."""
    lines = []

    # Header
    if version:
        header = f"## [{version}]"
    else:
        header = "## [Unreleased]"

    if date:
        header += f" - {date}"

    lines.append(header)
    lines.append("")

    # Categories in standard order
    for category in CATEGORY_ORDER:
        commits = categories.get(category, [])
        if not commits:
            continue

        lines.append(f"### {category}")
        lines.append("")

        for commit in commits:
            hash_short = commit["hash"][:7]
            entry = commit["entry"]

            if github_repo:
                link = f"[`{hash_short}`](https://github.com/{github_repo}/commit/{commit['hash']})"
                lines.append(f"- {entry} ({link})")
            else:
                lines.append(f"- {entry} (`{hash_short}`)")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def prepend_to_changelog(new_content: str, changelog_path: Path) -> None:
    """Prepend new content to an existing CHANGELOG.md."""
    if changelog_path.exists():
        existing = changelog_path.read_text(encoding="utf-8")
        # Find the first ## heading and insert before it
        match = re.search(r"^## ", existing, re.MULTILINE)
        if match:
            pos = match.start()
            updated = existing[:pos] + new_content + "\n" + existing[pos:]
        else:
            updated = new_content + "\n" + existing
    else:
        updated = f"# Changelog\n\n{new_content}"

    changelog_path.write_text(updated, encoding="utf-8")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="changelog-gen",
        description="Generate structured CHANGELOG.md from git history",
    )
    parser.add_argument(
        "--since", default=None,
        help="Git ref to start from (default: last tag, or all commits)",
    )
    parser.add_argument(
        "--version", "-v", default=None,
        help="Version label for this release (e.g., 1.2.0)",
    )
    parser.add_argument(
        "--date", default=None,
        help="Release date (default: today)",
    )
    parser.add_argument(
        "--github", default=None,
        help="GitHub repo for commit links (e.g., owner/repo)",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write to file instead of stdout",
    )
    parser.add_argument(
        "--append", action="store_true",
        help="Prepend to existing CHANGELOG.md (requires --output)",
    )

    args = parser.parse_args()

    # Resolve --since
    since = args.since
    if not since:
        since = get_latest_tag()

    # Resolve --date
    date = args.date
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get and categorize commits
    commits = get_commits(since)
    if not commits:
        tag_info = f" since {since}" if since else ""
        print(f"No commits found{tag_info}.", file=sys.stderr)
        sys.exit(0)

    categories = categorize_commits(commits)

    # Format
    changelog = format_changelog(
        categories,
        version=args.version,
        date=date,
        github_repo=args.github,
    )

    # Output
    if args.output:
        path = Path(args.output)
        if args.append:
            prepend_to_changelog(changelog, path)
        else:
            path.write_text(f"# Changelog\n\n{changelog}", encoding="utf-8")
        print(f"Written to {path}", file=sys.stderr)
    else:
        print(changelog)


if __name__ == "__main__":
    main()
