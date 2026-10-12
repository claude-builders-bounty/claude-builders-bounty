#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History.
Extracts commits since the latest git tag and categorizes into Added, Fixed, Changed, Removed.
"""

import sys
import subprocess
import re
from datetime import datetime, timezone


def get_latest_tag() -> str | None:
    """Gets the latest tag in the current repository, or None if no tags exist."""
    try:
        res = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None


def get_commit_messages(since_tag: str | None = None) -> list[str]:
    """Retrieves commit subjects since given tag, or all commits if none."""
    cmd = ["git", "log", "--pretty=format:%s"]
    if since_tag:
        cmd = ["git", "log", f"{since_tag}..HEAD", "--pretty=format:%s"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = [line.strip() for line in res.stdout.split("\n") if line.strip()]
        return lines
    except Exception as e:
        sys.stderr.write(f"Error reading git log: {e}\n")
        return []


def categorize_commits(commits: list[str]) -> dict[str, list[str]]:
    """Categorizes commits into Added, Fixed, Changed, Removed."""
    categories: dict[str, list[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }

    for msg in commits:
        clean_msg = msg.strip()
        lower = clean_msg.lower()

        # Added
        if re.match(r"^(feat|add|feature)(\(.*?\))?:\s*", lower) or "add " in lower:
            clean = re.sub(r"^(feat|add|feature)(\(.*?\))?:\s*", "", clean_msg, flags=re.IGNORECASE)
            categories["Added"].append(clean)
        # Fixed
        elif re.match(r"^(fix|bug|patch)(\(.*?\))?:\s*", lower) or "fix " in lower:
            clean = re.sub(r"^(fix|bug|patch)(\(.*?\))?:\s*", "", clean_msg, flags=re.IGNORECASE)
            categories["Fixed"].append(clean)
        # Removed
        elif re.match(r"^(remove|deprecate|delete)(\(.*?\))?:\s*", lower) or "remove " in lower:
            clean = re.sub(r"^(remove|deprecate|delete)(\(.*?\))?:\s*", "", clean_msg, flags=re.IGNORECASE)
            categories["Removed"].append(clean)
        # Changed (refactor, chore, perf, docs, style, update)
        else:
            clean = re.sub(r"^(refactor|chore|perf|docs|style|update)(\(.*?\))?:\s*", "", clean_msg, flags=re.IGNORECASE)
            categories["Changed"].append(clean)

    return categories


def build_markdown(categories: dict[str, list[str]], tag: str | None = None) -> str:
    """Builds Keep a Changelog compliant Markdown string."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    version_header = f"## [Unreleased] - {today}" if not tag else f"## [{tag}] - {today}"

    out = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).",
        "",
        version_header,
        "",
    ]

    for section in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories.get(section, [])
        if items:
            out.append(f"### {section}")
            for item in items:
                out.append(f"- {item}")
            out.append("")

    return "\n".join(out).strip() + "\n"


def main():
    tag = get_latest_tag()
    commits = get_commit_messages(tag)
    if not commits:
        print("No commits found to process.")
        return

    categorized = categorize_commits(commits)
    changelog_content = build_markdown(categorized, tag)

    out_file = "CHANGELOG.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(changelog_content)

    print(f"Successfully generated {out_file} ({len(commits)} commits processed).")
    print("\n--- Output Preview ---")
    print(changelog_content)


if __name__ == "__main__":
    main()
