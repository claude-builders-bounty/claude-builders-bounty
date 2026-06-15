#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history between tags.

Usage:
    python3 changelog.py [--tag-prefix v] [--output CHANGELOG.md]

Auto-categorizes commits into: Added, Fixed, Changed, Removed.
"""

import subprocess
import argparse
from datetime import date

CATEGORIES = {
    "Added": ["add", "feat", "new", "implement", "create", "introduce"],
    "Fixed": ["fix", "bug", "patch", "resolve", "repair", "correct"],
    "Changed": ["update", "change", "modify", "refactor", "improve", "tweak", "adjust", "rename", "move"],
    "Removed": ["remove", "delete", "drop", "deprecate", "clean"],
}


def get_tags(tag_prefix: str) -> list[str]:
    """Get sorted list of git tags."""
    result = subprocess.run(
        ["git", "tag", "--sort=-creatordate"],
        capture_output=True, text=True
    )
    tags = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
    if tag_prefix:
        tags = [t for t in tags if t.startswith(tag_prefix)]
    return tags


def get_commits_between(from_ref: str | None, to_ref: str) -> list[tuple[str, str]]:
    """Get commits between two refs as (hash, message) pairs."""
    range_spec = f"{from_ref}..{to_ref}" if from_ref else to_ref
    result = subprocess.run(
        ["git", "log", range_spec, "--pretty=format:%h %s"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    commits = []
    for line in lines:
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append((parts[0], parts[1]))
    return commits


def categorize(message: str) -> str:
    """Categorize a commit message by keyword matching."""
    msg_lower = message.lower()
    for category, keywords in CATEGORIES.items():
        if any(kw in msg_lower for kw in keywords):
            return category
    return "Changed"


def group_commits(commits: list[tuple[str, str]]) -> dict[str, list[tuple[str, str]]]:
    """Group commits into categories."""
    groups: dict[str, list[tuple[str, str]]] = {c: [] for c in CATEGORIES}
    for h, msg in commits:
        cat = categorize(msg)
        groups[cat].append((h, msg))
    return groups


def generate_changelog(version: str, groups: dict[str, list[tuple[str, str]]], today: str) -> str:
    """Generate the markdown changelog content."""
    lines = [
        f"# Changelog",
        "",
        f"## [{version}] - {today}",
        "",
    ]
    for category in ["Added", "Fixed", "Changed", "Removed"]:
        entries = groups.get(category, [])
        if not entries:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for h, msg in entries:
            lines.append(f"- {msg} ({h})")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git tags")
    parser.add_argument("--tag-prefix", default="", help="Tag prefix to filter (e.g. 'v')")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--append", action="store_true", help="Append to existing CHANGELOG instead of overwriting")
    args = parser.parse_args()

    tags = get_tags(args.tag_prefix)
    if len(tags) < 2:
        print("⚠️  Need at least 2 tags to generate changelog")
        return

    # Latest release = most recent tag
    version = tags[0]
    previous = tags[1] if len(tags) > 1 else None

    commits = get_commits_between(previous, version if not previous else "HEAD")
    if not commits:
        print(f"ℹ️  No commits found between {previous} and {version}")
        return

    groups = group_commits(commits)
    today_str = date.today().isoformat()
    changelog = generate_changelog(version, groups, today_str)

    mode = "a" if args.append else "w"
    with open(args.output, mode) as f:
        f.write(changelog + "\n")

    total = sum(len(v) for v in groups.values())
    print(f"✅ Generated {args.output} — {total} commits across {len([c for c in groups if groups[c]])} categories")


if __name__ == "__main__":
    main()
