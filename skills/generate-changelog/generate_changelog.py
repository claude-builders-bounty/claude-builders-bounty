#!/usr/bin/env python3
"""
generate-changelog: Generate CHANGELOG.md from commits since the last git tag.
Categories: Added, Fixed, Changed, Removed.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

CATEGORY_ADDED = "Added"
CATEGORY_FIXED = "Fixed"
CATEGORY_CHANGED = "Changed"
CATEGORY_REMOVED = "Removed"

CONVENTIONAL_MAP = {
    "feat": CATEGORY_ADDED,
    "feature": CATEGORY_ADDED,
    "fix": CATEGORY_FIXED,
    "bugfix": CATEGORY_FIXED,
    "perf": CATEGORY_CHANGED,
    "refactor": CATEGORY_CHANGED,
    "style": CATEGORY_CHANGED,
    "chore": CATEGORY_CHANGED,
    "build": CATEGORY_CHANGED,
    "ci": CATEGORY_CHANGED,
    "docs": CATEGORY_CHANGED,
    "test": CATEGORY_CHANGED,
    "deprecate": CATEGORY_REMOVED,
    "revert": CATEGORY_REMOVED,
    "remove": CATEGORY_REMOVED,
}

KEYWORD_PREFIXES = [
    (r"^(add|added|adding|new|support)\b", CATEGORY_ADDED),
    (r"^(fix|fixed|fixing|resolve|resolved|patch)\b", CATEGORY_FIXED),
    (r"^(remove|removed|removing|delete|deleted|drop|dropped|deprecate|deprecated)\b", CATEGORY_REMOVED),
    (r"^(update|updated|change|changed|refactor|upgrade|bump|clean|improve)\b", CATEGORY_CHANGED),
]


def parse_commit_message(msg: str):
    """
    Parses a commit message line into (category, clean_message).
    Returns (None, None) if the commit should be ignored (e.g. merge commits, empty).
    """
    if not msg or not msg.strip():
        return None, None

    msg = msg.strip()

    # Ignore merge commits
    if re.match(r"^merge\s+", msg, flags=re.IGNORECASE):
        return None, None

    # Check conventional commit format: type(scope)!: message or type: message
    conv_match = re.match(r"^([a-zA-Z]+)(?:\([^\)]+\))?!?:\s*(.+)$", msg)
    if conv_match:
        ctype = conv_match.group(1).lower()
        body = conv_match.group(2).strip()
        cat = CONVENTIONAL_MAP.get(ctype, CATEGORY_CHANGED)
        return cat, body

    # Check keyword prefix matching
    for pattern, cat in KEYWORD_PREFIXES:
        if re.search(pattern, msg, flags=re.IGNORECASE):
            return cat, msg

    # Default fallback category
    return CATEGORY_CHANGED, msg


def get_commits_since_last_tag(repo_path: str = ".", since: str = None):
    """
    Finds commits since the most recent reachable tag, or since a specified revision/tag.
    If no tags exist and since is None, returns all commits.
    Returns list of tuples: [(hash, subject), ...]
    """
    if since:
        rev_range = f"{since}..HEAD" if ".." not in since else since
    else:
        tag_proc = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if tag_proc.returncode == 0 and tag_proc.stdout.strip():
            latest_tag = tag_proc.stdout.strip()
            rev_range = f"{latest_tag}..HEAD"
        else:
            rev_range = "HEAD"

    log_proc = subprocess.run(
        ["git", "log", rev_range, "--no-merges", "--pretty=format:%h %s"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if log_proc.returncode != 0:
        return []

    lines = log_proc.stdout.strip().split("\n")
    commits = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append((parts[0], parts[1]))
        elif len(parts) == 1:
            commits.append((parts[0], ""))
    return commits


def format_markdown(commits_by_cat: dict, tag_name: str = "Unreleased", date_str: str = None) -> str:
    """
    Formats categorized commits into standard Keep a Changelog markdown.
    """
    if date_str is None:
        date_str = datetime.date.today().isoformat()

    lines = [
        f"## [{tag_name}] - {date_str}",
        ""
    ]

    order = [CATEGORY_ADDED, CATEGORY_FIXED, CATEGORY_CHANGED, CATEGORY_REMOVED]
    total_entries = 0

    for cat in order:
        entries = commits_by_cat.get(cat, [])
        if entries:
            lines.append(f"### {cat}")
            for chash, desc in entries:
                if chash:
                    lines.append(f"- {desc} ({chash})")
                else:
                    lines.append(f"- {desc}")
            lines.append("")
            total_entries += len(entries)

    if total_entries == 0:
        lines.append("No changes recorded.")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def generate_changelog(repo_path: str = ".", output_path: str = "CHANGELOG.md", tag_name: str = "Unreleased", since: str = None):
    """
    Extracts commits and writes or prepends to output_path.
    """
    raw_commits = get_commits_since_last_tag(repo_path, since=since)
    commits_by_cat = {
        CATEGORY_ADDED: [],
        CATEGORY_FIXED: [],
        CATEGORY_CHANGED: [],
        CATEGORY_REMOVED: [],
    }

    for chash, msg in raw_commits:
        cat, clean_msg = parse_commit_message(msg)
        if cat and clean_msg:
            commits_by_cat[cat].append((chash, clean_msg))

    new_section = format_markdown(commits_by_cat, tag_name=tag_name)

    # Prepend or create CHANGELOG.md
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing.startswith("# Changelog"):
            # Insert after header
            rest = existing[len(header):] if existing.startswith(header) else existing
            full_content = header + new_section + "\n" + rest.lstrip()
        else:
            full_content = header + new_section + "\n" + existing
    else:
        full_content = header + new_section

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    return full_content


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since last git tag.")
    parser.add_argument("--repo", default=".", help="Path to git repository (default: current directory)")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output path (default: CHANGELOG.md)")
    parser.add_argument("--tag", "-t", default="Unreleased", help="Tag / Version name for header (default: Unreleased)")
    parser.add_argument("--since", "-s", default=None, help="Tag or commit range to generate changelog from (default: latest tag)")

    args = parser.parse_args()
    try:
        generate_changelog(repo_path=args.repo, output_path=args.output, tag_name=args.tag, since=args.since)
        print(f"Successfully generated changelog at {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
