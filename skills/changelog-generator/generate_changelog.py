#!/usr/bin/env python3
"""
generate_changelog.py — Generate a structured CHANGELOG.md from git history.

Fetches commits since the last git tag and auto-categorizes them into
Added, Fixed, Changed, Removed, Security, Deprecated, and Other sections.

Follows the Keep a Changelog format (https://keepachangelog.com/en/1.1.0/)
and Semantic Versioning (https://semver.org/spec/v2.0.0.html).

Usage:
    python generate_changelog.py [--repo PATH] [--output CHANGELOG.md] [--tag-pattern v*]
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from collections import OrderedDict
from typing import Optional


# ─── Configuration ──────────────────────────────────────────────────────────

CATEGORY_ORDER = [
    "Breaking Changes",
    "Added",
    "Fixed",
    "Changed",
    "Removed",
    "Security",
    "Deprecated",
    "Documentation",
    "Testing",
    "Other",
]

CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r"^(?P<type>\w+)(\((?P<scope>[^)]*)\))?(?P<breaking>!)?\s*:\s*(?P<message>.+)$",
    re.IGNORECASE,
)

# Map conventional commit types to CHANGELOG categories
TYPE_TO_CATEGORY = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "refactor": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "perf": "Changed",
    "style": "Changed",
    "remove": "Removed",
    "revert": "Removed",
    "delete": "Removed",
    "security": "Security",
    "audit": "Security",
    "deprecate": "Deprecated",
    "deprecated": "Deprecated",
    "docs": "Documentation",
    "documentation": "Documentation",
    "test": "Testing",
    "tests": "Testing",
}

# Keyword-based fallback for non-conventional commits
KEYWORD_CATEGORY = [
    (re.compile(r"^(add|new|create|implement|support|introduce|init)", re.IGNORECASE), "Added"),
    (re.compile(r"^(fix|bug|correct|hotfix|patch|resolve|repair)", re.IGNORECASE), "Fixed"),
    (re.compile(r"^(remove|delete|drop|revert|cleanup|purge)", re.IGNORECASE), "Removed"),
    (re.compile(r"^(update|change|refactor|improve|migrate|redesign|rewrite)", re.IGNORECASE), "Changed"),
    (re.compile(r"^(bump|upgrade|downgrade|bump)", re.IGNORECASE), "Changed"),
    (re.compile(r"^(doc|readme|comment)", re.IGNORECASE), "Documentation"),
    (re.compile(r"^(test|spec)", re.IGNORECASE), "Testing"),
    (re.compile(r"^(sec|audit)", re.IGNORECASE), "Security"),
    (re.compile(r"^(deprecat)", re.IGNORECASE), "Deprecated"),
]


# ─── Git Operations ─────────────────────────────────────────────────────────


def run_git(repo_path: str, args: list[str]) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", "-C", repo_path] + args,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def get_last_tag(repo_path: str, tag_pattern: str) -> Optional[str]:
    """Get the latest git tag matching the pattern, sorted by version."""
    tags = run_git(repo_path, ["tag", "--list", tag_pattern])
    if not tags:
        return None
    tag_list = tags.split("\n")

    try:
        from packaging.version import Version
        tag_list.sort(key=lambda t: Version(t.lstrip("v")), reverse=True)
    except ImportError:
        tag_list.sort(key=lambda t: [int(x) for x in re.findall(r"\d+", t) or [0]], reverse=True)

    return tag_list[0] if tag_list else None


def get_previous_tag(repo_path: str, tag_pattern: str, last_tag: str) -> Optional[str]:
    """Get the tag before the latest one."""
    tags = run_git(repo_path, ["tag", "--list", tag_pattern])
    if not tags:
        return None
    tag_list = tags.split("\n")
    try:
        from packaging.version import Version
        tag_list.sort(key=lambda t: Version(t.lstrip("v")))
    except ImportError:
        tag_list.sort(key=lambda t: [int(x) for x in re.findall(r"\d+", t) or [0]])

    idx = tag_list.index(last_tag)
    if idx > 0:
        return tag_list[idx - 1]
    return None


def get_commits(repo_path: str, commit_range: str) -> list[dict]:
    """Get list of commits in the range."""
    output = run_git(
        repo_path,
        [
            "log",
            commit_range,
            "--pretty=format:%H||%s||%an||%ai",
            "--no-merges",
        ],
    )
    if not output:
        return []

    commits = []
    for line in output.split("\n"):
        if not line.strip():
            continue
        parts = line.split("||", 3)
        if len(parts) < 4:
            continue
        commits.append({
            "hash": parts[0],
            "subject": parts[1],
            "author": parts[2],
            "date": parts[3].split(" ")[0],
        })
    return commits


def get_remote_owner_repo(repo_path: str) -> Optional[str]:
    """Extract owner/repo from git remote URL."""
    remote = run_git(repo_path, ["remote", "get-url", "origin"])
    if not remote:
        return None

    # Handle both HTTPS and SSH formats
    match = re.search(r"github.com[:\/]([^/]+/[^/]+?)(?:\.git)?$", remote)
    if match:
        return match.group(1)
    return None


def bump_patch_version(tag: str) -> str:
    """Bump the patch version of a semver tag."""
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", tag)
    if match:
        major, minor, patch = match.groups()
        return f"v{major}.{minor}.{int(patch) + 1}"
    return tag


# ─── Commit Categorization ──────────────────────────────────────────────────


def categorize_commit(subject: str) -> tuple[str, str, bool]:
    """
    Categorize a commit subject into a CHANGELOG section.

    Returns: (category, cleaned_message, is_breaking)
    """
    match = CONVENTIONAL_COMMIT_PATTERN.match(subject)
    if match:
        commit_type = match.group("type").lower()
        scope = match.group("scope")
        is_breaking = match.group("breaking") == "!" or "BREAKING CHANGE" in subject.upper()
        message = match.group("message").strip()

        if scope:
            message = f"**{scope}:** {message}"

        category = TYPE_TO_CATEGORY.get(commit_type, "Other")
        return category, message, is_breaking

    # Keyword-based fallback
    for pattern, category in KEYWORD_CATEGORY:
        if pattern.match(subject):
            return category, subject, False

    return "Other", subject, False


# ─── CHANGELOG Generation ────────────────────────────────────────────────────


def generate_changelog(
    repo_path: str = ".",
    output_file: str = "CHANGELOG.md",
    tag_pattern: str = "v*",
) -> str:
    """Generate a structured CHANGELOG.md from git history."""

    # Validate git repo
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        # Try gitdir file (submodules)
        if not os.path.isfile(os.path.join(repo_path, ".git")):
            git_dir = run_git(repo_path, ["rev-parse", "--git-dir"])
            if not git_dir:
                print(f"❌ Not a git repository: {repo_path}", file=sys.stderr)
                sys.exit(1)

    # Detect last tag
    last_tag = get_last_tag(repo_path, tag_pattern)
    previous_tag = None

    if last_tag:
        print(f"✓ Last tag: {last_tag}")
        commit_range = f"{last_tag}..HEAD"
        previous_tag = get_previous_tag(repo_path, tag_pattern, last_tag)
    else:
        print(f"! No tags found matching '{tag_pattern}'. Using all commits.")
        commit_range = "HEAD"
        last_tag = "v0.1.0"

    # Get commits
    commits = get_commits(repo_path, commit_range)
    if not commits:
        print(f"! No commits found in range '{commit_range}'", file=sys.stderr)
        # Fallback: try all commits
        output = run_git(repo_path, [
            "log", "--max-count=50",
            "--pretty=format:%H||%s||%an||%ai",
            "--no-merges",
        ])
        if output:
            for line in output.split("\n"):
                if not line.strip():
                    continue
                parts = line.split("||", 3)
                if len(parts) < 4:
                    continue
                commits.append({
                    "hash": parts[0],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3].split(" ")[0],
                })
        if not commits:
            print("❌ No commits found.", file=sys.stderr)
            sys.exit(1)
        print("ℹ Using last 50 commits as fallback")

    print(f"✓ Found {len(commits)} commits")

    # Categorize commits
    categories: "dict[str, list[str]]" = OrderedDict()
    for cat in CATEGORY_ORDER:
        categories[cat] = []

    repo_slug = get_remote_owner_repo(repo_path)

    for c in commits:
        category, message, is_breaking = categorize_commit(c["subject"])
        short_hash = c["hash"][:7]

        if repo_slug:
            link = f"https://github.com/{repo_slug}/commit/{c['hash']}"
            entry = f"- {message} ([{short_hash}]({link}))"
        else:
            entry = f"- {message} ({short_hash})"

        if is_breaking:
            categories["Breaking Changes"].append(
                entry.replace("- ", "- **").replace("([", "** ([")
            )
        else:
            categories[category].append(entry)

    # Determine next version
    next_version = bump_patch_version(last_tag)
    today = datetime.date.today().isoformat()

    # Build CHANGELOG content
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
        f"## [{next_version}] - {today}",
        "",
    ]

    has_content = False
    for cat in CATEGORY_ORDER:
        entries = categories[cat]
        if entries:
            lines.append(f"### {cat}")
            lines.append("")
            lines.extend(entries)
            lines.append("")
            has_content = True

    if not has_content:
        lines.append("_No changes in this release._")
        lines.append("")

    # Add comparison links
    if previous_tag and repo_slug:
        lines.append(
            f"[{next_version}]: https://github.com/{repo_slug}/compare/"
            f"{previous_tag}...{next_version}"
        )
    elif last_tag and repo_slug:
        lines.append(
            f"[{next_version}]: https://github.com/{repo_slug}/compare/"
            f"{last_tag}...{next_version}"
        )

    content = "\n".join(lines) + "\n"

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    abs_path = os.path.abspath(output_file)
    print(f"\n✓ CHANGELOG generated successfully → {abs_path}")

    # Summary
    print(f"\n{'─' * 40}")
    print(f"{'Version:':<20} {next_version}")
    print(f"{'Date:':<20} {today}")
    print(f"{'Total commits:':<20} {len(commits)}")
    for cat in CATEGORY_ORDER:
        count = len(categories[cat])
        if count > 0:
            print(f"{cat + ':':<20} {count}")
    print(f"{'─' * 40}")

    return content


# ─── CLI Entry Point ────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generate_changelog.py\n"
            "  python generate_changelog.py --repo /path/to/repo\n"
            "  python generate_changelog.py --output docs/CHANGELOG.md\n"
            "  python generate_changelog.py --tag-pattern release-*"
        ),
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to git repository (default: current directory)",
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--tag-pattern",
        default="v*",
        help="Git tag pattern to use (default: v*)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="generate_changelog 1.0.0",
    )

    args = parser.parse_args()
    generate_changelog(
        repo_path=os.path.abspath(args.repo),
        output_file=args.output,
        tag_pattern=args.tag_pattern,
    )


if __name__ == "__main__":
    main()
