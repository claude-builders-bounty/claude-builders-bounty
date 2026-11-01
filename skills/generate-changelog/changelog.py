#!/usr/bin/env python3
"""
Cross-Platform Changelog Generator from Git History (#1).
Generates or prepends a Keep a Changelog v1.1.0 release section to CHANGELOG.md.
"""

import argparse
from datetime import datetime
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

CATEGORIES = ["Added", "Fixed", "Changed", "Removed", "Security"]

HEADER = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
"""

def run_git_command(args: List[str]) -> Tuple[int, str]:
    try:
        proc = subprocess.run(["git"] + args, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip()
    except Exception as e:
        return 1, str(e)

def get_latest_tag() -> Optional[str]:
    code, tag = run_git_command(["describe", "--tags", "--abbrev=0"])
    return tag if code == 0 and tag else None

def fetch_commits(since_tag: Optional[str] = None) -> List[Tuple[str, str, str]]:
    if since_tag:
        git_range = f"{since_tag}..HEAD"
    else:
        git_range = "HEAD"

    code, out = run_git_command(["log", git_range, '--pretty=format:%h%x09%s%x09%an'])
    if code != 0 or not out:
        return []

    commits = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            sha = parts[0]
            msg = parts[1]
            author = parts[2] if len(parts) > 2 else "Unknown"
            commits.append((sha, msg, author))
    return commits

def categorize_commit(message: str) -> str:
    lower = message.lower().strip()

    if re.match(r"^(sec|security)(\(.*\))?:", lower) or any(w in lower for w in ["vulnerability", "cve", "sanitize"]):
        return "Security"
    elif re.match(r"^feat(\(.*\))?:", lower) or lower.startswith(("add", "implement", "support", "new")):
        return "Added"
    elif re.match(r"^fix(\(.*\))?:", lower) or lower.startswith(("bug", "patch", "resolve", "close", "repair")):
        return "Fixed"
    elif re.match(r"^(remove|delete|deprecate|drop)", lower):
        return "Removed"
    else:
        return "Changed"

def format_changelog_section(version: str, date_str: str, commits: List[Tuple[str, str, str]]) -> str:
    groups: Dict[str, List[str]] = {cat: [] for cat in CATEGORIES}

    for sha, msg, _ in commits:
        cat = categorize_commit(msg)
        # Clean conventional prefix for cleaner changelog entry
        clean_msg = re.sub(r"^(feat|fix|refactor|perf|chore|sec|style|docs|test)(\(.*\))?:\s*", "", msg, flags=re.I)
        groups[cat].append(f"- {clean_msg} (`{sha}`)")

    lines = [f"## [{version}] - {date_str}", ""]
    for cat in CATEGORIES:
        if groups[cat]:
            lines.append(f"### {cat}")
            for entry in groups[cat]:
                lines.append(entry)
            lines.append("")

    return "\n".join(lines).strip()

def update_changelog_file(output_path: str, new_section: str):
    if not os.path.exists(output_path):
        full_content = f"{HEADER}\n\n{new_section}\n"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_content)
        print(f"✅ Created new {output_path}")
    else:
        with open(output_path, "r", encoding="utf-8") as f:
            existing = f.read()

        # Check if version already exists
        version_header = new_section.splitlines()[0]
        if version_header in existing:
            print(f"⚠️ {version_header} already exists in {output_path}; skipping duplicate prepend.")
            return

        # Prepend after header if header exists
        if "# Changelog" in existing:
            parts = re.split(r"(# Changelog.*?\n\n)", existing, maxsplit=1, flags=re.DOTALL)
            if len(parts) >= 3:
                updated = parts[1] + new_section + "\n\n" + parts[2].lstrip()
            else:
                updated = f"{HEADER}\n\n{new_section}\n\n" + existing
        else:
            updated = f"{HEADER}\n\n{new_section}\n\n" + existing

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"✅ Prepended release notes to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate structured Keep a Changelog CHANGELOG.md from git history.")
    parser.add_argument("--version", "-v", default="Unreleased", help="Target release version name (default: Unreleased)")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output path for changelog (default: CHANGELOG.md)")
    parser.add_argument("--since", "-s", help="Starting git tag (default: auto-detected latest tag)")
    args = parser.parse_args()

    tag = args.since or get_latest_tag()
    if tag:
        print(f"🔍 Fetching commits since latest tag: {tag}")
    else:
        print("🔍 No tags found; fetching all commits in repository history")

    commits = fetch_commits(tag)
    print(f"✓ Found {len(commits)} commits to process")

    today = datetime.now().strftime("%Y-%m-%d")
    section = format_changelog_section(args.version, today, commits)

    print("\n" + "=" * 50)
    print(section)
    print("=" * 50 + "\n")

    update_changelog_file(args.output, section)

if __name__ == "__main__":
    main()
