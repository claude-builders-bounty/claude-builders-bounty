#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.

Categorizes commits into: Added, Fixed, Changed, Removed.
Fetches commits since the last git tag (or all history if no tag exists).

Usage:
    python3 generate_changelog.py                    # generate CHANGELOG.md
    python3 generate_changelog.py --since v1.0.0     # commits since tag
    python3 generate_changelog.py --output FILE.md   # custom output path
    python3 generate_changelog.py --all              # all history (no tag filter)
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# Conventional commit categorization
CATEGORY_PATTERNS = {
    "Added": [
        r"^feat[\(:]",
        r"^add[\(:]",
        r"^new[\(:]",
        r"^implement[\(:]",
        r"^introduce[\(:]",
        r"^create[\(:]",
    ],
    "Fixed": [
        r"^fix[\(:]",
        r"^bug[\(:]",
        r"^bugfix[\(:]",
        r"^patch[\(:]",
        r"^resolve[\(:]",
        r"^repair[\(:]",
    ],
    "Changed": [
        r"^change[\(:]",
        r"^update[\(:]",
        r"^modify[\(:]",
        r"^refactor[\(:]",
        r"^improve[\(:]",
        r"^enhance[\(:]",
        r"^optimize[\(:]",
        r"^perf[\(:]",
        r"^style[\(:]",
        r"^docs?[\(:]",
        r"^chore[\(:]",
        r"^build[\(:]",
        r"^ci[\(:]",
        r"^test[\(:]",
    ],
    "Removed": [
        r"^remove[\(:]",
        r"^delete[\(:]",
        r"^drop[\(:]",
        r"^deprecate[\(:]",
        r"^revert[\(:]",
    ],
}

# Breaking change indicator
BREAKING_RE = r"^[a-z]+(?:\([^)]+\))?!:"


def run_git(*args):
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"git error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("git not found in PATH", file=sys.stderr)
        sys.exit(1)


def get_latest_tag():
    """Get the most recent git tag, or None if no tags exist."""
    tag = run_git("describe", "--tags", "--abbrev=0")
    return tag if tag else None


def get_commits(since_tag=None, all_history=False):
    """
    Get commits with hash, date, subject, body.
    Format: hash|date|subject
    """
    if all_history or not since_tag:
        range_ref = "HEAD"
    else:
        range_ref = f"{since_tag}..HEAD"

    fmt = "%h|%ad|%s|%b"
    date_fmt = "iso"
    output = run_git(
        "log",
        range_ref,
        f"--pretty=format:{fmt}",
        f"--date={date_fmt}",
        "--no-merges",
    )
    return output


def categorize_commit(subject):
    """
    Categorize a commit subject into Added/Fixed/Changed/Removed.
    Returns (category, is_breaking).
    """
    is_breaking = bool(re.match(BREAKING_RE, subject))
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, subject, re.IGNORECASE):
                return category, is_breaking
    # Default to Changed
    return "Changed", is_breaking


def strip_prefix(subject):
    """Remove conventional commit prefix (feat:, fix:, etc.) for cleaner display."""
    return re.sub(r"^[a-z]+(?:\([^)]+\))?!?:\s*", "", subject, flags=re.IGNORECASE).strip()


def parse_commits(commits_text):
    """Parse raw git log output into structured commits."""
    commits = []
    for line in commits_text.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) < 3:
            continue
        commit = {
            "hash": parts[0],
            "date": parts[1],
            "subject": parts[2],
            "body": parts[3] if len(parts) > 3 else "",
        }
        commits.append(commit)
    return commits


def generate_changelog(commits, version="Unreleased", since_tag=None):
    """Generate Markdown changelog content from commits."""
    categorized = defaultdict(list)

    for commit in commits:
        category, breaking = categorize_commit(commit["subject"])
        clean_subject = strip_prefix(commit["subject"])
        if breaking:
            clean_subject = f"⚠️ **BREAKING**: {clean_subject}"
        categorized[category].append(clean_subject)

    # Header
    today = datetime.now().strftime("%Y-%m-%d")
    if since_tag:
        header = f"## [{version}] - {today}\n\n"
    else:
        header = f"## [{version}] - {today}\n\n"

    sections = []
    # Ordered: Added, Changed, Fixed, Removed
    for category in ["Added", "Changed", "Fixed", "Removed"]:
        items = categorized.get(category, [])
        if items:
            section = f"### {category}\n\n"
            for item in items:
                section += f"- {item}\n"
            sections.append(section)

    if not sections:
        return header + "_No changes._\n"

    return header + "\n".join(sections) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history"
    )
    parser.add_argument(
        "--since",
        help="Generate from this tag (default: latest tag)",
        default=None,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all history (ignore tags)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--version",
        default="Unreleased",
        help="Version label for this changelog entry",
    )

    args = parser.parse_args()

    # Determine starting point
    since_tag = args.since
    if not since_tag and not args.all:
        since_tag = get_latest_tag()
        if since_tag:
            print(f"Found latest tag: {since_tag}", file=sys.stderr)
        else:
            print("No tags found, including all history", file=sys.stderr)

    # Get commits
    commits_text = get_commits(since_tag=since_tag, all_history=args.all)
    commits = parse_commits(commits_text)

    if not commits:
        print("No commits found in range", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(commits)} commits", file=sys.stderr)

    # Generate changelog
    content = generate_changelog(commits, version=args.version, since_tag=since_tag)

    # Prepend header if file doesn't exist
    output_path = Path(args.output)
    if not output_path.exists():
        full_content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        full_content += content
    else:
        # Insert new entry after header
        existing = output_path.read_text(encoding="utf-8")
        # Find first ## (or end of header)
        match = re.search(r"^## ", existing, re.MULTILINE)
        if match:
            full_content = existing[:match.start()] + content + existing[match.start():]
        else:
            full_content = existing + "\n" + content

    output_path.write_text(full_content, encoding="utf-8")
    print(f"Changelog written to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
