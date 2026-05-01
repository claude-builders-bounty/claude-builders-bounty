#!/usr/bin/env python3
"""
generate-changelog.py — Generate CHANGELOG.md from Git History

Parses conventional commits and generates a structured changelog
categorized into: Added / Fixed / Changed / Removed

Usage:
  python3 generate-changelog.py                    # Full changelog
  python3 generate-changelog.py --since v1.0.0     # From tag to HEAD
  python3 generate-changelog.py --unreleased       # Since last tag
  python3 generate-changelog.py -o CHANGELOG.md    # Write to file

Requires: git, Python 3.9+
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from typing import Optional

# ─── Configuration ────────────────────────────────────────────────────────────

COMMIT_PATTERN = re.compile(
    r"^(?P<type>[a-zA-Z]+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<description>.+)$"
)

# ─── Git Helpers ──────────────────────────────────────────────────────────────

def run_git(args: list[str]) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            print("Error: Not a git repository", file=sys.stderr)
            sys.exit(1)
        return ""
    except FileNotFoundError:
        print("Error: git not found", file=sys.stderr)
        sys.exit(1)


def get_latest_tag() -> Optional[str]:
    """Get the most recent tag."""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except Exception:
        return None


def get_commits(ref_range: Optional[str] = None) -> list[dict]:
    """Get commits with hash and subject."""
    fmt = "%H|%s"
    if ref_range:
        log = run_git(["log", ref_range, f"--pretty=format:{fmt}", "--no-merges"])
    else:
        log = run_git(["log", f"--pretty=format:{fmt}", "--no-merges"])

    if not log:
        return []

    commits = []
    for line in log.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|", 1)
        if len(parts) >= 2:
            commits.append({"hash": parts[0], "subject": parts[1]})
    return commits


# ─── Commit Parsing ───────────────────────────────────────────────────────────

def classify_commit_type(commit_type: str) -> str:
    """Map conventional commit type to changelog category."""
    mapping = {
        "feat": "Added",
        "fix": "Fixed",
        "remove": "Removed",
    }
    return mapping.get(commit_type.lower(), "Changed")


def parse_commit(subject: str) -> Optional[dict]:
    """Parse a conventional commit message."""
    match = COMMIT_PATTERN.match(subject)
    if not match:
        return None
    return {
        "type": match.group("type").lower(),
        "scope": match.group("scope") or "",
        "description": match.group("description"),
    }


def format_entry(scope: str, description: str, commit_hash: str) -> str:
    """Format a changelog entry."""
    short_hash = commit_hash[:7]
    if scope:
        return f"- **{scope}:** {description} (`{short_hash}`)"
    return f"- {description} (`{short_hash}`)"


# ─── Changelog Generation ─────────────────────────────────────────────────────

def generate_changelog(commits: list[dict]) -> str:
    """Generate the changelog content."""
    sections: dict[str, list[str]] = defaultdict(list)
    other_entries: list[str] = []

    for commit in commits:
        subject = commit["subject"]

        if subject.startswith("Merge "):
            continue

        parsed = parse_commit(subject)
        if not parsed:
            other_entries.append(format_entry("", subject, commit["hash"]))
            continue

        category = classify_commit_type(parsed["type"])
        entry = format_entry(parsed["scope"], parsed["description"], commit["hash"])
        sections[category].append(entry)

    # Build output
    lines: list[str] = []
    lines.append("# Changelog")
    lines.append("")
    lines.append("All notable changes to this project will be documented in this file.")
    lines.append("")

    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"## [Unreleased] - {date}")
    lines.append("")

    for category in ["Added", "Fixed", "Changed", "Removed"]:
        if sections.get(category):
            lines.append(f"### {category}")
            lines.append("")
            lines.extend(sections[category])
            lines.append("")

    if other_entries:
        lines.append("### Changed")
        lines.append("")
        lines.extend(other_entries)
        lines.append("")

    return "\n".join(lines)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from git conventional commits."
    )
    parser.add_argument("range", nargs="?", help="Git range (e.g., v1.0.0..v2.0.0)")
    parser.add_argument("--since", help="Generate from this tag to HEAD")
    parser.add_argument("--unreleased", action="store_true", help="Only since last tag")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    ref_range = args.range
    if args.since:
        ref_range = f"{args.since}..HEAD"
    elif args.unreleased:
        latest = get_latest_tag()
        if latest:
            ref_range = f"{latest}..HEAD"

    commits = get_commits(ref_range)
    if not commits:
        print("No commits found in range.", file=sys.stderr)
        sys.exit(0)

    changelog = generate_changelog(commits)

    if args.output:
        with open(args.output, "w") as f:
            f.write(changelog + "\n")
        print(f"✅ Changelog written to {args.output}", file=sys.stderr)
    else:
        print(changelog)


if __name__ == "__main__":
    main()
