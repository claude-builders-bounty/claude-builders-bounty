#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History.
Fulfills Bounty #1 on claude-builders-bounty ($50).

Fetches commits since the latest git tag, auto-categorizes into
Added, Fixed, Changed, and Removed based on Conventional Commits,
and outputs a standard Keep a Changelog markdown document.
"""

import subprocess
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def run_git(args: list[str]) -> str:
    res = subprocess.run(["git"] + args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        return ""
    return res.stdout.strip()

def get_latest_tag() -> str:
    return run_git(["describe", "--tags", "--abbrev=0"])

def get_commits_since(tag: str) -> list[str]:
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    raw = run_git(["log", rev_range, "--pretty=format:%s|||%h|||%an"])
    if not raw:
        # Fallback to all commits if no tag exists
        raw = run_git(["log", "-n", "50", "--pretty=format:%s|||%h|||%an"])
    lines = [line.strip() for line in raw.split("\n") if line.strip()]
    return lines

def categorize_commits(commit_lines: list[str]) -> dict[str, list[str]]:
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Other": [],
    }

    for line in commit_lines:
        parts = line.split("|||")
        if len(parts) < 2:
            continue
        msg, sha = parts[0].strip(), parts[1].strip()

        # Categorization heuristics (Conventional Commits + Keywords)
        clean_msg = re.sub(r"^(?:feat|fix|refactor|perf|chore|docs|style|test|build|ci)(?:\([^)]+\))?:\s*", "", msg, flags=re.IGNORECASE)
        entry = f"- {clean_msg} ([`{sha}`]({sha}))"

        lower_msg = msg.lower()
        if re.match(r"^feat(?:\([^)]+\))?:", lower_msg) or "add" in lower_msg or "support" in lower_msg:
            categories["Added"].append(entry)
        elif re.match(r"^fix(?:\([^)]+\))?:", lower_msg) or "fix" in lower_msg or "bug" in lower_msg or "resolve" in lower_msg:
            categories["Fixed"].append(entry)
        elif re.match(r"^refactor(?:\([^)]+\))?:", lower_msg) or re.match(r"^perf(?:\([^)]+\))?:", lower_msg) or "change" in lower_msg or "update" in lower_msg:
            categories["Changed"].append(entry)
        elif "remove" in lower_msg or "deprecat" in lower_msg or "drop" in lower_msg or "delete" in lower_msg:
            categories["Removed"].append(entry)
        else:
            categories["Changed"].append(entry)

    return categories

def generate_markdown(categories: dict[str, list[str]], tag: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    version_title = f"## [Unreleased] - {today}" if not tag else f"## [{tag}..HEAD] - {today}"

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).",
        "",
        version_title,
        "",
    ]

    for section in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories.get(section, [])
        if items:
            lines.append(f"### {section}")
            lines.extend(items)
            lines.append("")

    return "\n".join(lines).strip() + "\n"

def main():
    tag = get_latest_tag()
    commits = get_commits_since(tag)
    categorized = categorize_commits(commits)
    changelog_md = generate_markdown(categorized, tag)

    out_file = Path("CHANGELOG.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(changelog_md)

    print(f"✅ Generated {out_file} successfully! ({len(commits)} commits processed)")
    print(changelog_md[:500])

if __name__ == "__main__":
    main()
