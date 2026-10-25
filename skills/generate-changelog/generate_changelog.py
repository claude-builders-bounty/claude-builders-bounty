#!/usr/bin/env python3
"""
Structured CHANGELOG Generator from Git History
Repository: claude-builders-bounty
Author: @satyadilip
Target Issue: #1 ($50 Bounty)
"""

import sys
import os
import subprocess
import re
from datetime import datetime
from pathlib import Path


def run_git(args, cwd=None):
    res = subprocess.run(
        ["git"] + args,
        cwd=cwd or os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if res.returncode != 0:
        return ""
    return res.stdout.strip()


def get_latest_tag(cwd=None):
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    return tag if tag else None


def get_commits(since_tag=None, cwd=None):
    range_arg = f"{since_tag}..HEAD" if since_tag else "HEAD"
    log_format = "%h%x09%s%x09%an%x09%ad"
    raw = run_git(["log", range_arg, f"--pretty=format:{log_format}", "--date=short"], cwd=cwd)
    if not raw:
        return []

    commits = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            commits.append({
                "hash": parts[0],
                "subject": parts[1],
                "author": parts[2] if len(parts) > 2 else "",
                "date": parts[3] if len(parts) > 3 else ""
            })
    return commits


def categorize_commit(subject):
    """Categorize commit into Keep-a-Changelog standard sections."""
    sub_lower = subject.lower()

    # Added
    if re.match(r"^(feat|feature|add)(\(.*\))?:\s*", sub_lower) or any(k in sub_lower for k in ["add ", "new ", "create "]):
        clean = re.sub(r"^(feat|feature|add)(\(.*\))?:\s*", "", subject, flags=re.IGNORECASE)
        return "Added", clean.strip()

    # Fixed
    if re.match(r"^(fix|bug|patch)(\(.*\))?:\s*", sub_lower) or any(k in sub_lower for k in ["fix ", "resolve ", "bug "]):
        clean = re.sub(r"^(fix|bug|patch)(\(.*\))?:\s*", "", subject, flags=re.IGNORECASE)
        return "Fixed", clean.strip()

    # Removed
    if re.match(r"^(remove|deprecate|delete)(\(.*\))?:\s*", sub_lower) or any(k in sub_lower for k in ["remove ", "deprecate "]):
        clean = re.sub(r"^(remove|deprecate|delete)(\(.*\))?:\s*", "", subject, flags=re.IGNORECASE)
        return "Removed", clean.strip()

    # Changed (refactor, perf, chore, style, docs, update)
    clean = re.sub(r"^(change|refactor|perf|chore|style|docs|update)(\(.*\))?:\s*", "", subject, flags=re.IGNORECASE)
    return "Changed", clean.strip()


def generate_changelog_markdown(commits, tag=None, version_name="Unreleased"):
    date_str = datetime.now().strftime("%Y-%m-%d")
    header = f"## [{version_name}] - {date_str}\n"
    if tag:
        header += f"*Changes since tag `{tag}`*\n"

    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    for c in commits:
        cat, clean_msg = categorize_commit(c["subject"])
        categories[cat].append(f"- {clean_msg} (`{c['hash']}` by @{c['author']})")

    sections = [header]
    for cat_name, entries in categories.items():
        if entries:
            sections.append(f"### {cat_name}\n" + "\n".join(entries))

    return "\n\n".join(sections) + "\n"


def main():
    cwd = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else os.getcwd()
    output_file = Path(cwd) / "CHANGELOG.md"

    latest_tag = get_latest_tag(cwd)
    commits = get_commits(latest_tag, cwd)

    if not commits:
        print("No new commits found since last tag/initial commit.")
        sys.exit(0)

    new_section = generate_changelog_markdown(commits, tag=latest_tag)

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            existing = f.read()
        # Prepend to existing changelog after title
        if "# Changelog" in existing:
            parts = existing.split("# Changelog", 1)
            updated = f"# Changelog\n\n{new_section}\n" + parts[1].strip()
        else:
            updated = f"# Changelog\n\n{new_section}\n" + existing
    else:
        updated = (
            "# Changelog\n\n"
            "All notable changes to this project will be documented in this file.\n"
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"
            f"{new_section}"
        )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"🎉 CHANGELOG.md successfully updated at {output_file} ({len(commits)} commits processed).")


if __name__ == "__main__":
    main()
