#!/usr/bin/env python3
"""
Conventional Changelog Generator
Extracts git history since the latest tag, groups by Conventional Commits categories,
and formats a clean, standardized CHANGELOG.md.
"""

import subprocess
import re
import sys
import os
from datetime import datetime, timezone

CATEGORIES = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "refactor": "Changed",
    "perf": "Changed",
    "change": "Changed",
    "style": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "docs": "Changed",
    "remove": "Removed",
    "deprecate": "Removed",
    "revert": "Removed",
}

def get_last_tag() -> str:
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return tag
    except Exception:
        return ""

def get_commits_since(tag: str) -> list[str]:
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        log_output = subprocess.check_output(
            ["git", "log", rev_range, "--no-merges", "--pretty=format:%h|||%s|||%an"],
            text=True
        ).strip()
        if not log_output:
            return []
        return log_output.split("\n")
    except Exception as e:
        sys.stderr.write(f"Error reading git commits: {e}\n")
        return []

def categorize_commits(commit_lines: list[str]) -> dict[str, list[dict]]:
    buckets = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    # Matches conventional commit: feat(scope): subject or fix: subject
    pattern = re.compile(r"^([a-zA-Z]+)(?:\((.*?)\))?(!)?:\s*(.*)$")

    for line in commit_lines:
        if not line.strip():
            continue
        parts = line.split("|||")
        if len(parts) < 2:
            continue
        commit_hash = parts[0]
        subject = parts[1]
        author = parts[2] if len(parts) > 2 else ""

        match = pattern.match(subject)
        if match:
            ctype, scope, breaking, desc = match.groups()
            ctype_lower = ctype.lower()
            category = CATEGORIES.get(ctype_lower, "Changed")
            scope_prefix = f"**{scope}:** " if scope else ""
            item = f"{scope_prefix}{desc} (`{commit_hash}` by {author})"
            buckets[category].append(item)
        else:
            # Fallback heuristic
            sub_lower = subject.lower()
            if any(k in sub_lower for k in ["add", "feat", "new", "create"]):
                buckets["Added"].append(f"{subject} (`{commit_hash}`)")
            elif any(k in sub_lower for k in ["fix", "patch", "resolve", "bug"]):
                buckets["Fixed"].append(f"{subject} (`{commit_hash}`)")
            elif any(k in sub_lower for k in ["remove", "delete", "deprecat"]):
                buckets["Removed"].append(f"{subject} (`{commit_hash}`)")
            else:
                buckets["Changed"].append(f"{subject} (`{commit_hash}`)")

    return buckets

def generate_markdown(buckets: dict[str, list[dict]], tag: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    version_header = f"## [{tag or 'Unreleased'}] - {today}\n"

    sections = []
    for section in ["Added", "Fixed", "Changed", "Removed"]:
        items = buckets.get(section, [])
        if items:
            sections.append(f"### {section}\n" + "\n".join(f"- {it}" for it in items))

    if not sections:
        sections.append("No significant changes recorded.")

    return version_header + "\n\n".join(sections) + "\n"

def main():
    tag = get_last_tag()
    commits = get_commits_since(tag)
    buckets = categorize_commits(commits)
    changelog_content = generate_markdown(buckets, tag)

    output_file = "CHANGELOG.md"
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            existing = f.read()
        combined = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{changelog_content}\n---\n\n" + existing.replace("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n", "")
    else:
        combined = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{changelog_content}"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined)

    print(f"✅ Generated {output_file} successfully ({len(commits)} commits processed)!")

if __name__ == "__main__":
    main()
