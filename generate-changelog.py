#!/usr/bin/env python3
"""
generate-changelog — Professional CHANGELOG Generator from Git History

Generates a structured CHANGELOG.md by parsing Conventional Commits
from the project's git history. Supports tag-based release grouping,
custom output paths, and exclusion of merge commits.

Usage:
  python3 generate-changelog.py              → CHANGELOG.md
  python3 generate-changelog.py --output RELEASE.md
  python3 generate-changelog.py --from-tag v1.0.0

Requirements: git, Python 3.8+
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import DefaultDict, Final, List, Optional, Tuple

# ─────────────────────────────────────────────
#  Types
# ─────────────────────────────────────────────
CommitType = str
CommitMessage = str
CommitHash = str
CategoryEntries = DefaultDict[CommitType, List[Tuple[CommitHash, CommitMessage]]]

# ─────────────────────────────────────────────
#  Conventional Commit Type → Section Mapping
# ─────────────────────────────────────────────
TYPE_LABELS: Final[dict[str, str]] = {
    "feat": "✨ Added",
    "feature": "✨ Added",
    "add": "✨ Added",
    "new": "✨ Added",
    "fix": "🐛 Fixed",
    "bugfix": "🐛 Fixed",
    "hotfix": "🐛 Fixed",
    "bug": "🐛 Fixed",
    "patch": "🐛 Fixed",
    "refactor": "♻️ Changed",
    "perf": "⚡ Performance",
    "performance": "⚡ Performance",
    "improve": "♻️ Changed",
    "improvement": "♻️ Changed",
    "change": "♻️ Changed",
    "update": "♻️ Changed",
    "remove": "🗑️ Removed",
    "delete": "🗑️ Removed",
    "deprecate": "🗑️ Removed",
    "drop": "🗑️ Removed",
    "docs": "📝 Documentation",
    "documentation": "📝 Documentation",
    "doc": "📝 Documentation",
    "style": "🎨 Style",
    "test": "✅ Tests",
    "testing": "✅ Tests",
    "ci": "👷 CI/CD",
    "build": "📦 Build",
    "chore": "🔧 Chores",
    "security": "🔒 Security",
    "docker": "🐳 Docker",
    "config": "⚙️ Configuration",
    "configs": "⚙️ Configuration",
}

# Types ordered by importance for the final output
SECTION_ORDER: Final[list[str]] = [
    "✨ Added",
    "🐛 Fixed",
    "⚡ Performance",
    "♻️ Changed",
    "🗑️ Removed",
    "🔒 Security",
    "📝 Documentation",
    "✅ Tests",
    "🎨 Style",
    "👷 CI/CD",
    "📦 Build",
    "🐳 Docker",
    "⚙️ Configuration",
    "🔧 Chores",
]

UNCATEGORIZED_LABEL: Final[str] = "📋 Uncategorized"


def get_type_prefix(message: str) -> str:
    """Extract the Conventional Commit type prefix from a message.
    
    Handles formats: feat: msg, feat(scope): msg, fix!: msg, etc.
    Returns the type (lowercase) or empty string.
    """
    match = re.match(r'^([a-zA-Z][a-zA-Z0-9_-]*)(?:\([^)]*\))?(!)?\s*:\s*', message)
    if match:
        return match.group(1).lower()
    return ""


def strip_type_prefix(message: str) -> str:
    """Remove the type prefix from a Conventional Commit message."""
    return re.sub(r'^[a-zA-Z][a-zA-Z0-9_-]*(?:\([^)]*\))?(!)?:\s*', '', message).strip()


def run_git(*args: str, repo_path: Optional[str] = None) -> str:
    """Run a git command and return stdout."""
    cmd = ["git"]
    if repo_path:
        cmd.extend(["-C", repo_path])
    cmd.extend(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running git {' '.join(args)}: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def get_latest_tag() -> Optional[str]:
    """Get the latest git tag, if any."""
    tag = run_git("describe", "--tags", "--abbrev=0").strip()
    return tag if tag else None


def get_commits(since_tag: Optional[str] = None) -> list[tuple[str, str, str]]:
    """Get commits as (hash, date, message) tuples.
    
    If since_tag is provided, only commits after that tag are included.
    """
    args = ["log", "--oneline", "--no-merges", "--format=%H|%aI|%s"]
    if since_tag:
        args.append(f"{since_tag}..HEAD")
    else:
        args.append("HEAD")  # All commits

    output = run_git(*args).strip()
    if not output:
        return []

    commits: list[tuple[str, str, str]] = []
    for line in output.split("\n"):
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append((parts[0], parts[1], parts[2]))

    return commits


def categorize_commits(commits: list[tuple[str, str, str]]) -> CategoryEntries:
    """Categorize commits by their Conventional Commit type."""
    categories: CategoryEntries = defaultdict(list)

    for hash_val, date_val, message in commits:
        type_prefix = get_type_prefix(message)
        clean_msg = strip_type_prefix(message) if type_prefix else message

        if type_prefix and type_prefix in TYPE_LABELS:
            label = TYPE_LABELS[type_prefix]
        elif type_prefix:
            # Unknown type — try to find the closest match or add as-is
            label = f"🔧 {type_prefix.capitalize()}"
        else:
            label = UNCATEGORIZED_LABEL

        categories[label].append((hash_val[:7], clean_msg))

    return categories


def generate_changelog(
    categories: CategoryEntries,
    version: Optional[str] = None,
    release_date: Optional[str] = None,
) -> str:
    """Generate formatted CHANGELOG.md content."""
    lines: list[str] = []

    # Header
    lines.append("# Changelog")
    lines.append("")

    if version:
        lines.append(f"## [{version}] - {release_date or date.today().isoformat()}")
    else:
        lines.append(f"## [Unreleased] - {release_date or date.today().isoformat()}")
    lines.append("")

    # Summary
    total = sum(len(msgs) for msgs in categories.values())
    lines.append(f"> **{total} change{'s' if total != 1 else ''}** in this release")
    lines.append("")

    # Sections in priority order
    ordered_sections = [s for s in SECTION_ORDER if s in categories]
    other_sections = [s for s in sorted(categories.keys()) if s not in SECTION_ORDER and s != UNCATEGORIZED_LABEL]
    uncategorized = categories.get(UNCATEGORIZED_LABEL, [])

    all_sections = ordered_sections + other_sections

    for section in all_sections:
        entries = categories[section]
        if not entries:
            continue

        lines.append(f"### {section}")
        lines.append("")
        for hash_val, msg in entries:
            lines.append(f"- {msg} ([`{hash_val}`](https://github.com/placeholder/commit/{hash_val}))")
        lines.append("")

    if uncategorized:
        lines.append("### 📋 Uncategorized")
        lines.append("")
        for hash_val, msg in uncategorized:
            lines.append(f"- {msg} ([`{hash_val}`](https://github.com/placeholder/commit/{hash_val}))")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--output", "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--from-tag", "-t",
        default=None,
        help="Generate changes since this tag (default: latest tag or all commits)",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Version string for the release header",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Release date (default: today)",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="Path to git repository (default: current directory)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print to stdout instead of writing to file",
    )

    args = parser.parse_args()

    # Determine tag range
    since_tag = args.from_tag
    if since_tag is None:
        try:
            since_tag = get_latest_tag()
        except (subprocess.CalledProcessError, SystemExit):
            since_tag = None

    # Get commits
    commits = get_commits(since_tag)

    if not commits:
        print("No commits found to generate changelog.", file=sys.stderr)
        return 0

    # Categorize
    categories = categorize_commits(commits)

    # Generate
    version = args.version
    if version is None and since_tag:
        version = since_tag

    changelog = generate_changelog(categories, version=version, release_date=args.date)

    # Output stats
    total = sum(len(msgs) for msgs in categories.values())
    print(f"\n  {'='*44}", file=sys.stderr)
    print(f"  📋  CHANGELOG Generated", file=sys.stderr)
    print(f"  {'='*44}", file=sys.stderr)
    print(f"     Total commits: {total}", file=sys.stderr)
    for section, entries in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"     {section}: {len(entries)}", file=sys.stderr)
    print(f"  {'='*44}\n", file=sys.stderr)

    # Output or write
    if args.stdout:
        print(changelog)
    else:
        output_path = args.output
        with open(output_path, "w") as f:
            f.write(changelog)
        print(f"  ✅ Written to {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
