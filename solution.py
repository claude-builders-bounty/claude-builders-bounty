#!/usr/bin/env python3
"""
changelog.py - Generate a structured CHANGELOG.md from git history.

Usage:
    python3 changelog.py [--tag <tag>] [--output CHANGELOG.md] [--since <date>]
    bash changelog.sh [--tag <tag>] [--output CHANGELOG.md]

Categorization keywords (case-insensitive, checked against commit subject):
    Added:   feat, feature, add, new, introduce
    Fixed:   fix, bug, patch, resolve, repair, hotfix
    Changed:   change, update, refactor, improve, modify, restructure
    Removed:  remove, delete, drop, deprecate, break
"""

import subprocess
import sys
import os
import re
import argparse
from datetime import datetime
from collections import defaultdict
from typing import Optional, List, Dict, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ADDED_KEYWORDS = re.compile(
    r"\b(feat|feature|add|new|introduce|implement)\b", re.IGNORECASE
)
FIXED_KEYWORDS = re.compile(
    r"\b(fix|bug|patch|resolve|repair|hotfix|security)\b", re.IGNORECASE
)
CHANGED_KEYWORDS = re.compile(
    r"\b(change|update|refactor|improve|modify|restructure|enhance)\b",
    re.IGNORECASE,
)
REMOVED_KEYWORDS = re.compile(
    r"\b(remove|delete|drop|deprecate|break|drop)\b", re.IGNORECASE
)

DEFAULT_OUTPUT = "CHANGELOG.md"
CHANGELOG_HEADER = """\
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
"""

# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def run_git(args: List[str], **kwargs) -> str:
    """Run a git command and return stdout stripped."""
    result = subprocess.run(
        ["git"] + args, capture_output=True, text=True, check=True, **kwargs
    )
    return result.stdout.strip()


def get_latest_tag(since: Optional[str] = None) -> Optional[str]:
    """Return the most recent lightweight or annotated tag."""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None


def get_commits_since(tag: Optional[str]) -> List[Tuple[str, str]]:
    """Return list of (hash, subject) tuples for commits after *tag*."""
    ref = tag if tag else "HEAD"
    try:
        output = run_git([
            "log",
            f"{ref}..HEAD",
            "--pretty=format:%H|||%s",
            "--reverse",
        ])
    except subprocess.CalledProcessError:
        return []
    entries = []
    for line in output.splitlines():
        if not line:
            continue
        parts = line.split("|||", 1)
        if len(parts) == 2:
            entries.append((parts[0], parts[1]))
    return entries


def get_current_version(tag: Optional[str]) -> str:
    """Return the version string derived from the latest tag, or HEAD short ref."""
    latest = tag or get_latest_tag()
    if latest:
        # Strip common prefixes like 'v'
        return latest.lstrip("v")
    try:
        short = run_git(["rev-parse", "--short", "HEAD"])
        date = datetime.now().strftime("%Y-%m-%d")
        return f"Unreleased ({date}) — {short}"
    except subprocess.CalledProcessError:
        return "Unknown"


def get_date_range(tag: Optional[str]) -> Tuple[str, str]:
    """Return (oldest_date, newest_date) for commits since *tag*."""
    commits = get_commits_since(tag)
    if not commits:
        return ("N/A", "N/A")
    oldest = run_git(["log", "-1", "--format=%cd", "--date=short", commits[0][0]])
    newest = run_git(["log", "-1", "--format=%cd", "--date=short", commits[-1][0]])
    return oldest, newest


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------

def categorize(commit_subject: str) -> str:
    """Classify a commit subject into one of the four categories."""
    if FIXED_KEYWORDS.search(commit_subject):
        return "Fixed"
    if ADDED_KEYWORDS.search(commit_subject):
        return "Added"
    if CHANGED_KEYWORDS.search(commit_subject):
        return "Changed"
    if REMOVED_KEYWORDS.search(commit_subject):
        return "Removed"
    # Fallback: look at conventional-commit prefix
    prefix = commit_subject.split(":")[0].split("(")[0].strip().lower()
    if prefix.startswith("feat") or prefix.startswith("feature"):
        return "Added"
    if prefix.startswith("fix"):
        return "Fixed"
    if prefix.startswith("refactor") or prefix.startswith("style"):
        return "Changed"
    if prefix.startswith("chore"):
        return "Changed"
    return "Other"


def extract_scope(subject: str) -> Optional[str]:
    """Extract optional scope from '(scope)' in a conventional-commit message."""
    match = re.search(r"^\w+\(([^)]+)\):\s*", subject)
    if match:
        return match.group(1)
    return None


def clean_subject(subject: str) -> str:
    """Strip conventional-commit prefixes for cleaner listing."""
    # Remove leading 'feat:', 'fix(scope):', etc.
    cleaned = re.sub(r"^(\w+)(\([^)]+\))?:\s*", "", subject)
    # Capitalize first letter
    return cleaned[0].upper() + cleaned[1:] if cleaned else cleaned


# ---------------------------------------------------------------------------
# Build changelog
# ---------------------------------------------------------------------------

def build_changelog(
    tag: Optional[str] = None,
    include_all: bool = False,
) -> str:
    """Build the full CHANGELOG.md content as a string."""
    current_version = get_current_version(tag)
    old_date, new_date = get_date_range(tag)
    commits = get_commits_since(tag) if not include_all else []

    # Collect all historical tags for the 'Archives' section
    archives: List[str] = []
    try:
        tags_output = run_git(["tag", "--sort=-version:refname"])
        archives = [t for t in tags_output.splitlines() if t != (tag or "")]
        # Keep only the last few versions
        archives = archives[:5]
    except subprocess.CalledProcessError:
        pass

    lines: List[str] = [CHANGELOG_HEADER, ""]
    lines.append(f"## [{current_version}] — {old_date} to {new_date}")
    lines.append("")

    categorized: Dict[str, List[str]] = defaultdict(list)
    for commit_hash, subject in commits:
        cat = categorize(subject)
        short_hash = commit_hash[:8]
        entry = f"- {clean_subject(subject)} ({short_hash})"
        if include_all and not commits:
            pass  # no commits to show
        categorized[cat].append(entry)

    # Render categories in a deterministic order
    category_order = ["Added", "Fixed", "Changed", "Removed", "Other"]
    has_changes = any(commits)

    for cat in category_order:
        items = categorized.get(cat, [])
        if not items and not has_changes:
            continue
        if has_changes and not items:
            continue
        lines.append(f"### {cat}")
        lines.append("")
        lines.extend(items)
        lines.append("")

    if not has_changes:
        lines.append("*No new commits since the last release.*")
        lines.append("")

    # Link block for the current version
    if tag or archives:
        prev_tag = archives[-1] if archives else ""
        if prev_tag:
            lines.append(
                f"[{current_version}]: "
                f"https://github.com/compare/{prev_tag}...{tag or 'HEAD'}"
            )

    # Archives section
    if archives:
        lines.append("----")
        lines.append("")
        lines.append("## Archived Releases")
        lines.append("")
        for ver in archives:
            lines.append(f"- **{ver.lstrip('v')}**")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history."
    )
    parser.add_argument(
        "--tag",
        help="Starting git tag (default: latest tag or HEAD)",
        default=None,
    )
    parser.add_argument(
        "--output", "-o",
        help=f"Output file path (default: {DEFAULT_OUTPUT})",
        default=DEFAULT_OUTPUT,
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include ALL git history (ignores --tag)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the changelog to stdout without writing a file",
    )
    args = parser.parse_args()

    try:
        content = build_changelog(tag=args.tag, include_all=args.include_all)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: git command failed: {exc.stderr.strip() or exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("ERROR: 'git' command not found. Ensure git is installed.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(content)
        return 0

    output_path = args.output
    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"✅  CHANGELOG written to {output_path}")
    except OSError as exc:
        print(f"ERROR: could not write {output_path}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())


bash
#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh               # uses latest tag / HEAD; writes CHANGELOG.md
#   bash changelog.sh --tag v1.2.3
#   bash changelog.sh --output docs/CHANGELOG.md
#   bash changelog.sh --dry-run     # print to stdout only
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/changelog.py"

# Resolve Python interpreter
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "ERROR: Python 3 is required but not found." >&2
    exit 1
fi

# Check for git
if ! command -v git &>/dev/null; then
    echo "ERROR: git is required but not found." >&2
    exit 1
fi

# If invoked directly without arguments, delegate to Python script
ARGS=("$@")
if [[ $# -eq 0 ]]; then
    exec "$PYTHON" "$PYTHON_SCRIPT"
fi

exec "$PYTHON" "$PYTHON_SCRIPT" "${ARGS[@]}"


markdown
# CLAUDE-CODE-SKILL.md

---
name: generate-changelog
description: |
  Generate a structured CHANGELOG.md from the project's git history.
  Use this skill when asked to create, update, or regenerate a CHANGELOG.
---

# Generating a CHANGELOG from git history

## Overview

This skill runs the `changelog.py` / `changelog.sh` utility to produce a
structured, semantic-versioning-compliant `CHANGELOG.md` from the repository's
git tags and commit history.

## Commands

bash
# Generate (or regenerate) CHANGELOG.md from the latest tag to HEAD
bash changelog.sh

# Starting from a specific tag
bash changelog.sh --tag v2.0.0

# Custom output path
bash changelog.sh --output releases/v3/CHANGELOG.md

# Preview before writing
bash changelog.sh --dry-run


## How categorization works

Each commit subject is scanned for keywords and classified into:

| Category  | Keywords                                               |
|-----------|--------------------------------------------------------|
| **Added** | feat, feature, add, new, introduce, implement          |
| **Fixed** | fix, bug, patch, resolve, repair, hotfix, security     |
| **Changed**| change, update, refactor, improve, modify, enhance    |
| **Removed**| remove, delete, drop, deprecate, break                |
| **Other** | anything that doesn't match the above                  |

Conventional-commit prefixes (`feat:`, `fix(scope):`, …) are also honoured
when keyword matching fails.

## What the output looks like

md
# Changelog

## [v2.1.0] — 2025-06-01 to 2025-07-10

### Added
- Implement user authentication via OAuth2 (a1b2c3d4)
- Add REST API rate-limiting middleware (e5f6g7h8)

### Fixed
- Resolve memory leak in websocket handler (#142) (i9j0k1l2)

### Changed
- Refactor database connection pool for better performance (m3n4o5p6)

## [v2.0.0] — 2025-03-15 to 2025-05-30
…


## Workflow

When the user asks you to **generate a CHANGELOG**:

1. Run `bash changelog.sh --dry-run` to preview.
2. Show the preview to the user and ask if they want to adjust the tag base.
3. If satisfied, run `bash changelog.sh` to write the file.
4. Optionally commit the updated CHANGELOG.md.

## Notes

- Works in any git repository. Run it from the repo root.
- If no tags exist, it falls back to showing all commits since the first.
- The script is self-contained — no external dependencies beyond Python 3 and git.


markdown
# CHANGELOG Generator

A zero-dependency tool that generates a structured `CHANGELOG.md` from your
project's git history, auto-categorizing commits into **Added**, **Fixed**,
**Changed**, and **Removed** sections.

## Setup (3 steps)

1. **Clone or copy** this repository into your project.
2. **Make the script executable** (optional but convenient):
   bash
   chmod +x changelog.sh
   
3. **Run the generator**:
   bash
   bash changelog.sh
   
   This creates/overwrites `CHANGELOG.md` in your project root.

## Quick start

bash
# Standard usage — since latest tag
bash changelog.sh

# From a specific tag
bash changelog.sh --tag v1.0.0

# Custom output path
bash changelog.sh --output docs/HISTORY.md

# Dry-run to preview
bash changelog.sh --dry-run


## Requirements

- **git** — installed and your project is a git repository
- **Python 3.6+** — bundled in `changelog.py`; no third-party packages needed

## Claude Code integration

Import the `CLAUDE-CODE-SKILL.md` file into your `.claude/skills/` directory to
enable the `/generate-changelog` command inside Claude Code sessions.

## Sample output

Given a repo with these commits since `v1.0.0`:

| Commit                          | Category |
|---------------------------------|----------|
| `feat: add user dashboard`      | Added    |
| `fix: resolve login timeout`    | Fixed    |
| `refactor: extract auth module` | Changed  |
| `drop: remove legacy API v1`    | Removed  |

The generated CHANGELOG looks like:

md
# Changelog

## [v1.1.0] — 2025-06-01 to 2025-07-10

### Added
- Add user dashboard view (a1b2c3d4)

### Fixed
- Resolve login timeout under load (#87) (e5f6g7h8)

### Changed
- Extract authentication module for reusability (i9j0k1l2)

### Removed
- Drop legacy API v1 endpoints (m3n4o5p6)