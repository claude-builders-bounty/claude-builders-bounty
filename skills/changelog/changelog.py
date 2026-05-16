#!/usr/bin/env python3
"""Generate structured CHANGELOG.md from git history.

Usage:
  changelog.py                      # Output to stdout
  changelog.py --output CHANGELOG.md
  changelog.py --since v1.0.0       # Custom start point
  changelog.py --repo /path/to/repo # Another repo
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# Conventional commit type → Keep a Changelog category
TYPE_MAP: dict[str, str] = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "patch": "Fixed",
    "change": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "performance": "Changed",
    "update": "Changed",
    "style": "Changed",
    "remove": "Removed",
    "delete": "Removed",
    "deprecate": "Removed",
    "docs": "Documentation",
    "doc": "Documentation",
    "chore": "Maintenance",
    "build": "Maintenance",
    "ci": "Maintenance",
    "test": "Maintenance",
    "tests": "Maintenance",
    "security": "Security",
    "dep": "Dependencies",
    "deps": "Dependencies",
    "deps-dev": "Dependencies",
}

# Category display order
CATEGORY_ORDER = ["Added", "Changed", "Fixed", "Removed", "Security", "Dependencies", "Documentation", "Maintenance"]

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?\s*:\s*(?P<description>.+)"
)
PR_RE = re.compile(r"(?:#(\d+)|PR #(\d+)|\(#(\d+)\))")
ISSUE_RE = re.compile(r"#(\d+)")


def run_git(args: list[str], cwd: str | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True, text=True,
            cwd=cwd, timeout=30,
        )
        if result.returncode != 0:
            if "fatal" in (result.stderr or "").lower():
                return ""
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def get_latest_tag(cwd: str | None = None) -> str | None:
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd)
    return tag if tag else None


def get_commits(since: str | None = None, cwd: str | None = None) -> list[str]:
    args = ["log", "--format=%H~|~%s~|~%an~|~%ai", "--no-merges"]
    if since:
        args.append(f"{since}..HEAD")
    output = run_git(args, cwd)
    if not output:
        # Fallback: no range, get recent commits
        args = ["log", "--format=%H~|~%s~|~%an~|~%ai", "--no-merges", "-100"]
        output = run_git(args, cwd)
    return [line for line in output.split("\n") if line.strip() and "~|~" in line]


def parse_commit(line: str) -> dict:
    """Parse a log line into a structured commit."""
    parts = line.split("~|~", 3)
    sha, subject, author, date_str = parts if len(parts) == 4 else (*parts, "", "")

    date = None
    try:
        date = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, IndexError):
        try:
            date = datetime.fromisoformat(date_str) if date_str else None
        except (ValueError, TypeError):
            pass

    parsed_type = None
    parsed_scope = None
    parsed_desc = subject
    is_breaking = False

    m = CONVENTIONAL_RE.match(subject)
    if m:
        parsed_type = m.group("type").lower()
        parsed_scope = m.group("scope") or None
        parsed_desc = m.group("description").strip()
        is_breaking = m.group("breaking") == "!"

    # Detect PR/issue references
    pr_refs = []
    for match in PR_RE.finditer(subject):
        ref = match.group(1) or match.group(2) or match.group(3)
        if ref:
            pr_refs.append(f"#{ref}")

    return {
        "sha": sha[:8],
        "subject": subject,
        "description": parsed_desc,
        "author": author,
        "date": date,
        "type": parsed_type,
        "scope": parsed_scope,
        "breaking": is_breaking,
        "pr_refs": pr_refs,
    }


def categorize(commits: list[dict]) -> dict[str, list[dict]]:
    """Categorize commits into Keep a Changelog sections."""
    categories: dict[str, list[dict]] = defaultdict(list)

    for c in commits:
        cat = TYPE_MAP.get(c["type"], "Changed" if c["type"] else "Changed")
        if c["breaking"] and cat == "Added":
            cat = "Changed"  # Breaking features go under Changed
        categories[cat].append(c)

    return dict(categories)


def format_changelog(
    categories: dict[str, list[dict]],
    version: str | None = None,
    date_str: str | None = None,
) -> str:
    """Render the CHANGELOG.md content."""
    if not version:
        version = "Unreleased"
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines: list[str] = [
        f"## [{version}] - {date_str}",
        "",
    ]

    # Check for breaking changes
    breaking_commits = [c for cat_list in categories.values() for c in cat_list if c["breaking"]]
    if breaking_commits:
        lines.append("### ⚠ BREAKING CHANGES")
        lines.append("")
        for c in breaking_commits:
            scope = f"**{c['scope']}:** " if c["scope"] else ""
            pr = f" ({', '.join(c['pr_refs'])})" if c["pr_refs"] else ""
            lines.append(f"- {scope}{c['description']}{pr}")
            if c.get("sha"):
                lines[-1] += f" ({c['sha']})"
        lines.append("")

    seen_types = set()
    for cat in CATEGORY_ORDER:
        commits = categories.get(cat, [])
        if not commits:
            continue
        seen_types.add(cat)
        emoji = {
            "Added": "✨", "Changed": "🔧", "Fixed": "🐛",
            "Removed": "🗑", "Security": "🔒", "Dependencies": "📦",
            "Documentation": "📝", "Maintenance": "🧹",
        }.get(cat, "")
        lines.append(f"### {emoji} {cat}" if emoji else f"### {cat}")
        lines.append("")

        for c in commits:
            if c["breaking"]:
                continue  # Already listed above
            scope = f"**{c['scope']}:** " if c["scope"] else ""
            pr = f" ({', '.join(c['pr_refs'])})" if c["pr_refs"] else ""
            sha_suffix = f" ({c['sha']})" if c.get("sha") and not c["pr_refs"] else ""
            lines.append(f"- {scope}{c['description']}{pr}{sha_suffix}")
        lines.append("")

    # Any uncategorized
    uncategorized = categories.get("Changed", [])
    types_used = set(TYPE_MAP.get(c["type"], "") for cat_list in categories.values() for c in cat_list)
    return "\n".join(lines).rstrip("\n") + "\n"


def get_version(cwd: str | None = None) -> str | None:
    """Try to determine the next version from git tags."""
    tags = run_git(["tag", "--sort=-v:refname", "--merged"], cwd)
    if not tags:
        return "0.1.0"
    latest = tags.split("\n")[0].lstrip("v")
    parts = latest.split(".")
    if len(parts) == 3:
        return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
    return latest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--since", help="Starting tag/commit (default: last git tag)")
    parser.add_argument("--repo", help="Path to git repository (default: current dir)")
    parser.add_argument("--version", help="Version string (default: auto-detected)")
    args = parser.parse_args(argv)

    cwd = args.repo

    # Determine since point
    since = args.since or get_latest_tag(cwd)

    # Get commits
    raw_commits = get_commits(since, cwd)
    if not raw_commits:
        print("No commits found. Make sure you're in a git repository.", file=sys.stderr)
        return 1

    parsed = [parse_commit(c) for c in raw_commits]
    parsed.reverse()  # chronological order

    # Determine version
    version = args.version or get_version(cwd) or "Unreleased"

    # Categorize and format
    categories = categorize(parsed)
    changelog = format_changelog(categories, version=version)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(changelog)
        print(f"CHANGELOG written to {out_path}")
    else:
        print(changelog)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
