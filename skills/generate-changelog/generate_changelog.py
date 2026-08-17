#!/usr/bin/env python3
"""
generate_changelog.py — Automated Structured Changelog Generator
Extracts git history, categorizes commits following Conventional Commits and Keep a Changelog standards,
and writes a clean CHANGELOG.md.

Zero dependencies (Python standard library only).
"""

import subprocess
import re
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Optional

CATEGORIES = {
    "Added": ["feat", "add", "new", "feature", "create", "implement"],
    "Fixed": ["fix", "bug", "patch", "resolve", "hotfix", "repair"],
    "Changed": ["change", "refactor", "update", "style", "chore", "mod", "rewrite", "bump"],
    "Performance": ["perf", "optimize", "speed", "fast", "performance", "memory"],
    "Security": ["sec", "security", "vuln", "cve", "auth", "sanitize"],
    "Removed": ["remove", "delete", "drop", "deprecated", "deprecate", "rm"]
}

def run_git_command(args: List[str], cwd: Optional[str] = None) -> Tuple[int, str]:
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode, res.stdout.strip()
    except Exception as e:
        return 1, str(e)

def get_latest_tag(cwd: Optional[str] = None) -> Optional[str]:
    code, out = run_git_command(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    if code == 0 and out:
        return out.strip()
    return None

def get_commits(since_ref: Optional[str] = None, cwd: Optional[str] = None) -> List[Dict[str, str]]:
    git_args = ["log", "--no-merges", "--pretty=format:%H%x1f%s%x1f%an%x1f%ad", "--date=short"]
    if since_ref:
        git_args.append(f"{since_ref}..HEAD")

    code, out = run_git_command(git_args, cwd=cwd)
    if code != 0 or not out:
        return []

    commits = []
    for line in out.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\x1f")
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0],
                "short_hash": parts[0][:7],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3]
            })
    return commits

def categorize_commit(subject: str) -> Tuple[str, str]:
    """Categorizes a commit message into a changelog section and cleans the description."""
    # Check Conventional Commits format: feat(scope): message or fix: message
    conv_match = re.match(r"^([a-zA-Z]+)(?:\((.*?)\))?(!)?:\s*(.*)$", subject)
    if conv_match:
        tag_type = conv_match.group(1).lower()
        scope = conv_match.group(2)
        desc = conv_match.group(4)

        prefix = f"**{scope}**: " if scope else ""
        clean_desc = prefix + desc.strip()

        for section, keywords in CATEGORIES.items():
            if tag_type in keywords:
                return section, clean_desc

    # Fallback keyword search
    clean_sub = subject.strip()
    lower_sub = clean_sub.lower()
    for section, keywords in CATEGORIES.items():
        for kw in keywords:
            if lower_sub.startswith(kw) or f" {kw} " in lower_sub:
                return section, clean_sub

    return "Changed", clean_sub

def generate_markdown(commits: List[Dict[str, str]], version_title: str = "Unreleased", release_date: Optional[str] = None) -> str:
    date_str = release_date or datetime.now().strftime("%Y-%m-%d")
    header = f"## [{version_title}] - {date_str}\n"

    sections: Dict[str, List[str]] = {cat: [] for cat in CATEGORIES}

    for c in commits:
        category, desc = categorize_commit(c["subject"])
        bullet = f"- {desc} ([`{c['short_hash']}`])"
        sections[category].append(bullet)

    content_lines = [header]
    has_entries = False

    for cat in ["Added", "Fixed", "Changed", "Performance", "Security", "Removed"]:
        items = sections[cat]
        if items:
            has_entries = True
            content_lines.append(f"\n### {cat}\n")
            content_lines.extend([f"{item}\n" for item in items])

    if not has_entries:
        content_lines.append("\n*No significant user-facing changes recorded.*\n")

    return "".join(content_lines)

def build_full_changelog(new_section: str, existing_changelog: Optional[str] = None) -> str:
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\nand this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"

    if not existing_changelog or not existing_changelog.strip():
        return header + new_section

    # If changelog already has header, insert new section below header
    if existing_changelog.startswith("# Changelog"):
        # Find first version heading
        match = re.search(r"\n(##\s+\[.*?\].*?\n)", existing_changelog)
        if match:
            split_pos = match.start(1)
            top = existing_changelog[:split_pos]
            bottom = existing_changelog[split_pos:]
            return top + new_section.rstrip() + "\n\n" + bottom.lstrip()
        else:
            return existing_changelog.rstrip() + "\n\n" + new_section
    else:
        return header + new_section.rstrip() + "\n\n" + existing_changelog.lstrip()

def main():
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG from git history.")
    parser.add_argument("--since", help="Git tag or commit reference to fetch commits from (defaults to latest tag)")
    parser.add_argument("--version", default="Unreleased", help="Version title for the new section (default: Unreleased)")
    parser.add_argument("--date", help="Release date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("--stdout", action="store_true", help="Print changelog section to stdout only")
    parser.add_argument("--dir", default=None, help="Target git repository directory (default: current directory)")

    args = parser.parse_args()

    repo_dir = args.dir or os.getcwd()
    since_ref = args.since or get_latest_tag(cwd=repo_dir)

    print(f"[*] Analyzing git history in: {repo_dir}")
    if since_ref:
        print(f"[*] Commits since: {since_ref}")
    else:
        print("[*] No previous tag found. Parsing full repository history.")

    commits = get_commits(since_ref=since_ref, cwd=repo_dir)
    print(f"[*] Found {len(commits)} commits to process.")

    new_section = generate_markdown(commits, version_title=args.version, release_date=args.date)

    if args.stdout:
        print("\n" + new_section)
        return

    output_path = os.path.join(repo_dir, args.output)
    existing_content = ""
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

    full_changelog = build_full_changelog(new_section, existing_content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_changelog)

    print(f"[SUCCESS] Changelog written to: {output_path}")

if __name__ == "__main__":
    main()
