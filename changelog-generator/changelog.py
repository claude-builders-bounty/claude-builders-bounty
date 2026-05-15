#!/usr/bin/env python3
"""
changelog.py — Generate structured CHANGELOG.md from git history.

Zero external dependencies (stdlib only).
Supports: Conventional Commits, auto-categorization, last-tag detection.

Usage:
    python changelog.py                    # generate CHANGELOG.md
    python changelog.py --since v1.0.0     # from a specific tag
    python changelog.py --output RELEASE.md
"""

import subprocess
import re
import sys
import os
from datetime import datetime, timezone
from collections import OrderedDict
from typing import Optional


def run_git(*args: str) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""
    except FileNotFoundError:
        print("Error: git not found. This script must be run inside a git repository.", file=sys.stderr)
        sys.exit(1)


def get_last_tag() -> Optional[str]:
    """Find the most recent git tag (semver or any)."""
    tag = run_git("describe", "--tags", "--abbrev=0", "--match", "v*")
    if not tag:
        tag = run_git("describe", "--tags", "--abbrev=0")
    return tag if tag else None


def parse_conventional_commit(message: str) -> tuple:
    """
    Parse a conventional commit message.
    Returns (type, scope, description, is_breaking).

    Examples:
        feat(auth): add login → ('feat', 'auth', 'add login', False)
        fix!: fix security issue → ('fix', None, 'fix security issue', True)
        docs(readme): update usage → ('docs', 'readme', 'update usage', False)
    """
    # Pattern: type(scope)!: description
    # Or: type!: description
    # Or: type(scope): description
    pattern = r'^(\w+)(?:\(([^)]*)\))?(!)?\s*:\s*(.+)$'
    match = re.match(pattern, message)
    if not match:
        return None, None, message, False

    commit_type = match.group(1).lower()
    scope = match.group(2)
    is_breaking = bool(match.group(3))
    description = match.group(4).strip()

    # Also check for BREAKING CHANGE in body
    return commit_type, scope, description, is_breaking


def categorize_commit(commit_type: str, is_breaking: bool) -> str:
    """Map a conventional commit type to a changelog category."""
    if is_breaking:
        return "Changed"  # Breaking changes go to Changed

    category_map = {
        "feat": "Added",
        "feature": "Added",
        "add": "Added",
        "fix": "Fixed",
        "bugfix": "Fixed",
        "hotfix": "Fixed",
        "patch": "Fixed",
        "docs": "Added",
        "documentation": "Added",
        "style": "Changed",
        "refactor": "Changed",
        "perf": "Changed",
        "performance": "Changed",
        "improve": "Changed",
        "improvement": "Changed",
        "enhancement": "Changed",
        "chore": "Changed",
        "build": "Changed",
        "ci": "Changed",
        "test": "Changed",
        "testing": "Changed",
        "revert": "Fixed",
        "remove": "Removed",
        "delete": "Removed",
        "deprecate": "Removed",
        "deprecation": "Removed",
    }
    return category_map.get(commit_type, "Changed")


def get_commits(since: Optional[str] = None) -> list[dict]:
    """Get commits grouped by tag/version."""
    if since:
        log_range = f"{since}..HEAD"
    else:
        # Try to get all commits (first commit to HEAD)
        log_range = "HEAD"

    # Format: hash|||author_date|||author_name|||subject|||body
    fmt = "%H|||%aI|||%an|||%s|||%b"
    
    if since:
        raw = run_git("log", log_range, f"--pretty=format:{fmt}", "--reverse")
    else:
        raw = run_git("log", "--all", f"--pretty=format:{fmt}", "--reverse")

    if not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|||", 4)
        if len(parts) < 4:
            continue

        commit_hash = parts[0]
        date_str = parts[1]
        author = parts[2]
        subject = parts[3]
        body = parts[4] if len(parts) > 4 else ""

        commit_type, scope, description, is_breaking = parse_conventional_commit(subject)

        commits.append({
            "hash": commit_hash[:8],
            "date": date_str,
            "author": author,
            "type": commit_type,
            "scope": scope,
            "description": description,
            "is_breaking": is_breaking,
            "body": body.strip(),
            "raw_subject": subject,
        })

    return commits


def get_tags_with_commits() -> list[dict]:
    """Get all tags with their commits, plus untagged commits at the top."""
    tags = run_git("tag", "--sort=-v:refname")
    if not tags:
        # No tags — all commits are one group
        commits = get_commits()
        return [{"version": "Unreleased", "commits": commits}] if commits else []

    tag_list = tags.split("\n")
    
    # Get commits since the first tag
    first_tag = tag_list[-1]  # Oldest tag
    result = []

    # Untagged commits (newer than the latest tag)
    latest_tag = tag_list[0]
    unreleased = get_commits(since=latest_tag) if latest_tag else []
    if unreleased:
        result.append({"version": "Unreleased", "commits": unreleased, "date": None})

    # Commits per tag
    for i, tag in enumerate(tag_list):
        if i + 1 < len(tag_list):
            # Commits between this tag and the next older one
            next_tag = tag_list[i + 1]
            range_str = f"{next_tag}..{tag}"
        else:
            # Oldest tag — get commits before it
            # Use the tag ref itself
            range_str = tag

        # Get the tag date
        tag_date = run_git("log", "-1", "--format=%aI", tag)
        
        raw = run_git("log", range_str, "--format=%H|||%aI|||%an|||%s|||%b", "--reverse")
        if not raw:
            continue

        commits = []
        for line in raw.split("\n"):
            if not line.strip():
                continue
            parts = line.split("|||", 4)
            if len(parts) < 4:
                continue

            subject = parts[3]
            body = parts[4] if len(parts) > 4 else ""
            commit_type, scope, description, is_breaking = parse_conventional_commit(subject)

            commits.append({
                "hash": parts[0][:8],
                "date": parts[1],
                "author": parts[2],
                "type": commit_type,
                "scope": scope,
                "description": description,
                "is_breaking": is_breaking,
                "body": body.strip(),
                "raw_subject": subject,
            })

        if commits:
            result.append({
                "version": tag,
                "commits": commits,
                "date": tag_date[:10] if tag_date else None,
            })

    return result


def format_changelog(sections: list[dict]) -> str:
    """Format categorized commits into a CHANGELOG.md string."""
    categories_order = ["Added", "Changed", "Fixed", "Removed"]
    category_icons = {
        "Added": "✨",
        "Changed": "🔄",
        "Fixed": "🐛",
        "Removed": "🗑️",
    }
    category_descriptions = {
        "Added": "New features and additions",
        "Changed": "Changes and improvements",
        "Fixed": "Bug fixes and corrections",
        "Removed": "Deprecations and removals",
    }

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project are documented in this file.",
        "",
    ]

    for section in sections:
        version = section["version"]
        date_str = section.get("date")
        
        if date_str:
            lines.append(f"## [{version}] - {date_str}")
        else:
            lines.append(f"## [{version}]")
        lines.append("")

        # Group commits by category
        categorized: dict[str, list] = OrderedDict()
        for cat in categories_order:
            categorized[cat] = []

        for c in section["commits"]:
            if c["type"] is None:
                # Uncategorized commit
                categorized.setdefault("Changed", [])
                categorized["Changed"].append(c)
            else:
                cat = categorize_commit(c["type"], c["is_breaking"])
                categorized.setdefault(cat, [])
                categorized[cat].append(c)

        # Write categories
        has_any = any(items for items in categorized.values())
        if not has_any:
            lines.append("  - No notable changes")
            lines.append("")
            continue

        for cat in categories_order:
            commits = categorized[cat]
            if not commits:
                continue
            
            icon = category_icons[cat]
            # desc = category_descriptions[cat]
            lines.append(f"### {icon} {cat}")
            lines.append("")

            # Group by scope if multiple scopes exist
            scopes: dict[str, list] = {}
            no_scope = []
            for c in commits:
                if c["scope"]:
                    scopes.setdefault(c["scope"], [])
                    scopes[c["scope"]].append(c)
                else:
                    no_scope.append(c)

            if len(scopes) > 1 or (scopes and no_scope):
                # Multiple scopes — group them
                for scope_name, scope_commits in sorted(scopes.items()):
                    for c in scope_commits:
                        lines.append(f"  - **{scope_name}:** {c['description']} ([{c['hash']}]({c['hash']}))")
                for c in no_scope:
                    lines.append(f"  - {c['description']} ([{c['hash']}]({c['hash']}))")
            else:
                # Single scope or no scope — flat list
                for c in commits:
                    if c["scope"]:
                        lines.append(f"  - **{c['scope']}:** {c['description']} ([{c['hash']}]({c['hash']}))")
                    else:
                        lines.append(f"  - {c['description']} ([{c['hash']}]({c['hash']}))")
            
            lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Generated by [changelog.py](https://github.com/laojinpassion/changelog-generator) on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

    return "\n".join(lines)


def generate(since: Optional[str] = None, output_file: str = "CHANGELOG.md") -> None:
    """Main generate function."""
    if not os.path.exists(".git"):
        print("Error: Not a git repository. Run this from the root of a git repo.", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Analyzing git history...")
    
    if since:
        commits = get_commits(since=since)
        sections = [{"version": "Unreleased", "commits": commits, "date": None}]
    else:
        sections = get_tags_with_commits()

    if not sections or all(len(s["commits"]) == 0 for s in sections):
        print("No commits found.", file=sys.stderr)
        sys.exit(0)

    total = sum(len(s["commits"]) for s in sections)
    print(f"📝 Found {total} commits across {len(sections)} version(s)")

    changelog = format_changelog(sections)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(changelog)

    print(f"✅ {output_file} generated ({len(changelog)} bytes)")
    print(f"   Versions: {', '.join(s['version'] for s in sections)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--since", "-s", help="Start from a specific tag/ref")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    args = parser.parse_args()

    generate(since=args.since, output_file=args.output)


if __name__ == "__main__":
    main()
