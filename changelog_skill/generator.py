#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from collections import OrderedDict
from pathlib import Path
from typing import Iterable


CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")


def categorize_commit(message: str) -> str:
    lowered = message.strip().lower()
    if lowered.startswith(("feat", "add")):
        return "Added"
    if lowered.startswith(("fix", "bug")):
        return "Fixed"
    if lowered.startswith(("remove", "delete", "drop")):
        return "Removed"
    return "Changed"


def latest_tag(repo_path: Path) -> str | None:
    proc = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=repo_path,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def collect_commits_since_last_tag(repo_path: Path) -> list[str]:
    tag = latest_tag(repo_path)
    revspec = f"{tag}..HEAD" if tag else "HEAD"
    proc = subprocess.run(
        ["git", "log", revspec, "--pretty=format:%s"],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def generate_changelog_markdown(version: str, commits: Iterable[str]) -> str:
    grouped: OrderedDict[str, list[str]] = OrderedDict((name, []) for name in CATEGORY_ORDER)
    for commit in commits:
        grouped[categorize_commit(commit)].append(commit)

    lines = ["# CHANGELOG", "", f"## {version}", ""]
    for category, items in grouped.items():
        if not items:
            continue
        lines.append(f"### {category}")
        lines.extend(f"- {item}" for item in items)
        lines.append("")
    if lines[-1] != "":
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="changelog.sh")
    parser.add_argument("--repo", default=".", help="Git repository path")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--version", default="Unreleased", help="Version heading to use")
    args = parser.parse_args(argv)

    repo_path = Path(args.repo).resolve()
    commits = collect_commits_since_last_tag(repo_path)
    markdown = generate_changelog_markdown(args.version, commits)
    Path(args.output).write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
