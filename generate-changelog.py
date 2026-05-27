#!/usr/bin/env python3
"""
Generate structured CHANGELOG.md from git history since the last tag.

Usage:
    python3 generate-changelog.py [--repo PATH] [--output FILE] [--unreleased-only]

Features:
    - Fetches commits since the most recent git tag (or all history if no tags)
    - Auto-categorizes commits into: Added | Fixed | Changed | Removed
    - Conventional-commit aware: feat/fix/refactor/perf/docs/style/test/chore/build/ci
    - Outputs Keep-a-Changelog formatted CHANGELOG.md
    - Idempotent: safe to run multiple times
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── Conventional Commit type → changelog category mapping ──────────────
TYPE_MAP: dict[str, str] = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Performance",
    "refactor": "Changed",
    "docs": "Docs",
    "style": "Style",
    "test": "Tests",
    "chore": "Chore",
    "build": "Build",
    "ci": "CI",
}

# Types that are considered breaking by default
BREAKING_TYPES = {"fix", "refactor", "perf", "feat"}


@dataclass
class Commit:
    hash: str
    subject: str
    body: str = ""
    commit_type: str = ""
    scope: str = ""
    is_breaking: bool = False
    date: str = ""


def _run_git(*args: str, cwd: Optional[Path] = None) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def get_last_tag(cwd: Optional[Path] = None) -> Optional[str]:
    """Return the most recent git tag, or None if no tags exist."""
    tag = _run_git("describe", "--tags", "--abbrev=0", cwd=cwd)
    return tag if tag else None


def get_commits_since(since_ref: Optional[str], cwd: Optional[Path] = None) -> list[Commit]:
    """Parse git log into Commit objects since `since_ref` (or all time)."""
    range_spec = f"{since_ref}..HEAD" if since_ref else "HEAD"
    # Format: hash|subject|body (separator records)
    fmt = "%H|%s|%b%%COMMIT_END%%"
    raw = _run_git(
        "log", f"--format={fmt}", range_spec, "--no-merges", cwd=cwd
    )
    if not raw:
        return []

    commits: list[Commit] = []
    for block in raw.split("%%COMMIT_END%%"):
        block = block.strip()
        if not block or "|" not in block:
            continue
        parts = block.split("|", 2)
        h, subject = parts[0], parts[1]
        body = parts[2] if len(parts) > 2 else ""

        # Parse conventional commit
        ctype, scope, is_breaking = parse_conventional(subject + "\n" + body)

        # Get commit date
        date_raw = _run_git("log", "-1", "--format=%cI", h, cwd=cwd) or ""

        commits.append(
            Commit(
                hash=h[:8],
                subject=subject,
                body=body,
                commit_type=ctype,
                scope=scope,
                is_breaking=is_breaking,
                date=date_raw,
            )
        )
    return commits


def parse_conventional(text: str) -> tuple[str, str, bool]:
    """
    Parse conventional commit prefix.
    Returns (type, scope, is_breaking).
    """
    m = re.match(r"^(\w+)(\([^)]+\))?!?:\s", text, re.MULTILINE)
    if not m:
        return ("", "", False)

    ctype = m.group(1).lower()
    scope = m.group(2)[1:-1] if m.group(2) else ""  # strip parens
    has_exclamation = "!" in (m.group(2) or "")

    # Also check body for BREAKING CHANGE
    is_breaking = has_exclamation or bool(re.search(r"BREAKING\s+CHANGE:", text, re.I))
    return (ctype, scope, is_breaking)


def categorize(commit: Commit) -> str:
    """Map commit type to human-readable changelog category."""
    if not commit.commit_type:
        return "Other"
    return TYPE_MAP.get(commit.commit_type, "Other")


def format_entry(commit: Commit) -> str:
    """Format a single commit as a markdown list item."""
    line = f"- {commit.subject} ({commit.hash})"
    if commit.scope:
        line = f"- **{commit.scope}:** {commit.subject} ({commit.hash})"
    if commit.is_breaking:
        line += " **⚠️ BREAKING**"
    return line


def generate_changelog(commits: list[Commit], unreleased_only: bool = False) -> str:
    """Build full CHANGELOG.md content from categorized commits."""
    lines: list[str] = []

    # Header
    lines.append("# Changelog")
    lines.append("")
    lines.append("All notable changes to this project will be documented in this file.")
    lines.append("")
    lines.append("The format is based on [Keep a Changelog](https://keepachangelog.com/),")
    lines.append("and this project adheres to [Semantic Versioning](https://semver.org/).")
    lines.append("")

    if not commits:
        lines.append("## Unreleased")
        lines.append("")
        lines.append("No changes yet.")
        return "\n".join(lines)

    # Group commits by category
    categories: dict[str, list[Commit]] = {}
    for c in commits:
        cat = categorize(c)
        categories.setdefault(cat, []).append(c)

    # Category order (most important first)
    order = ["Added", "Fixed", "Changed", "Performance", "Removed", "Security",
             "Docs", "Tests", "Style", "Chore", "Build", "CI", "Other"]

    # Unreleased section
    lines.append("## Unreleased")
    lines.append("")

    # Breaking changes first
    breaking = [c for c in commits if c.is_breaking]
    if breaking:
        lines.append("### ⚠️ Breaking Changes")
        lines.append("")
        for c in breaking:
            lines.append(format_entry(c))
        lines.append("")

    # Normal categories
    for cat in order:
        if cat not in categories or cat in {"Other"}:
            continue
        cat_commits = categories[cat]
        # Skip breaking ones already shown
        cat_commits = [c for c in cat_commits if not c.is_breaking]
        if not cat_commits:
            continue

        lines.append(f"### {cat}")
        lines.append("")
        for c in cat_commits:
            lines.append(format_entry(c))
        lines.append("")

    # Other bucket
    if "Other" in categories:
        other = [c for c in categories["Other"] if not c.is_breaking]
        if other:
            lines.append("### Other")
            lines.append("")
            for c in other:
                lines.append(format_entry(c))
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from git history since last tag."
    )
    parser.add_argument(
        "--repo", type=Path, default=None,
        help="Path to git repository (default: current directory)",
    )
    parser.add_argument(
        "--output", type=str, default="CHANGELOG.md",
        help="Output filename (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--unreleased-only", action="store_true",
        help="Only output the Unreleased section (no header boilerplate)",
    )
    args = parser.parse_args()

    repo_path = args.repo.resolve() if args.repo else Path.cwd()

    # Verify it's a git repo
    if not (repo_path / ".git").exists():
        print(f"Error: {repo_path} is not a git repository.", file=sys.stderr)
        return 1

    last_tag = get_last_tag(repo_path)
    if last_tag:
        print(f"📌 Last tag: {last_tag} — scanning commits since then...")
    else:
        print("⚠️  No git tags found — scanning entire history...")

    commits = get_commits_since(last_tag, repo_path)
    print(f"📝 Found {len(commits)} commits.")

    if args.unreleased_only:
        # Output just the entries without header
        content = generate_changelog(commits, unreleased_only=True)
        # Strip header
        idx = content.find("## Unreleased")
        if idx >= 0:
            print(content[idx:])
        else:
            print(content)
    else:
        content = generate_changelog(commits)
        out_path = repo_path / args.output
        out_path.write_text(content, encoding="utf-8")
        print(f"✅ Wrote {out_path} ({len(content)} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
