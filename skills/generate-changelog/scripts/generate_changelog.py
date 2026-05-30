#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = [
    "Added",
    "Fixed",
    "Changed",
    "Removed",
]


TYPE_TO_CATEGORY = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "change": "Changed",
    "changed": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "deps": "Changed",
    "chore": "Changed",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "docs": "Changed",
    "doc": "Changed",
}


@dataclass(frozen=True)
class Commit:
    full_hash: str
    short_hash: str
    subject: str


def git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def discover_range(user_range: str | None) -> tuple[str | None, str]:
    if user_range:
        return user_range, user_range

    try:
        latest_tag = git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None, "all commits"

    return f"{latest_tag}..HEAD", f"{latest_tag}..HEAD"


def read_commits(commit_range: str | None) -> list[Commit]:
    fmt = "%H%x1f%h%x1f%s"
    args = ["log", f"--pretty=format:{fmt}", "--no-merges"]
    if commit_range:
        args.append(commit_range)

    output = git(args)
    commits: list[Commit] = []
    for line in output.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        commits.append(Commit(full_hash=parts[0], short_hash=parts[1], subject=parts[2]))
    return commits


def remote_commit_base() -> str | None:
    try:
        remote = git(["remote", "get-url", "origin"])
    except subprocess.CalledProcessError:
        return None

    remote = remote.strip()
    if remote.endswith(".git"):
        remote = remote[:-4]
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.removeprefix("git@github.com:")
    if remote.startswith("https://github.com/"):
        return remote + "/commit/"
    return None


def categorize(subject: str) -> str:
    lower = subject.lower()
    conventional = re.match(r"^(?P<type>[a-z]+)(?:\([^)]+\))?!?:\s*(?P<rest>.+)$", lower)
    if conventional:
        return TYPE_TO_CATEGORY.get(conventional.group("type"), "Changed")

    keyword_rules = [
        ("Fixed", ["fix", "bug", "crash", "regression", "broken", "error"]),
        ("Added", ["add", "new", "introduce", "support", "create"]),
        ("Removed", ["remove", "delete", "drop"]),
        ("Changed", ["readme", "doc", "example", "guide", "security", "vulnerability", "cve", "xss", "csrf", "injection", "secret"]),
    ]
    for category, keywords in keyword_rules:
        if any(keyword in lower for keyword in keywords):
            return category
    return "Changed"


def clean_subject(subject: str) -> str:
    match = re.match(r"^[a-z]+(?:\([^)]+\))?!?:\s*(?P<rest>.+)$", subject, flags=re.I)
    if match:
        subject = match.group("rest")
    subject = subject.strip()
    if not subject:
        return "Update project"
    return subject[0].upper() + subject[1:]


def render(commits: list[Commit], range_label: str, version: str | None) -> str:
    today = dt.date.today().isoformat()
    heading = version or "Unreleased"
    base = remote_commit_base()
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}

    for commit in reversed(commits):
        category = categorize(commit.subject)
        label = clean_subject(commit.subject)
        if base:
            suffix = f" ([`{commit.short_hash}`]({base}{commit.full_hash}))"
        else:
            suffix = f" (`{commit.short_hash}`)"
        grouped[category].append(f"- {label}{suffix}")

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project are documented in this file.",
        "",
        f"Generated from git history range: `{range_label}`.",
        "",
        f"## {heading} - {today}",
        "",
    ]

    wrote_any = False
    for category in CATEGORIES:
        entries = grouped[category]
        if not entries:
            continue
        wrote_any = True
        lines.append(f"### {category}")
        lines.append("")
        lines.extend(entries)
        lines.append("")

    if not wrote_any:
        lines.extend(["### Changed", "", "- No commits found for the selected range.", ""])

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--range", dest="commit_range", help="git revision range, for example v1.0.0..HEAD")
    parser.add_argument("--version", help="release heading to use instead of Unreleased")
    parser.add_argument("--output", default="CHANGELOG.md", help="output path")
    args = parser.parse_args()

    commit_range, range_label = discover_range(args.commit_range)
    commits = read_commits(commit_range)
    changelog = render(commits, range_label, args.version)
    Path(args.output).write_text(changelog, encoding="utf-8")
    print(f"Wrote {args.output} with {len(commits)} commits from {range_label}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
