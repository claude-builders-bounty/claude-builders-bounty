#!/usr/bin/env python3
"""
CHANGELOG Generator from Git History
Bounty: claude-builders-bounty/claude-builders-bounty #1
Author: FanLi (范蠡)
"""

import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Commit categorization keywords - pre-built for efficiency
KEYWORD_MAP = {
    kw: cat
    for cat, keywords in {
        "Added": ["add", "create", "new", "implement", "feature", "introduce"],
        "Fixed": ["fix", "bug", "patch", "resolve", "correct", "repair"],
        "Changed": ["change", "update", "modify", "refactor", "improve", "enhance"],
        "Removed": ["remove", "delete", "drop", "deprecate", "clean"],
    }.items()
    for kw in keywords
}

# Category display order
CATEGORY_ORDER = ["Added", "Changed", "Fixed", "Removed"]


def run_git(args: list[str]) -> str:
    """Run a git command and return stdout"""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def get_last_tag() -> str | None:
    """Get the last git tag"""
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None


def get_commits_since_tag(tag: str | None = None) -> list[dict]:
    """Get commits since tag (or all commits if no tag)"""
    range_spec = f"{tag}..HEAD" if tag else "HEAD"

    try:
        output = run_git(["log", range_spec, "--pretty=format:%H|%ad|%s", "--date=short"])
    except subprocess.CalledProcessError:
        return []

    if not output:
        return []

    # Parse commits using list comprehension
    parts_list = [line.split("|", 2) for line in output.split("\n") if line]
    return [
        {"hash": p[0][:8], "date": p[1], "message": p[2]}
        for p in parts_list
        if len(p) == 3
    ]


def categorize_commit(message: str) -> str:
    """Categorize commit based on message keywords using pre-built map"""
    message_lower = message.lower()
    return next(
        (cat for kw, cat in KEYWORD_MAP.items() if kw in message_lower),
        "Changed"
    )


def generate_changelog(commits: list[dict]) -> str:
    """Generate formatted CHANGELOG content"""
    # Categorize commits
    categorized = defaultdict(list)
    for commit in commits:
        categorized[categorize_commit(commit["message"])].append(commit)

    # Build CHANGELOG using extend
    lines = [
        "# Changelog",
        "",
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]

    for category in CATEGORY_ORDER:
        if not categorized.get(category):
            continue

        commit_lines = [
            f"- {c['message']} ({c['hash']}) - {c['date']}"
            for c in categorized[category]
        ]
        lines.extend([f"## {category}", "", *commit_lines, ""])

    return "\n".join(lines)


def main() -> int:
    """Main entry point"""
    # Get last tag
    last_tag = get_last_tag()
    print(f"Generating CHANGELOG since tag: {last_tag}" if last_tag else "No tags found, generating from all commits")

    # Get commits
    commits = get_commits_since_tag(last_tag)

    if not commits:
        print("No commits found")
        return 1

    print(f"Found {len(commits)} commits")

    # Generate and write CHANGELOG
    changelog = generate_changelog(commits)
    output_file = Path("CHANGELOG.md")
    output_file.write_text(changelog, encoding="utf-8")

    print(f"✅ CHANGELOG.md generated with {len(commits)} commits")
    print(f"📄 Output: {output_file.absolute()}")

    return 0


if __name__ == "__main__":
    exit(main())
