#!/usr/bin/env python3
"""
Automated Git Changelog Generator
Bounty #1: Generates structured CHANGELOG.md from git commit history.

Usage:
  python3 generate_changelog.py [--version VERSION] [--tag-prefix v] [--output CHANGELOG.md] [--since TAG]
  bash changelog.sh
"""

import sys
import subprocess
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Conventional commit mappings to "Keep a Changelog" categories
CATEGORY_MAPPINGS = [
    ("Added", re.compile(r'^(feat|add|feature)(\(.*?\))?:\s*(.*)', re.IGNORECASE)),
    ("Fixed", re.compile(r'^(fix|bugfix|patch|hotfix)(\(.*?\))?:\s*(.*)', re.IGNORECASE)),
    ("Removed", re.compile(r'^(remove|delete|deprecate)(\(.*?\))?:\s*(.*)', re.IGNORECASE)),
    ("Changed", re.compile(r'^(refactor|perf|change|update|chore|docs|style|test|build|ci)(\(.*?\))?:\s*(.*)', re.IGNORECASE)),
]

def run_git_command(args: List[str]) -> str:
    """Run a git command and return its standard output."""
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""

def get_latest_git_tag() -> Optional[str]:
    """Retrieve the most recent git tag, or None if no tags exist."""
    tag = run_git_command(["describe", "--tags", "--abbrev=0"])
    return tag if tag else None

def get_git_commits(since_ref: Optional[str] = None) -> List[Tuple[str, str, str, str]]:
    """
    Fetch commits since given ref (or all commits if None).
    Returns list of tuples: (hash, author, date_iso, subject)
    """
    cmd = ["log", "--no-merges", "--format=%h|%an|%as|%s"]
    if since_ref:
        cmd.append(f"{since_ref}..HEAD")

    raw = run_git_command(cmd)
    if not raw:
        return []

    commits = []
    for line in raw.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append((parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()))
    return commits

def categorize_commits(commits: List[Tuple[str, str, str, str]]) -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Sort commits into Added, Fixed, Changed, Removed categories.
    Returns dictionary mapping category -> list of (message, hash, author).
    """
    categorized: Dict[str, List[Tuple[str, str, str]]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for sha, author, date_str, subject in commits:
        clean_subject = subject.strip()
        matched = False

        for cat_name, pattern in CATEGORY_MAPPINGS:
            m = pattern.match(clean_subject)
            if m:
                # Extract clean description without conventional prefix
                desc = m.group(3).strip() if m.group(3) else clean_subject
                # Capitalize first letter
                if desc:
                    desc = desc[0].upper() + desc[1:]
                categorized[cat_name].append((desc, sha, author))
                matched = True
                break

        if not matched:
            # Fallback heuristic analysis
            lower_sub = clean_subject.lower()
            if any(w in lower_sub for w in ["add", "feat", "new", "create", "support"]):
                categorized["Added"].append((clean_subject, sha, author))
            elif any(w in lower_sub for w in ["fix", "bug", "patch", "resolve", "correct"]):
                categorized["Fixed"].append((clean_subject, sha, author))
            elif any(w in lower_sub for w in ["remove", "delete", "drop", "deprecate"]):
                categorized["Removed"].append((clean_subject, sha, author))
            else:
                categorized["Changed"].append((clean_subject, sha, author))

    return categorized

def format_changelog_section(version: str, date_str: str, categorized: Dict[str, List[Tuple[str, str, str]]]) -> str:
    """Format a single release section in Markdown according to Keep a Changelog standard."""
    lines = [f"## [{version}] - {date_str}"]

    has_entries = False
    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categorized.get(cat, [])
        if items:
            has_entries = True
            lines.append(f"\n### {cat}")
            for desc, sha, author in items:
                lines.append(f"- {desc} ([`{sha}`]) - *{author}*")

    if not has_entries:
        lines.append("\n*No user-facing changes in this release.*")

    lines.append("")
    return "\n".join(lines)

def generate_changelog(version: str = "Unreleased", since_tag: Optional[str] = None, output_file: Optional[str] = None) -> str:
    """Main pipeline to generate or update CHANGELOG.md."""
    if not since_tag:
        since_tag = get_latest_git_tag()

    commits = get_git_commits(since_tag)
    today = datetime.now().strftime("%Y-%m-%d")
    categorized = categorize_commits(commits)
    new_section = format_changelog_section(version, today, categorized)

    header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

    final_content = ""
    if output_file and Path(output_file).exists():
        existing = Path(output_file).read_text(encoding="utf-8")
        if "# Changelog" in existing:
            # Prepend new section after main header
            parts = existing.split("## ", 1)
            if len(parts) == 2:
                final_content = parts[0].rstrip() + "\n\n" + new_section + "\n## " + parts[1]
            else:
                final_content = existing.rstrip() + "\n\n" + new_section
        else:
            final_content = header + new_section + "\n" + existing
    else:
        final_content = header + new_section

    if output_file:
        Path(output_file).write_text(final_content, encoding="utf-8")

    return final_content

def main():
    parser = argparse.ArgumentParser(description="Structured Git Changelog Generator")
    parser.add_argument("--version", default="Unreleased", help="Version header (e.g. 1.0.0, v2.1.0, or Unreleased)")
    parser.add_argument("--since", help="Git reference/tag to collect commits from (default: latest git tag)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Target output file path (default: CHANGELOG.md)")
    parser.add_argument("--stdout", action="store_true", help="Print changelog markdown directly to stdout")

    args = parser.parse_args()

    out_path = None if args.stdout else args.output
    content = generate_changelog(version=args.version, since_tag=args.since, output_file=out_path)

    if args.stdout:
        print(content)
    else:
        print(f"[+] Successfully generated changelog at: {args.output}")

if __name__ == "__main__":
    main()
