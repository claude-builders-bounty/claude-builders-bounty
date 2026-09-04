#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History

Fetches commits since the last git tag (or initial commit) and auto-categorizes them
into Keep-a-Changelog standard categories:
- Added
- Fixed
- Changed
- Removed

Supports:
- python3 changelog.py
- python3 changelog.py --from-tag v1.0.0
- python3 changelog.py --output CHANGELOG.md
- python3 changelog.py --dry-run
"""

import sys
import os
import re
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, List, Dict


# Conventional Commit Category Mapping
CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "new": "Added",
    "fix": "Fixed",
    "bug": "Fixed",
    "hotfix": "Fixed",
    "patch": "Fixed",
    "refactor": "Changed",
    "perf": "Changed",
    "performance": "Changed",
    "style": "Changed",
    "update": "Changed",
    "change": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "docs": "Changed",
    "revert": "Removed",
    "remove": "Removed",
    "deprecate": "Removed",
    "delete": "Removed",
    "drop": "Removed"
}


def get_latest_git_tag() -> Optional[str]:
    """Retrieve the most recent reachable git tag, or None if no tags exist."""
    try:
        res = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=False
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None


def get_commits_since(from_tag: Optional[str] = None, to_ref: str = "HEAD") -> List[Dict[str, str]]:
    """Fetch list of commits between from_tag and to_ref."""
    if from_tag:
        git_range = f"{from_tag}..{to_ref}"
    else:
        git_range = to_ref

    cmd = ["git", "log", git_range, "--pretty=format:%H%x1f%h%x1f%s%x1f%an%x1f%ad", "--date=short"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        return []

    commits = []
    for line in res.stdout.strip().splitlines():
        parts = line.split("\x1f")
        if len(parts) >= 5:
            full_sha, short_sha, subject, author, date = parts[0], parts[1], parts[2], parts[3], parts[4]
            commits.append({
                "sha": full_sha,
                "short_sha": short_sha,
                "subject": subject.strip(),
                "author": author.strip(),
                "date": date.strip()
            })
    return commits


def categorize_commit(subject: str) -> Tuple[str, str]:
    """
    Categorize commit message by conventional commit prefix or keyword.
    Returns (Category, CleanedDescription).
    """
    # Pattern: type(scope)!: message OR type: message
    match = re.match(r"^([a-zA-Z]+)(?:\(([^)]+)\))?!?:?\s*(.*)$", subject)
    if match:
        prefix = match.group(1).lower()
        scope = match.group(2)
        rest = match.group(3).strip()

        if prefix in CATEGORY_MAP:
            category = CATEGORY_MAP[prefix]
            if scope:
                cleaned = f"**{scope}:** {rest}" if rest else f"**{scope}**"
            else:
                cleaned = rest if rest else subject
            return category, cleaned

    # Keyword heuristics if not conventional commit
    sub_lower = subject.lower()
    if sub_lower.startswith(("add ", "create ", "new ", "implement ")):
        return "Added", subject
    if sub_lower.startswith(("fix ", "resolve ", "patch ", "bug ")):
        return "Fixed", subject
    if sub_lower.startswith(("remove ", "delete ", "drop ", "revert ")):
        return "Removed", subject

    return "Changed", subject


def generate_changelog_markdown(
    commits: List[Dict[str, str]],
    version_title: str = "Unreleased",
    from_tag: Optional[str] = None
) -> str:
    """Group commits and format into Keep-a-Changelog Markdown."""
    sections: Dict[str, List[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for c in commits:
        category, cleaned_desc = categorize_commit(c["subject"])
        # Format: - Description ([short_sha]) - Author
        entry = f"- {cleaned_desc} (`{c['short_sha']}`) - *{c['author']}*"
        sections[category].append(entry)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tag_info = f"since tag `{from_tag}`" if from_tag else "initial release"

    lines = [
        f"## [{version_title}] - {today}",
        f"*{len(commits)} commits {tag_info}*",
        ""
    ]

    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = sections[cat]
        if items:
            lines.append(f"### {cat}")
            lines.extend(items)
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate structured Keep-a-Changelog CHANGELOG from git history")
    parser.add_argument("--from-tag", type=str, default=None, help="Git tag or commit to start from (defaults to latest tag)")
    parser.add_argument("--to-ref", type=str, default="HEAD", help="Git ref to stop at (default: HEAD)")
    parser.add_argument("--title", type=str, default="Unreleased", help="Version title (default: Unreleased)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output file path (e.g. CHANGELOG.md)")
    parser.add_argument("--dry-run", action="store_true", help="Print output to stdout without modifying files")

    args = parser.parse_args()

    from_tag = args.from_tag or get_latest_git_tag()
    commits = get_commits_since(from_tag, args.to_ref)

    if not commits:
        print(f"No new commits found since '{from_tag or 'beginning of history'}'.")
        sys.exit(0)

    markdown = generate_changelog_markdown(commits, version_title=args.title, from_tag=from_tag)

    if args.output and not args.dry_run:
        out_path = Path(args.output)
        if out_path.exists():
            existing = out_path.read_text(encoding="utf-8")
            # If # Changelog header exists, insert under it
            if existing.startswith("# Changelog"):
                new_content = existing.replace("# Changelog\n", f"# Changelog\n\n{markdown}\n", 1)
            else:
                new_content = f"# Changelog\n\n{markdown}\n\n---\n\n{existing}"
        else:
            new_content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{markdown}"

        out_path.write_text(new_content, encoding="utf-8")
        print(f"Changelog successfully written to {args.output}")

    print(markdown)


if __name__ == "__main__":
    main()
