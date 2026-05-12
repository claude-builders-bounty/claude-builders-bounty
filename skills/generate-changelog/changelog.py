#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

import subprocess
import sys
import re
from datetime import date
from pathlib import Path
from typing import Optional

CATEGORIES = {
    "Added": ["feat", "add", "new", "create", "implement"],
    "Fixed": ["fix", "bug", "resolve", "patch", "repair"],
    "Changed": ["refactor", "update", "change", "modify", "improve", "tweak", "adjust"],
    "Removed": ["remove", "delete", "drop", "deprecate"],
}

FALLBACK = "Other"


def get_last_tag() -> 'Optional[str]':
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_commits_since(tag=None):
    ref = tag if tag is not None else ""
    cmd = ["git", "log", "--pretty=format:%h|%s|%an", f"{ref}..HEAD"] if tag is not None else ["git", "log", "--pretty=format:%h|%s|%an"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) >= 2:
                commits.append({"hash": parts[0], "message": parts[1], "author": parts[2] if len(parts) > 2 else "unknown"})
        return commits
    except Exception:
        return []


def categorize(message: str) -> str:
    lower = message.lower()

    # Try conventional commit prefix: type(scope): description
    match = re.match(r"^(\w+)(?:\(.*?\))?:\s*(.*)", message)
    if match:
        prefix = match.group(1).lower()
        for category, keywords in CATEGORIES.items():
            if prefix in keywords:
                return category

    # Fallback: keyword matching
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if lower.startswith(kw) or f" {kw} " in lower or lower.endswith(kw):
                return category

    return FALLBACK


def clean_message(message: str) -> str:
    """Strip conventional commit prefix and whitespace."""
    msg = re.sub(r"^\w+(?:\(.*?\))?:\s*", "", message)
    return msg.strip().rstrip(".")


def generate_changelog(
    output_path: str = "CHANGELOG.md",
    from_tag = None,
    include_all: bool = False,
) -> str:
    if from_tag:
        tag = from_tag
    elif not include_all:
        tag = get_last_tag()
    else:
        tag = None

    commits = get_commits_since(tag)
    if not commits:
        print("No commits found.")
        sys.exit(0)

    grouped: dict[str, list[dict]] = {c: [] for c in CATEGORIES}
    grouped[FALLBACK] = []
    for c in commits:
        grouped[categorize(c["message"])].append(c)

    today = date.today().isoformat()
    tag_label = tag or "first commit"
    lines = [
        "# Changelog\n",
        f"## [Unreleased] — {today}\n",
        f"> Commits since `{tag_label}` ({len(commits)} total)\n",
    ]

    order = ["Added", "Fixed", "Changed", "Removed", "Other"]
    emojis = {"Added": "\u2728", "Fixed": "\U0001f41b", "Changed": "\U0001f527", "Removed": "\U0001f5d1\ufe0f", "Other": "\U0001f4dd"}

    for cat in order:
        items = grouped.get(cat, [])
        if not items:
            continue
        lines.append(f"### {emojis.get(cat, '')} {cat}\n")
        for c in items:
            lines.append(f"- {clean_message(c['message'])}")
        lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    output = Path(output_path)
    output.write_text(text)
    print(f"CHANGELOG.md written ({len(commits)} commits)")
    return text


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    parser.add_argument("--from", dest="from_tag", help="Generate from a specific tag")
    parser.add_argument("--all", action="store_true", help="Include all commits (ignore tags)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing file")
    args = parser.parse_args()

    text = generate_changelog(
        output_path=args.output,
        from_tag=getattr(args, "from_tag"),
        include_all=args.all,
    )
    if args.stdout:
        print(text)


if __name__ == "__main__":
    main()
