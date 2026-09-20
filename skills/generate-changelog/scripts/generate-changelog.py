#!/usr/bin/env python3
"""
generate-changelog.py

Extracts commits from git history since the latest tag, categorizes them into
Added, Fixed, Changed, and Removed according to Conventional Commits and Keep a Changelog,
and writes or updates CHANGELOG.md.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

CATEGORY_PATTERNS = {
    "Added": [
        r"^feat(?:\([^)]+\))?!?:",
        r"^add(?:\([^)]+\))?!?:",
        r"^new(?:\([^)]+\))?!?:",
        r"^implement(?:\([^)]+\))?!?:",
        r"\badded\b",
        r"\bfeature\b"
    ],
    "Fixed": [
        r"^fix(?:\([^)]+\))?!?:",
        r"^bug(?:\([^)]+\))?!?:",
        r"^hotfix(?:\([^)]+\))?!?:",
        r"^patch(?:\([^)]+\))?!?:",
        r"^resolve(?:\([^)]+\))?!?:",
        r"\bfixed\b",
        r"\bresolves\b",
        r"\bbugfix\b"
    ],
    "Removed": [
        r"^remove(?:\([^)]+\))?!?:",
        r"^delete(?:\([^)]+\))?!?:",
        r"^drop(?:\([^)]+\))?!?:",
        r"^deprecate(?:\([^)]+\))?!?:",
        r"\bremoved\b",
        r"\bdeleted\b",
        r"\bdeprecated\b"
    ],
    "Changed": [
        r"^refactor(?:\([^)]+\))?!?:",
        r"^perf(?:\([^)]+\))?!?:",
        r"^chore(?:\([^)]+\))?!?:",
        r"^docs(?:\([^)]+\))?!?:",
        r"^style(?:\([^)]+\))?!?:",
        r"^build(?:\([^)]+\))?!?:",
        r"^ci(?:\([^)]+\))?!?:",
        r"^update(?:\([^)]+\))?!?:",
        r"^change(?:\([^)]+\))?!?:",
        r"\bupdated\b",
        r"\brefactored\b"
    ]
}


def run_git_cmd(args):
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""


def get_latest_tag():
    # Try getting the most recent tag reachable from HEAD
    tag = run_git_cmd(["describe", "--tags", "--abbrev=0"])
    if not tag:
        # Fallback to listing all tags sorted by creation
        tags = run_git_cmd(["tag", "--sort=-creatordate"]).splitlines()
        if tags and tags[0].strip():
            tag = tags[0].strip()
    return tag if tag else None


def get_commits_since(tag=None):
    if tag:
        git_range = f"{tag}..HEAD"
    else:
        git_range = "HEAD"

    # %h: short hash, %s: subject, %an: author name
    log_output = run_git_cmd(["log", git_range, "--format=%h|||%s|||%an"])
    if not log_output:
        return []

    commits = []
    for line in log_output.splitlines():
        parts = line.split("|||")
        if len(parts) == 3:
            commits.append({
                "hash": parts[0].strip(),
                "subject": parts[1].strip(),
                "author": parts[2].strip()
            })
    return commits


def categorize_commit(subject):
    clean_subject = subject.strip()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, clean_subject, re.IGNORECASE):
                return category
    return "Changed"


def clean_commit_message(subject):
    # Strip conventional commit prefixes e.g. "feat(auth): add login" -> "add login" or "Add login"
    cleaned = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:", "", subject).strip()
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    else:
        cleaned = subject
    return cleaned


def generate_markdown(version, date_str, categorized_commits):
    lines = [f"## [{version}] - {date_str}"]
    categories_order = ["Added", "Fixed", "Changed", "Removed"]

    has_content = False
    for cat in categories_order:
        entries = categorized_commits.get(cat, [])
        if entries:
            has_content = True
            lines.append(f"\n### {cat}")
            for entry in entries:
                msg = clean_commit_message(entry["subject"])
                lines.append(f"- {msg} ([`{entry['hash']}`] - @{entry['author']})")

    if not has_content:
        lines.append("\n### Changed\n- Maintenance updates and general improvements.")

    return "\n".join(lines)


def update_changelog_file(output_path, release_block):
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\nand this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"

    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        if existing_content.startswith("# Changelog"):
            # Find the position after the header
            match = re.search(r"## \[", existing_content)
            if match:
                idx = match.start()
                new_content = existing_content[:idx] + release_block + "\n\n" + existing_content[idx:]
            else:
                new_content = existing_content.rstrip() + "\n\n" + release_block + "\n"
        else:
            new_content = header + release_block + "\n\n" + existing_content
    else:
        new_content = header + release_block + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("--version", default="Unreleased", help="Version tag to assign to this release")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("--from-tag", default=None, help="Base git tag to start commit log from")
    args = parser.parse_args()

    base_tag = args.from_tag or get_latest_tag()
    commits = get_commits_since(base_tag)

    print(f"Generating changelog for version: {args.version}")
    if base_tag:
        print(f"Comparing against tag: {base_tag} ({len(commits)} commits found)")
    else:
        print(f"No prior tag found. Processing all repository commits ({len(commits)} commits found)")

    categorized = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for c in commits:
        cat = categorize_commit(c["subject"])
        categorized[cat].append(c)

    date_str = datetime.date.today().isoformat()
    release_block = generate_markdown(args.version, date_str, categorized)

    update_changelog_file(args.output, release_block)
    print(f"Successfully generated/updated {args.output}")


if __name__ == "__main__":
    main()
