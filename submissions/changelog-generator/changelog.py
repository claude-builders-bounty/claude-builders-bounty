#!/usr/bin/env python3
"""changelog.py — Generate structured CHANGELOG.md from git history.

Supports conventional commits and plain commit messages.
Auto-categorizes into Added / Fixed / Changed / Removed / Security sections.

Usage:
    python3 changelog.py [--output CHANGELOG.md] [--tag v1.0.0]
    bash changelog.sh               # thin wrapper, same result
"""

import argparse
import subprocess
import sys
import os
import re
from datetime import date
from collections import defaultdict


def run_git(*args: str) -> str:
    """Run a git command and return stripped stdout."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        print("Error: git is not installed or not found in PATH.", file=sys.stderr)
        sys.exit(1)


def get_latest_tag() -> str:
    """Return the most recent git tag, or empty string if none."""
    tag = run_git("describe", "--tags", "--abbrev=0")
    return tag


def get_previous_tag(current_tag: str) -> str:
    """Get the tag before current_tag, or empty if this is the first tag."""
    tags = run_git("tag", "--sort=-creatordate")
    if not tags:
        return ""
    tag_list = tags.split("\n")
    try:
        idx = tag_list.index(current_tag)
        if idx + 1 < len(tag_list):
            return tag_list[idx + 1]
    except ValueError:
        pass
    return ""


def get_commits(start_ref: str, end_ref: str = "HEAD") -> str:
    """Get commit log between two refs."""
    if start_ref:
        range_spec = f"{start_ref}..{end_ref}"
    else:
        range_spec = end_ref
    return run_git("log", range_spec, "--oneline", "--no-merges")


def categorize_commits(commits: str) -> dict[str, list[str]]:
    """Parse conventional commits and plain messages into categories.

    Conventional commit prefixes:
      feat:     → Added
      fix:      → Fixed
      refactor: → Changed
      perf:     → Changed
      style:    → Changed
      docs:     → Changed
      test:     → Changed
      chore:    → Changed
      ci:       → Changed
      build:    → Changed
      revert:   → Removed
      remove:   → Removed
      security: → Security

    Falls back to keyword matching for plain messages.
    """
    categories: dict[str, list[str]] = defaultdict(list)

    conventional_map = {
        "feat": "Added",
        "fix": "Fixed",
        "refactor": "Changed",
        "perf": "Changed",
        "style": "Changed",
        "docs": "Changed",
        "test": "Changed",
        "chore": "Changed",
        "ci": "Changed",
        "build": "Changed",
        "revert": "Removed",
        "remove": "Removed",
        "security": "Security",
    }

    keyword_map = {
        "Added": [
            r"\b(add|create|new|implement|introduce|support|allow|enable)\b",
        ],
        "Fixed": [
            r"\b(fix|bug|hotfix|patch|correct|resolve|repair)\b",
        ],
        "Removed": [
            r"\b(remove|delete|deprecat|drop|retire|obsolete)\b",
        ],
        "Changed": [
            r"\b(change|update|refactor|improve|migrate|upgrade|tweak|adjust|optimize)\b",
        ],
        "Security": [
            r"\b(security|vuln|exploit|injection|auth|csrf|xss)\b",
        ],
    }

    if not commits:
        return categories

    for line in commits.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove the short hash prefix (e.g., "abc1234 ")
        message = line
        if re.match(r"^[a-f0-9]{7,}\s", line):
            message = line[line.index(" ") + 1:]

        categorized = False

        # Try conventional commit pattern: "type(scope): description"
        cc_match = re.match(r"^(\w+)(\([^)]*\))?!?:\s*(.+)", message)
        if cc_match:
            prefix = cc_match.group(1).lower()
            desc = cc_match.group(3)
            if prefix in conventional_map:
                cat = conventional_map[prefix]
                # BREAKING CHANGE marker: feat(scope)!: or feat!:
                prefix = cc_match.group(0)
                if "!:" in prefix.split(":")[0] + ":":
                    categories[cat].append(f"{desc} **[BREAKING]**")
                else:
                    categories[cat].append(desc)
                categorized = True

        # Fallback to keyword matching
        if not categorized:
            msg_lower = message.lower()
            for cat, patterns in keyword_map.items():
                if any(re.search(p, msg_lower) for p in patterns):
                    categories[cat].append(message)
                    categorized = True
                    break

        # Uncategorized → Changes section
        if not categorized:
            categories["Changed"].append(message)

    return categories


def generate_changelog(
    output_path: str,
    release_tag: str | None = None,
    previous_tag: str | None = None,
) -> str:
    """Generate CHANGELOG.md and return the markdown content."""

    # Determine range
    if release_tag:
        tag = release_tag
        prev = previous_tag or get_previous_tag(tag)
    else:
        tag = get_latest_tag()
        prev = get_previous_tag(tag) if tag else ""

    start_ref = prev if prev else ""
    commits = get_commits(start_ref)

    categories = categorize_commits(commits)

    # Build markdown
    lines = []
    lines.append("# Changelog")
    lines.append("")

    version_label = tag if tag else "Unreleased"
    version_label = f"[{version_label}]" if tag else version_label
    today = date.today().isoformat()
    lines.append(f"## {version_label} - {today}")
    lines.append("")

    section_order = ["Added", "Fixed", "Changed", "Removed", "Security"]
    has_content = False

    for section in section_order:
        items = categories.get(section, [])
        if items:
            has_content = True
            lines.append(f"### {section}")
            lines.append("")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    if not has_content:
        lines.append("*No changes recorded.*")
        lines.append("")

    content = "\n".join(lines) + "\n"

    # Write output
    with open(output_path, "w") as f:
        f.write(content)

    return content


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured CHANGELOG.md from git history."
    )
    parser.add_argument(
        "--output", "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)"
    )
    parser.add_argument(
        "--tag", "-t",
        default=None,
        help="Release tag for this changelog entry (default: latest tag)"
    )
    parser.add_argument(
        "--prev-tag", "-p",
        default=None,
        help="Previous tag to diff against (default: auto-detect)"
    )
    args = parser.parse_args()

    # Must be in a git repo
    if not run_git("rev-parse", "--git-dir"):
        print("Error: not a git repository (or any parent directory).", file=sys.stderr)
        sys.exit(1)

    content = generate_changelog(
        output_path=args.output,
        release_tag=args.tag,
        previous_tag=args.prev_tag,
    )

    print(content)
    print(f"✓ Generated {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
