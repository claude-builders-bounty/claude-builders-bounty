#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py          # output to stdout
    python changelog.py -o CHANGELOG.md   # write to file
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from typing import Literal


Category = Literal["Added", "Fixed", "Changed", "Removed"]

CONVENTIONAL_MAP: dict[re.Pattern, Category] = {
    re.compile(r"^(feat|feature)(\(.+?\))?[!]?:\s*"): "Added",
    re.compile(r"^(fix|bugfix|hotfix)(\(.+?\))?[!]?:\s*"): "Fixed",
    re.compile(r"^(chore|refactor|perf|style|docs|test|ci|build)(\(.+?\))?[!]?:\s*"): "Changed",
    re.compile(r"^(revert|deprecate)(\(.+?\))?[!]?:\s*"): "Removed",
}

FALLBACK_MAP: dict[re.Pattern, Category] = {
    re.compile(r"^\s*[Aa]dd"): "Added",
    re.compile(r"^\s*[Ff]ix"): "Fixed",
    re.compile(r"^\s*[Rr]emov"): "Removed",
    re.compile(r"^\s*[Uu]pdate|[Ii]mprov|[Cc]hang|[Rr]efactor"): "Changed",
}


def classify(message: str) -> Category:
    for pattern, cat in CONVENTIONAL_MAP.items():
        if pattern.search(message):
            return cat
    for pattern, cat in FALLBACK_MAP.items():
        if pattern.search(message):
            return cat
    return "Changed"


def get_last_tag() -> str | None:
    try:
        return subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commits(since: str | None) -> list[dict[str, str]]:
    if since:
        fmt = f"{since}..HEAD"
    else:
        fmt = "--all"

    log = subprocess.run(
        ["git", "log", fmt, "--pretty=format:%H||%s||%an||%ai", "--no-merges"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    entries: list[dict[str, str]] = []
    for line in log.split("\n"):
        if not line:
            continue
        parts = line.split("||", 3)
        if len(parts) >= 2:
            entries.append({
                "hash": parts[0][:7],
                "subject": parts[1],
                "author": parts[2] if len(parts) > 2 else "",
                "date": parts[3] if len(parts) > 3 else "",
            })
    return entries


def generate(commits: list[dict[str, str]]) -> str:
    groups: dict[Category, list[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }

    for c in commits:
        cat = classify(c["subject"])
        line = f"- {c['subject']} ([{c['hash']}]({c['hash']}))"
        groups[cat].append(line)

    lines = ["# Changelog", ""]

    tag = get_last_tag() or "initial"
    lines.append(f"## [{tag}] - {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")

    has_content = False
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = groups[cat]
        if items:
            has_content = True
            lines.append(f"### {cat}")
            lines.extend(items)
            lines.append("")

    if not has_content:
        lines.append("_No significant changes._")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    since = get_last_tag()
    commits = get_commits(since)
    changelog = generate(commits)

    if args.output:
        with open(args.output, "w") as f:
            f.write(changelog)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(changelog)


if __name__ == "__main__":
    main()
