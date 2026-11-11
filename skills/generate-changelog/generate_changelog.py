#!/usr/bin/env python3
"""
generate_changelog.py - Generates Keep a Changelog compliant CHANGELOG.md from git history.
Categorizes commits into Added, Fixed, Changed, Removed based on Conventional Commits.
"""

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path


def run_git(args: list[str]) -> str:
    res = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def get_last_tag() -> str | None:
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None


def get_commits(commit_range: str) -> list[tuple[str, str, str]]:
    cmd = ["log", commit_range, "--no-merges", "--pretty=format:%h|%s|%an"]
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
    categories: dict[str, list[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }

    for chash, subject, _author in commits:
        entry = f"- {subject} ([{chash}]({chash}))"
        s_lower = subject.lower()

        if re.match(r"^feat(\(.*\))?:", s_lower):
            categories["Added"].append(entry)
        elif re.match(r"^(fix|bugfix)(\(.*\))?:", s_lower):
            categories["Fixed"].append(entry)
        elif re.match(r"^(remove|delete|deprecate)(\(.*\))?:", s_lower):
            categories["Removed"].append(entry)
        elif re.match(r"^(chore|refactor|perf|docs|style|test|build|ci)(\(.*\))?:", s_lower):
            categories["Changed"].append(entry)
        elif any(k in s_lower for k in ["add", "feature", "new"]):
            categories["Added"].append(entry)
        elif any(k in s_lower for k in ["fix", "resolve", "close"]):
            categories["Fixed"].append(entry)
        elif any(k in s_lower for k in ["remove", "delete", "deprecate"]):
            categories["Removed"].append(entry)
        else:
            categories["Changed"].append(entry)

    return categories


def build_markdown(categories: dict[str, list[str]], tag_info: str) -> str:
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
        f"## [Unreleased] - {today} ({tag_info})",
        "",
    ]

    has_entries = False
    for section in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories.get(section, [])
        if items:
            has_entries = True
            lines.append(f"### {section}")
            lines.append("")
            lines.extend(items)
            lines.append("")

    if not has_entries:
        lines.append("*No commits found in range.*")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git history.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("-t", "--tag", help="Specific tag to query since")
    parser.add_argument("-a", "--all", action="store_true", help="Include full commit history")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Print to stdout without writing")
    args = parser.parse_args()

    last_tag = args.tag or (None if args.all else get_last_tag())
    if last_tag:
        commit_range = f"{last_tag}..HEAD"
        tag_info = f"since {last_tag}"
    else:
        commit_range = "HEAD"
        tag_info = "full repository history"

    commits = get_commits(commit_range)
    categories = categorize_commits(commits)
    content = build_markdown(categories, tag_info)

    if args.dry_run:
        print(content)
    else:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"Successfully generated {args.output} ({tag_info})")


if __name__ == "__main__":
    main()
