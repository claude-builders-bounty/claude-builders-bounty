#!/usr/bin/env python3
"""
Structured Git Changelog Generator
Part of Claude Code Skills Suite (Bounty #1)

Parses git history since the last tag and outputs a categorized CHANGELOG.md
following Keep a Changelog standards.
"""

import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_git(args: list[str]) -> str:
    """Executes a git command and returns stdout."""
    res = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if res.returncode != 0:
        return ""
    return res.stdout.strip()


def get_latest_tag() -> str:
    """Finds the most recent reachable git tag."""
    return run_git(["describe", "--tags", "--abbrev=0"])


def get_commits_since_tag(tag: str = "") -> list[tuple[str, str, str]]:
    """
    Returns list of (hash, subject, author) since tag.
    Format: %h|%s|%an
    """
    cmd = ["log", "--no-merges", "--pretty=format:%h|%s|%an"]
    if tag:
        cmd.append(f"{tag}..HEAD")
    output = run_git(cmd)
    if not output:
        return []

    commits = []
    for line in output.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return commits


def categorize_commits(commits: list[tuple[str, str, str]]) -> dict[str, list[str]]:
    """Categorizes commits into Added, Fixed, Changed, Removed."""
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    # Conventional commit regex: type(scope)?: message
    pattern = re.compile(r"^([a-zA-Z]+)(?:\([^\)]+\))?!?:\s*(.+)$")

    for commit_hash, subject, author in commits:
        match = pattern.match(subject)
        if match:
            commit_type = match.group(1).lower()
            message = match.group(2).strip()
        else:
            commit_type = ""
            message = subject

        entry = f"- {message} ([`{commit_hash}`] - {author})"

        if commit_type in ("feat", "feature", "add"):
            categories["Added"].append(entry)
        elif commit_type in ("fix", "bugfix", "patch", "security"):
            categories["Fixed"].append(entry)
        elif commit_type in ("revert", "remove", "deprecate"):
            categories["Removed"].append(entry)
        elif commit_type in ("refactor", "perf", "chore", "build", "ci", "docs", "style"):
            categories["Changed"].append(entry)
        else:
            # Heuristic detection for non-conventional commit messages
            lower_msg = subject.lower()
            if any(lower_msg.startswith(w) for w in ("add", "create", "implement", "support", "new")):
                categories["Added"].append(f"- {subject} ([`{commit_hash}`] - {author})")
            elif any(lower_msg.startswith(w) for w in ("fix", "resolve", "handle", "correct", "bug")):
                categories["Fixed"].append(f"- {subject} ([`{commit_hash}`] - {author})")
            elif any(lower_msg.startswith(w) for w in ("remove", "delete", "revert", "deprecate")):
                categories["Removed"].append(f"- {subject} ([`{commit_hash}`] - {author})")
            else:
                categories["Changed"].append(f"- {subject} ([`{commit_hash}`] - {author})")

    return categories


def build_markdown_section(tag: str, categories: dict[str, list[str]], date_str: str = "") -> str:
    """Constructs the Markdown section for this release/batch."""
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    version_header = f"## [{tag or 'Unreleased'}] - {date_str}\n\n"
    content = version_header

    for section in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories.get(section, [])
        if items:
            content += f"### {section}\n\n"
            content += "\n".join(items) + "\n\n"

    return content


def generate_changelog(output_file: str = "CHANGELOG.md") -> str:
    """Generates and writes CHANGELOG.md."""
    tag = get_latest_tag()
    commits = get_commits_since_tag(tag)

    if not commits:
        print("ℹ️ No new commits found since last tag.")
        return ""

    categories = categorize_commits(commits)
    section = build_markdown_section(tag, categories)

    path = Path(output_file)
    existing_content = ""
    if path.exists():
        existing_content = path.read_text(encoding="utf-8")

    # If file exists, prepend new section under the header
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n"

    if existing_content.startswith("# Changelog"):
        # Remove the main title from existing and prepend
        body = existing_content[len(header):] if existing_content.startswith(header) else existing_content.split("\n\n", 1)[-1]
        final_content = header + section + body
    else:
        final_content = header + section + (existing_content if existing_content else "")

    path.write_text(final_content, encoding="utf-8")
    print(f"✅ Successfully updated {output_file} ({len(commits)} commits processed).")
    return final_content


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
    generate_changelog(out)
