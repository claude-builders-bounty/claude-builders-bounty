#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history since the latest tag."""

from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.strip()


def latest_tag() -> str:
    result = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return result.stdout.strip() if result.returncode == 0 else ""


def classify(subject: str) -> str:
    normalized = subject.strip().lower()
    if normalized.startswith(("feat:", "feat(", "feature:", "add ", "added ", "create ", "implement ")):
        return "Added"
    if normalized.startswith(("fix:", "fix(", "bugfix:", "repair ", "hotfix ")):
        return "Fixed"
    if normalized.startswith(("remove ", "removed ", "delete ", "deleted ", "drop ", "dropped ", "deprecate ")):
        return "Removed"
    return "Changed"


def collect_commits() -> tuple[str, list[tuple[str, str, str]]]:
    tag = latest_tag()
    if tag:
        revision_range = f"{tag}..HEAD"
        label = f"since {tag}"
    else:
        revision_range = "HEAD"
        label = "from repository history"

    log = git("log", revision_range, "--no-merges", "--date=short", "--pretty=format:%h%x09%ad%x09%s")
    commits: list[tuple[str, str, str]] = []
    for line in log.splitlines():
        if not line.strip():
            continue
        commit_hash, date, subject = line.split("\t", 2)
        commits.append((commit_hash, date, subject))
    return label, commits


def render_changelog(range_label: str, commits: list[tuple[str, str, str]]) -> str:
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    for commit_hash, date, subject in commits:
        grouped[classify(subject)].append(f"- {subject} ({commit_hash}, {date})")

    generated = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = ["# Changelog", "", f"Generated {generated} using commits {range_label}.", ""]
    for category in CATEGORIES:
        lines.extend([f"## {category}", ""])
        lines.extend(grouped[category] or ["_No changes._"])
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    try:
        git("rev-parse", "--is-inside-work-tree")
    except subprocess.CalledProcessError:
        print("error: run this script from inside a git repository", file=sys.stderr)
        return 1

    output_file = Path(argv[1] if len(argv) > 1 else "CHANGELOG.md")
    range_label, commits = collect_commits()
    output_file.write_text(render_changelog(range_label, commits), encoding="utf-8")
    print(f"Wrote {output_file} with {len(commits)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
