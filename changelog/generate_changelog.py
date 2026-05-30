#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.

Usage:
    python generate_changelog.py [--repo PATH] [--output FILE] [--since TAG]

Categorizes commits into: Added, Fixed, Changed, Removed, and Security
based on conventional commit prefixes (feat, fix, refactor, chore, etc.).
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone


# Conventional commit prefix to changelog category mapping
CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "new": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "patch": "Fixed",
    "refactor": "Changed",
    "change": "Changed",
    "update": "Changed",
    "update": "Changed",
    "improve": "Changed",
    "enhance": "Changed",
    "move": "Changed",
    "rename": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "perf": "Changed",
    "style": "Changed",
    "docs": "Changed",
    "revert": "Removed",
    "remove": "Removed",
    "delete": "Removed",
    "deprecate": "Removed",
    "drop": "Removed",
    "security": "Security",
    "sec": "Security",
}

# Ordered categories for output
CATEGORY_ORDER = ["Added", "Fixed", "Changed", "Removed", "Security"]

# Regex to parse conventional commit messages
# Matches: type(scope)!: description  or  type: description
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)"          # type (feat, fix, etc.)
    r"(?:\((?P<scope>[^)]+)\))?"     # optional scope in parens
    r"(?P<breaking>!)?"              # optional breaking change marker
    r":\s*(?P<description>.+)$"      # description after colon
)

# Fallback: try to detect category from keywords in the message
KEYWORD_CATEGORIES = {
    "Added": ["add ", "added ", "new ", "create ", "created ", "implement ", "implemented ", "introduce ", "introduced ", "support "],
    "Fixed": ["fix ", "fixed ", "bug ", "patch ", "patched ", "resolve ", "resolved ", "repair ", "hotfix "],
    "Changed": ["update ", "updated ", "change ", "changed ", "improve ", "improved ", "refactor ", "refactored ", "move ", "moved ", "rename ", "renamed ", "bump ", "upgrade "],
    "Removed": ["remove ", "removed ", "delete ", "deleted ", "drop ", "dropped ", "deprecate ", "deprecated "],
    "Security": ["security ", "cve ", "vulnerability ", "exploit "],
}


def run_git(args, repo_path=None):
    """Run a git command and return stdout."""
    cmd = ["git"]
    if repo_path:
        cmd.extend(["-C", repo_path])
    cmd.extend(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def get_last_tag(repo_path=None):
    """Get the most recent git tag, or None if no tags exist."""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], repo_path=repo_path)
    except RuntimeError:
        return None


def get_commits_since(since_ref=None, repo_path=None):
    """Fetch commits since a given ref (or all commits if None)."""
    args = ["log", "--pretty=format:%H|||%s|||%an|||%aI"]
    if since_ref:
        args.append(f"{since_ref}..HEAD")
    output = run_git(args, repo_path=repo_path)
    if not output:
        return []

    commits = []
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|||", 3)
        if len(parts) != 4:
            continue
        sha, subject, author, date = parts
        commits.append({
            "sha": sha,
            "subject": subject.strip(),
            "author": author.strip(),
            "date": date.strip(),
        })
    return commits


def categorize_commit(subject):
    """Categorize a commit based on its subject line."""
    match = CONVENTIONAL_RE.match(subject)
    if match:
        commit_type = match.group("type").lower()
        scope = match.group("scope")
        breaking = bool(match.group("breaking"))
        description = match.group("description").strip()

        category = CATEGORY_MAP.get(commit_type)
        if category is None:
            category = "Changed"  # default fallback

        if breaking:
            description = f"**BREAKING**: {description}"

        if scope:
            description = f"**{scope}**: {description}"

        return category, description

    # Fallback: keyword detection
    subject_lower = subject.lower()
    for category, keywords in KEYWORD_CATEGORIES.items():
        for kw in keywords:
            if subject_lower.startswith(kw):
                return category, subject

    # Default to Changed
    return "Changed", subject


def group_commits_by_category(commits):
    """Group commits by changelog category."""
    grouped = OrderedDict((cat, []) for cat in CATEGORY_ORDER)
    for commit in commits:
        category, description = categorize_commit(commit["subject"])
        grouped[category].append({
            "description": description,
            "sha": commit["sha"],
            "author": commit["author"],
            "date": commit["date"],
        })
    return grouped


def format_date(iso_date):
    """Format an ISO 8601 date to a human-readable format."""
    try:
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return iso_date


def generate_changelog(grouped, version=None, since_ref=None, repo_path=None):
    """Generate the CHANGELOG.md content."""
    lines = []

    # Header
    if version:
        header = f"## {version}"
    elif since_ref:
        header = f"## Changes since {since_ref}"
    else:
        header = "## Changelog"

    # Get date range
    all_entries = [e for entries in grouped.values() for e in entries]
    if all_entries:
        dates = [format_date(e["date"]) for e in all_entries]
        header += f" ({dates[0]})" if dates else ""

    lines.append(header)
    lines.append("")

    total_commits = sum(len(v) for v in grouped.values())
    lines.append(f"**{total_commits} commits** categorized below.")
    lines.append("")

    for category in CATEGORY_ORDER:
        entries = grouped[category]
        if not entries:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for entry in entries:
            short_sha = entry["sha"][:7]
            lines.append(
                f"- {entry['description']} "
                f"([`{short_sha}`](https://github.com/placeholder/commit/{entry['sha']}))"
            )
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history"
    )
    parser.add_argument(
        "--repo", default=None, help="Path to the git repository (default: current directory)"
    )
    parser.add_argument(
        "--output", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)"
    )
    parser.add_argument(
        "--since", default=None, help="Git ref to start from (default: last tag, or all commits)"
    )
    parser.add_argument(
        "--version", default=None, help="Version label for this changelog entry"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print to stdout instead of writing a file"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON instead of markdown"
    )
    args = parser.parse_args()

    repo_path = args.repo or os.getcwd()

    # Determine the starting ref
    since_ref = args.since
    if since_ref is None:
        since_ref = get_last_tag(repo_path=repo_path)

    # Get commits
    commits = get_commits_since(since_ref=since_ref, repo_path=repo_path)

    if not commits:
        print("No new commits found.", file=sys.stderr)
        sys.exit(0)

    # Categorize
    grouped = group_commits_by_category(commits)

    # Generate output
    if args.json:
        output = json.dumps(
            {"since": since_ref, "version": args.version, "categories": {
                cat: entries for cat, entries in grouped.items() if entries
            }},
            indent=2,
        )
    else:
        output = generate_changelog(
            grouped, version=args.version, since_ref=since_ref, repo_path=repo_path
        )

    # Write output
    if args.dry_run or args.json:
        print(output)
    else:
        output_path = args.output
        # If an existing changelog exists, prepend the new entry
        existing = ""
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                existing = f.read()

        with open(output_path, "w") as f:
            f.write("# Changelog\n\n")
            f.write(output)
            f.write("\n")
            # Append old content (skip the existing header if present)
            if existing:
                old = existing.replace("# Changelog\n\n", "", 1)
                if old.strip():
                    f.write("---\n\n")
                    f.write(old)
                    if not old.endswith("\n"):
                        f.write("\n")

        print(f"Changelog written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
