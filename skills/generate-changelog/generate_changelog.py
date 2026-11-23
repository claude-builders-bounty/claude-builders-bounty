#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Follows the Keep a Changelog standard (https://keepachangelog.com/).
Categorizes commits into: Added, Fixed, Changed, Removed.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

# Categorization patterns matching conventional commit types and common prefixes
CATEGORY_PATTERNS = {
    "Added": re.compile(
        r"^(feat|feature|add|added|create|created|new)(\(.*?\))?:\s*|^(add|added|create|created)\b",
        re.IGNORECASE,
    ),
    "Fixed": re.compile(
        r"^(fix|fixed|bug|bugfix|patch|hotfix|resolve|resolved|close|closed)(\(.*?\))?:\s*|^(fix|fixed|resolve|resolved)\b",
        re.IGNORECASE,
    ),
    "Removed": re.compile(
        r"^(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)(\(.*?\))?:\s*|^(remove|removed|delete|deleted)\b",
        re.IGNORECASE,
    ),
    "Changed": re.compile(
        r"^(refactor|change|changed|update|updated|perf|performance|style|docs|chore|ci|build|test)(\(.*?\))?:\s*|^(refactor|update|updated|change|changed)\b",
        re.IGNORECASE,
    ),
}


@dataclass
class Commit:
    hash: str
    short_hash: str
    author: str
    date: str
    subject: str
    category: str
    clean_message: str


def run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return its trimmed stdout."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_latest_tag(cwd: str | None = None) -> str | None:
    """Find the latest git tag reachable from HEAD, or None if no tags exist."""
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd)
        return tag if tag else None
    except subprocess.CalledProcessError:
        return None


def list_all_tags(cwd: str | None = None) -> list[str]:
    """Return all tags sorted by commit date descending."""
    try:
        output = run_git(
            ["tag", "--sort=-creatordate"],
            cwd=cwd,
        )
        return [t.strip() for t in output.splitlines() if t.strip()]
    except subprocess.CalledProcessError:
        return []


def classify_commit(message: str) -> tuple[str, str]:
    """Determine category and cleaned message for a commit subject."""
    clean = message.strip()

    for category in ("Added", "Fixed", "Removed", "Changed"):
        pattern = CATEGORY_PATTERNS[category]
        match = pattern.match(clean)
        if match:
            # Strip the conventional commit prefix if present
            trimmed = clean[match.end():].strip()
            if trimmed:
                # Capitalize first letter of cleaned message
                clean = trimmed[0].upper() + trimmed[1:]
            return category, clean

    # Default fallback
    return "Changed", clean


def fetch_commits(revision_range: str | None = None, cwd: str | None = None) -> list[Commit]:
    """Fetch commits in the given revision range (e.g. 'v1.0.0..HEAD' or None for all)."""
    git_args = [
        "log",
        "--pretty=format:%H%x1f%h%x1f%an%x1f%ad%x1f%s",
        "--date=short",
    ]
    if revision_range:
        git_args.append(revision_range)

    try:
        output = run_git(git_args, cwd=cwd)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to fetch git commits: {e.stderr.strip()}") from e

    commits: list[Commit] = []
    if not output:
        return commits

    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) != 5:
            continue
        full_hash, short_hash, author, date, subject = parts
        cat, clean_msg = classify_commit(subject)
        commits.append(
            Commit(
                hash=full_hash,
                short_hash=short_hash,
                author=author,
                date=date,
                subject=subject,
                category=cat,
                clean_message=clean_msg,
            )
        )
    return commits


def format_release_section(
    version_title: str,
    date_str: str,
    commits: list[Commit],
) -> str:
    """Format a single release entry following Keep a Changelog."""
    grouped: dict[str, list[Commit]] = defaultdict(list)
    for c in commits:
        grouped[c.category].append(c)

    lines: list[str] = [f"## [{version_title}] - {date_str}"]

    if not commits:
        lines.append("")
        lines.append("No changes recorded.")
        lines.append("")
        return "\n".join(lines)

    for category in CATEGORIES:
        items = grouped.get(category, [])
        if items:
            lines.append("")
            lines.append(f"### {category}")
            for item in items:
                lines.append(f"- {item.clean_message} (`{item.short_hash}`)")

    lines.append("")
    return "\n".join(lines)


CHANGELOG_HEADER = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""


def render_full_changelog(release_sections: list[str]) -> str:
    """Combine header and release sections."""
    return CHANGELOG_HEADER + "\n".join(release_sections).strip() + "\n"


def prepend_to_existing(existing_content: str, new_release_section: str) -> str:
    """Prepend a new release section right below the header in an existing CHANGELOG.md."""
    # Find where the first release entry (e.g. '## [') begins
    match = re.search(r"^##\s+\[", existing_content, flags=re.MULTILINE)
    if match:
        header = existing_content[:match.start()]
        rest = existing_content[match.start():]
        return header + new_release_section.strip() + "\n\n" + rest
    else:
        # If no previous release sections found, append under header
        if existing_content.strip():
            return existing_content.rstrip() + "\n\n" + new_release_section.strip() + "\n"
        return render_full_changelog([new_release_section])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate-changelog",
        description="Generate a Keep a Changelog formatted CHANGELOG.md from git history.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="CHANGELOG.md",
        help="Path to output file (default: CHANGELOG.md in current directory).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print changelog directly to stdout instead of writing to a file.",
    )
    parser.add_argument(
        "--version-title",
        "-v",
        default=None,
        help="Title for this release (default: 'Unreleased' or the current tag).",
    )
    parser.add_argument(
        "--since-tag",
        help="Explicit tag to collect commits since (default: latest tag reachable).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate changelog for all commits from the beginning of repository history.",
    )
    parser.add_argument(
        "--prepend",
        action="store_true",
        help="Prepend newly generated release section to existing CHANGELOG.md.",
    )
    return parser


def main(argv: list[str] | None = None, cwd: str | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    today = datetime.date.today().isoformat()
    latest_tag = args.since_tag or (None if args.all else get_latest_tag(cwd=cwd))

    if latest_tag:
        rev_range = f"{latest_tag}..HEAD"
        version_name = args.version_title or "Unreleased"
    else:
        rev_range = None
        version_name = args.version_title or "Unreleased"

    commits = fetch_commits(rev_range, cwd=cwd)
    release_block = format_release_section(version_name, today, commits)

    if args.stdout:
        sys.stdout.write(release_block)
        return 0

    output_path = Path(args.output if os.path.isabs(args.output) else (Path(cwd or ".") / args.output))

    if args.prepend and output_path.exists():
        existing = output_path.read_text(encoding="utf-8")
        updated = prepend_to_existing(existing, release_block)
        output_path.write_text(updated, encoding="utf-8")
    else:
        full_content = render_full_changelog([release_block])
        output_path.write_text(full_content, encoding="utf-8")

    print(f"Generated changelog with {len(commits)} commit(s) -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
