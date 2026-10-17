#!/usr/bin/env python3
"""
git-changelog-generator: Generates structured Keep-a-Changelog formatted CHANGELOG.md
from git commit history since the latest git tag.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CATEGORY_MAPPING = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "change": "Changed",
    "update": "Changed",
    "chore": "Changed",
    "style": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "docs": "Documentation",
    "doc": "Documentation",
    "remove": "Removed",
    "delete": "Removed",
    "deprecate": "Removed",
    "security": "Security",
    "sec": "Security",
}

SECTION_ORDER = ["Added", "Fixed", "Changed", "Removed", "Documentation", "Security", "Other"]


def run_git(args: List[str], cwd: Optional[Path] = None) -> str:
    """Executes a git command and returns stdout stripped."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd or Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def get_latest_tag(cwd: Optional[Path] = None) -> Optional[str]:
    """Resolves the latest reachable git tag."""
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    return tag if tag else None


def get_repo_remote_url(cwd: Optional[Path] = None) -> Optional[str]:
    """Gets origin remote URL cleaned for markdown links."""
    remote = run_git(["config", "--get", "remote.origin.url"], cwd=cwd)
    if not remote:
        return None
    # Convert git@github.com:owner/repo.git to https://github.com/owner/repo
    if remote.startswith("git@"):
        remote = remote.replace(":", "/").replace("git@", "https://")
    if remote.endswith(".git"):
        remote = remote[:-4]
    return remote


def parse_commit_line(line: str) -> Tuple[str, str, str, str]:
    """
    Parses 'hash|author|date|subject' format.
    Returns: (hash, author, date, subject)
    """
    parts = line.split("|", 3)
    if len(parts) < 4:
        return ("", "", "", line)
    return (parts[0], parts[1], parts[2], parts[3])


def categorize_commit(subject: str) -> Tuple[str, str, Optional[str]]:
    """
    Categorizes a commit subject based on Conventional Commits conventions.
    Returns: (Category, cleaned_message, scope)
    """
    # Regex matching conventional commit: feat(scope)!: message or feat: message
    match = re.match(r"^(\w+)(?:\(([^)]+)\))?!?:\s*(.*)$", subject)
    if match:
        prefix, scope, msg = match.groups()
        prefix = prefix.lower()
        category = CATEGORY_MAPPING.get(prefix, "Other")
        cleaned_msg = msg.strip() if msg else subject.strip()
        return category, cleaned_msg, scope
    return "Other", subject.strip(), None


def fetch_commits(since_tag: Optional[str] = None, cwd: Optional[Path] = None) -> List[Tuple[str, str, str, str]]:
    """Fetches commit log records in reverse chronological order."""
    git_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
    fmt = "%h|%an|%ad|%s"
    output = run_git(["log", git_range, f"--pretty=format:{fmt}", "--date=short"], cwd=cwd)
    if not output:
        return []
    lines = output.splitlines()
    return [parse_commit_line(line) for line in lines if line.strip()]


def generate_changelog_content(
    version: str,
    since_tag: Optional[str] = None,
    cwd: Optional[Path] = None,
    include_links: bool = True,
) -> str:
    """Constructs Keep a Changelog markdown string."""
    commits = fetch_commits(since_tag=since_tag, cwd=cwd)
    remote_url = get_repo_remote_url(cwd=cwd) if include_links else None
    today = datetime.date.today().strftime("%Y-%m-%d")

    categorized: Dict[str, List[str]] = defaultdict(list)

    for h, author, date, subject in commits:
        cat, msg, scope = categorize_commit(subject)
        
        commit_ref = f"[`{h}`]({remote_url}/commit/{h})" if (remote_url and h) else f"`{h}`"
        scope_prefix = f"**{scope}**: " if scope else ""
        item = f"- {scope_prefix}{msg} ({commit_ref})"
        categorized[cat].append(item)

    header = f"## [{version}] - {today}\n"
    if since_tag:
        header += f"*Changes since tag `{since_tag}`:*\n\n"
    else:
        header += "*Initial release and historical changes:*\n\n"

    sections = []
    for section in SECTION_ORDER:
        items = categorized.get(section, [])
        if items:
            sections.append(f"### {section}\n" + "\n".join(items) + "\n")

    if not sections:
        sections.append("### Changed\n- Routine maintenance and updates.\n")

    return header + "\n".join(sections)


def update_changelog_file(
    changelog_path: Path,
    new_entry: str,
) -> None:
    """Prepends new entry into existing CHANGELOG.md under # Changelog."""
    if not changelog_path.exists():
        content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n{new_entry}"
        changelog_path.write_text(content, encoding="utf-8")
        return

    existing = changelog_path.read_text(encoding="utf-8")
    
    # Locate first version heading or insert after initial title
    match = re.search(r"^##\s+\[", existing, flags=re.MULTILINE)
    if match:
        idx = match.start()
        updated = existing[:idx] + new_entry.strip() + "\n\n" + existing[idx:]
    else:
        updated = existing.strip() + "\n\n" + new_entry.strip() + "\n"

    changelog_path.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("--version", "-v", default="Unreleased", help="Version header name (default: Unreleased)")
    parser.add_argument("--since", "-s", default=None, help="Tag or commit reference to start from")
    parser.add_argument("--output", "-o", default=None, help="Path to CHANGELOG.md file to update")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog without writing to file")

    args = parser.parse_args()

    since_tag = args.since or get_latest_tag()
    content = generate_changelog_content(version=args.version, since_tag=since_tag)

    if args.dry_run or not args.output:
        print(content)
        if not args.dry_run and not args.output:
            print("\n💡 Tip: Use `--output CHANGELOG.md` to write or prepend to your file.", file=sys.stderr)
    else:
        out_path = Path(args.output).resolve()
        update_changelog_file(out_path, content)
        print(f"✅ Successfully updated {out_path}")


if __name__ == "__main__":
    main()
