#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Adheres to 'Keep a Changelog' (https://keepachangelog.com/) standards.
Works across Linux, macOS, and Windows.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


CONVENTIONAL_MAP = [
    (re.compile(r"^(feat|add|feature)(\(.*\))?:\s*(.*)", re.IGNORECASE), "Added"),
    (re.compile(r"^(fix|bug|patch|resolve)(\(.*\))?:\s*(.*)", re.IGNORECASE), "Fixed"),
    (re.compile(r"^(security|sec|vuln)(\(.*\))?:\s*(.*)", re.IGNORECASE), "Security"),
    (re.compile(r"^(remove|deprecate|del)(\(.*\))?:\s*(.*)", re.IGNORECASE), "Removed"),
    (re.compile(r"^(refactor|perf|change|update|chore|docs|style|build|ci)(\(.*\))?:\s*(.*)", re.IGNORECASE), "Changed"),
]

FALLBACK_KEYWORDS = [
    (re.compile(r"\b(fix|fixed|fixes|bug|patch)\b", re.IGNORECASE), "Fixed"),
    (re.compile(r"\b(add|added|feature|support|new)\b", re.IGNORECASE), "Added"),
    (re.compile(r"\b(remove|removed|delete|deprecated)\b", re.IGNORECASE), "Removed"),
    (re.compile(r"\b(security|vulnerability|cve)\b", re.IGNORECASE), "Security"),
]


def run_git_cmd(args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Execute git command returning exit code, stdout, stderr."""
    proc = subprocess.run(
        ["git"] + args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def get_latest_tag(cwd: Optional[Path] = None) -> Optional[str]:
    """Return the name of the most recent git tag, or None if no tags exist."""
    code, out, _ = run_git_cmd(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    return out if code == 0 and out else None


def get_commits_since(tag: Optional[str] = None, cwd: Optional[Path] = None) -> List[Tuple[str, str, str]]:
    """Fetch (hash, author, message) for commits since the given tag, or all if tag is None."""
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    fmt = "%h%x09%an%x09%s"
    code, out, err = run_git_cmd(["log", rev_range, f"--format={fmt}", "--no-merges"], cwd=cwd)
    if code != 0 or not out:
        return []

    commits = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            commits.append((parts[0], parts[1], parts[2]))
        elif len(parts) == 2:
            commits.append((parts[0], parts[1], ""))
    return commits


def categorize_commit(message: str) -> Tuple[str, str]:
    """Classify commit into category and clean summary."""
    clean_msg = message.strip()
    
    # Try conventional commit prefix matching
    for pattern, category in CONVENTIONAL_MAP:
        match = pattern.match(clean_msg)
        if match:
            scope = match.group(2) or ""
            desc = match.group(3).strip()
            if desc and len(desc) > 0:
                desc = desc[0].upper() + desc[1:]
            summary = f"**{scope.strip('()')}**: {desc}" if scope else desc
            return category, summary

    # Try fallback keyword matching
    for pattern, category in FALLBACK_KEYWORDS:
        if pattern.search(clean_msg):
            return category, clean_msg[0].upper() + clean_msg[1:]

    return "Changed", clean_msg[0].upper() + clean_msg[1:] if clean_msg else "Maintenance updates"


def build_changelog_section(version_title: str, date_str: str, commits: List[Tuple[str, str, str]]) -> str:
    """Generate Markdown for a single release section."""
    categories: Dict[str, List[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Security": []
    }

    for chash, author, message in commits:
        cat, summary = categorize_commit(message)
        categories[cat].append(f"- {summary} ([`{chash}`])")

    lines = [f"## [{version_title}] - {date_str}"]

    has_content = False
    for cat in ["Added", "Fixed", "Changed", "Removed", "Security"]:
        items = categories[cat]
        if items:
            has_content = True
            lines.append(f"\n### {cat}")
            lines.extend(items)

    if not has_content:
        lines.append("\n- Maintenance and internal improvements.")

    return "\n".join(lines)


def generate_changelog(
    target_file: Optional[Path] = None,
    version: str = "Unreleased",
    cwd: Optional[Path] = None
) -> str:
    """Generate and optionally write CHANGELOG.md."""
    tag = get_latest_tag(cwd=cwd)
    commits = get_commits_since(tag, cwd=cwd)
    date_str = datetime.date.today().isoformat()
    section = build_changelog_section(version, date_str, commits)

    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"

    if target_file and target_file.exists():
        existing_text = target_file.read_text(encoding="utf-8")
        if "# Changelog" in existing_text:
            # Insert section after main header
            parts = existing_text.split("## ", 1)
            if len(parts) == 2:
                new_content = parts[0] + section + "\n\n## " + parts[1]
            else:
                new_content = header + section + "\n"
        else:
            new_content = header + section + "\n\n" + existing_text
        target_file.write_text(new_content, encoding="utf-8")
        return new_content
    elif target_file:
        full_doc = header + section + "\n"
        target_file.write_text(full_doc, encoding="utf-8")
        return full_doc
    else:
        return header + section + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("-o", "--output", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("-v", "--version", default="Unreleased", help="Version title (default: Unreleased)")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing file")
    args = parser.parse_args()

    out_path = None if args.stdout else Path(args.output or "CHANGELOG.md")
    result = generate_changelog(target_file=out_path, version=args.version)
    if args.stdout or not out_path:
        print(result)
    else:
        print(f"Generated {out_path} ({len(result.splitlines())} lines).")


if __name__ == "__main__":
    main()
