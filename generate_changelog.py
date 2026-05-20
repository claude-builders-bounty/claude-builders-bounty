#!/usr/bin/env python3
"""
generate_changelog.py
Generates a structured CHANGELOG.md from git history.
Auto-categorizes commits into: Added, Fixed, Changed, Removed.
Usage: python3 generate_changelog.py [--since-tag TAG] [--output FILE]
"""

import subprocess
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path

CHANGELOG_TEMPLATE = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [{version}] - {date}

{body}

---

Generated automatically by `generate_changelog.py`.
"""

KEYWORD_MAP = {
    "Added": [
        r"\\badd(?:s|ed|ing)?\\b",
        r"\\bcreate(?:s|d|ing)?\\b",
        r"\\bfeat(?:ure)?(?:s|d)?\\b",
        r"\\binstall(?:s|ed|ing)?\\b",
        r"\\bnew\\b",
        r"\\bimplement(?:s|ed|ing)?\\b",
        r"\\bintroduce(?:s|d|ing)?\\b",
    ],
    "Fixed": [
        r"\\bfix(?:es|ed|ing)?\\b",
        r"\\bbug(?:s|fix)?\\b",
        r"\\brepair(?:s|ed|ing)?\\b",
        r"\\bresolve(?:s|d|ing)?\\b",
        r"\\bpatch(?:es|ed|ing)?\\b",
        r"\\bcorrect(?:s|ed|ing)?\\b",
    ],
    "Changed": [
        r"\\bupd?ate(?:s|d|ing)?\\b",
        r"\\bmodif(?:y|ies|ied)\\b",
        r"\\bchange(?:s|d)?\\b",
        r"\\brefactor(?:s|ed|ing)?\\b",
        r"\\bimprove(?:s|ed|ing)?\\b",
        r"\\benhance(?:s|ed|ing)?\\b",
        r"\\boptimiz(?:e|es|ed|ing)\\b",
        r"\\brework(?:s|ed|ing)?\\b",
    ],
    "Removed": [
        r"\\bremov(?:e|es|ed|ing)\\b",
        r"\\bdelet(?:e|es|ed|ing)\\b",
        r"\\bdeprecat(?:e|es|ed|ing)\\b",
        r"\\bdrop(?:s|ped|ping)?\\b",
    ],
}


def run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return stdout."""
    repo_cwd = cwd or str(Path(__file__).parent)
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=repo_cwd,
    )
    if result.returncode != 0 and result.stderr:
        print(f"git warning: {result.stderr.strip()}", file=sys.stderr)
    return result.stdout.strip()


def get_latest_tag() -> str | None:
    """Return the latest git tag, or None if no tags exist."""
    tags = run_git(["tag", "--sort=-creatordate"])
    if tags:
        return tags.splitlines()[0]
    return None


def get_commits(repo_path: str | None = None, since_tag: str | None = None) -> list[dict]:
    """Fetch commits since the given tag (or all if None)."""
    fmt = "%H|%an|%ad|%s"
    date_fmt = "--date=short"

    if since_tag:
        log_range = f"{since_tag}..HEAD"
    else:
        log_range = "HEAD"

    output = run_git(["log", log_range, f"--format={fmt}", date_fmt], cwd=repo_path)

    commits = []
    for line in output.splitlines():
        if "|" not in line:
            continue
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        commits.append(
            {
                "hash": parts[0][:7],
                "author": parts[1],
                "date": parts[2],
                "message": parts[3].strip(),
            }
        )
    return commits


def categorize_commit(message: str) -> str:
    """Auto-categorize a commit based on message keywords."""
    lower = message.lower()

    # Look for conventional commit prefixes first
    if lower.startswith("feat") or lower.startswith("add"):
        return "Added"
    if lower.startswith("fix"):
        return "Fixed"
    if lower.startswith("refactor") or lower.startswith("update") or lower.startswith("change"):
        return "Changed"
    if lower.startswith("remove") or lower.startswith("delete") or lower.startswith("deprecate"):
        return "Removed"

    # Fallback to keyword regex matching
    for category, patterns in KEYWORD_MAP.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                return category

    # Default: Changed (most neutral)
    return "Changed"


def generate_changelog(commits: list[dict], version: str = "Unreleased") -> str:
    """Build the CHANGELOG body from categorized commits."""
    categories: dict[str, list[str]] = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}

    for c in commits:
        cat = categorize_commit(c["message"])
        line = f"- {c['message']} (`{c['hash']}` by {c['author']})"
        categories[cat].append(line)

    body_parts = []
    for cat in ["Added", "Changed", "Fixed", "Removed"]:
        if categories[cat]:
            body_parts.append(f"### {cat}")
            body_parts.extend(categories[cat])
            body_parts.append("")

    return "\n".join(body_parts).strip()


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--since-tag", type=str, help="Generate changelog for commits after this tag")
    parser.add_argument("--output", type=str, default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--repo", type=str, default=".", help="Path to git repository")
    parser.add_argument("--version", type=str, default="Unreleased", help="Version string for header")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    if not (repo_path / ".git").exists():
        print(f"Error: {repo_path} is not a git repository.", file=sys.stderr)
        sys.exit(1)

    # Determine range
    since_tag = args.since_tag
    if not since_tag:
        since_tag = get_latest_tag()
        if since_tag:
            print(f"Using latest tag as baseline: {since_tag}")
        else:
            print("No tags found. Generating changelog for all commits.")

    commits = get_commits(repo_path=str(repo_path), since_tag=since_tag)
    if not commits:
        print("No commits found in range. Nothing to generate.")
        sys.exit(0)

    print(f"Found {len(commits)} commit(s) to categorize.")

    body = generate_changelog(commits, version=args.version)
    today = datetime.now().strftime("%Y-%m-%d")
    output = CHANGELOG_TEMPLATE.format(version=args.version, date=today, body=body)

    out_path = Path(args.output)
    out_path.write_text(output, encoding="utf-8")
    print(f"✅ CHANGELOG written to {out_path.resolve()}")


if __name__ == "__main__":
    main()
