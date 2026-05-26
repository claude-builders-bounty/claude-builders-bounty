#!/usr/bin/env python3
"""
changelog.py — Auto-generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py [--output CHANGELOG.md] [--since TAG] [--repo PATH]

Requirements:
    - Python 3.8+
    - Git CLI (installed and in PATH)
    - A git repository with at least one tag

This script parses Conventional Commit messages between the last tag and HEAD,
categorizes them, and writes a clean CHANGELOG.md.

Categories:
    feat / feature  →  Added
    fix / bugfix    →  Fixed
    refactor / chore / update / perf → Changed
    remove / delete / deprecate      → Removed
    Everything else →  Changed (fallback)

Bounty: $50 — https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple


# ─── Commit Parsing ────────────────────────────────────────────────────────────

# Conventional Commit type → changelog section mapping
CATEGORY_RULES: Dict[str, str] = OrderedDict({
    "added":    r"^(feat|feature|add|create|implement)",
    "fixed":    r"^(fix|bugfix|bug|hotfix|patch|correct|resolve)",
    "changed":  r"^(refactor|chore|update|perf|improve|migrate|rework|redesign)",
    "removed":  r"^(remove|delete|deprecate|drop|cleanup)",
})


def parse_commit_message(message: str) -> Tuple[str, str]:
    """
    Parse a single commit message into (category, description).

    Uses the Conventional Commit format:
        type(scope): description

    Falls back to the first line if no recognized type is found.
    """
    first_line = message.split("\n")[0].strip()

    for category, pattern in CATEGORY_RULES.items():
        match = re.match(pattern, first_line, re.IGNORECASE)
        if match:
            # Strip the type prefix and optional scope
            description = re.sub(
                r"^" + re.escape(match.group(1)) + r"(\([^)]*\))?:\s*",
                "",
                first_line,
                flags=re.IGNORECASE,
            ).strip()
            if not description:
                description = first_line
            return category.capitalize(), description

    # Fallback: no recognized prefix
    return "Changed", first_line


def get_commits_since_tag(repo_path: str, since_tag: Optional[str] = None) -> Dict[str, List[Tuple[str, str]]]:
    """
    Fetch commits since the last tag and categorize them.

    Returns a dict: {category: [(commit_hash, description), ...]}
    """
    original_dir = os.getcwd()
    os.chdir(repo_path)

    try:
        # Determine the last tag
        if not since_tag:
            try:
                since_tag = subprocess.run(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    capture_output=True, text=True, check=True, timeout=30,
                ).stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                # No tags found — use the full history
                since_tag = None

        # Build git log command
        log_range = f"{since_tag}..HEAD" if since_tag else "--all"
        cmd = [
            "git", "log",
            log_range,
            "--format=%s|||%b|||%H",
            "--no-merges",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        raw_output = result.stdout.strip()

        if not raw_output:
            print("[WARN] No new commits found since the last tag.")
            return {}

        categorized: Dict[str, List[Tuple[str, str]]] = OrderedDict({
            "Added": [],
            "Fixed": [],
            "Changed": [],
            "Removed": [],
        })
        uncategorized: List[Tuple[str, str]] = []

        for line in raw_output.split("\n"):
            parts = line.split("|||")
            if len(parts) < 3:
                continue
            subject = parts[0].strip()
            body = parts[1].strip()
            commit_hash = parts[2].strip()[:7]  # Short hash

            full_message = f"{subject}\n{body}" if body else subject
            category, description = parse_commit_message(full_message)

            if category in categorized:
                categorized[category].append((commit_hash, description))
            else:
                uncategorized.append((commit_hash, description))

        # Append uncategorized to "Changed"
        categorized["Changed"].extend(uncategorized)

        return categorized
    finally:
        os.chdir(original_dir)


def create_changelog(
    categorized: Dict[str, List[Tuple[str, str]]],
    repo_path: str,
    since_tag: Optional[str] = None,
) -> str:
    """
    Build the full CHANGELOG.md content from categorized commits.
    """
    today = datetime.date.today().isoformat()
    version_label = f"[Unreleased]" if not since_tag else f"[{since_tag} → HEAD]"
    lines = [
        "# Changelog",
        "",
        f"## {version_label} — {today}",
        "",
    ]

    has_content = any(commits for commits in categorized.values())

    if not has_content:
        lines.append("_No significant changes._")
        lines.append("")
        return "\n".join(lines)

    for category in ["Added", "Fixed", "Changed", "Removed"]:
        commits = categorized.get(category, [])
        if not commits:
            continue
        lines.append(f"### {category}")
        for hash_val, desc in commits:
            # Capitalize first letter of description
            desc = desc[0].upper() + desc[1:] if desc else desc
            lines.append(f"- {desc} ({hash_val})")
        lines.append("")

    return "\n".join(lines)


def write_changelog(content: str, output_path: str) -> None:
    """Write the changelog content to the specified file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[DONE] CHANGELOG written to: {output_path}")


# ─── CLI ───────────────────────────────────────────────────────────────────────

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python changelog.py\n"
            "  python changelog.py --output docs/CHANGELOG.md\n"
            "  python changelog.py --since v1.0.0\n"
            "  python changelog.py --repo /path/to/project\n"
        ),
    )
    parser.add_argument(
        "--output", "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--since", "-s",
        default=None,
        help="Tag to start from (default: auto-detect latest tag)",
    )
    parser.add_argument(
        "--repo", "-r",
        default=".",
        help="Path to git repository (default: current directory)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    repo_path = os.path.abspath(args.repo)

    # Verify it's a git repo
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=repo_path,
            capture_output=True,
            check=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"[ERROR] '{repo_path}' is not a git repository.", file=sys.stderr)
        return 1

    print(f"[SCAN] Scanning repository: {repo_path}")
    if args.since:
        print(f"[TAG] Using tag: {args.since}")

    categorized = get_commits_since_tag(repo_path, args.since)

    if not categorized:
        print("[INFO] No commits found. Nothing to generate.")
        return 0

    # Count total commits
    total = sum(len(commits) for commits in categorized.values())
    print(f"[OK] Found {total} commit(s)")

    for cat, commits in categorized.items():
        if commits:
            print(f"  {cat}: {len(commits)}")

    changelog_content = create_changelog(categorized, repo_path, args.since)
    output_path = os.path.join(repo_path, args.output)
    write_changelog(changelog_content, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
