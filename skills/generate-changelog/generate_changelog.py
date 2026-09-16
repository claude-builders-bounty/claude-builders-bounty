#!/usr/bin/env python3
"""
generate_changelog.py - Structured CHANGELOG.md Generator from Git History

Parses git commit messages (conventional commits & standard messages) and
generates/updates a Keep a Changelog compliant CHANGELOG.md.
"""

import os
import sys
import re
import subprocess
import argparse
from datetime import datetime
from collections import defaultdict

CATEGORIES = {
    "Added": [
        r"^feat(\(.*\))?:",
        r"^feature(\(.*\))?:",
        r"^add(\(.*\))?:",
        r"^added:",
        r"^new:",
    ],
    "Fixed": [
        r"^fix(\(.*\))?:",
        r"^bugfix(\(.*\))?:",
        r"^hotfix(\(.*\))?:",
        r"^patch(\(.*\))?:",
        r"^fixed:",
    ],
    "Changed": [
        r"^refactor(\(.*\))?:",
        r"^perf(\(.*\))?:",
        r"^performance(\(.*\))?:",
        r"^change(\(.*\))?:",
        r"^chore(\(.*\))?:",
        r"^docs(\(.*\))?:",
        r"^style(\(.*\))?:",
        r"^build(\(.*\))?:",
        r"^ci(\(.*\))?:",
        r"^update(\(.*\))?:",
    ],
    "Removed": [
        r"^remove(\(.*\))?:",
        r"^delete(\(.*\))?:",
        r"^revert(\(.*\))?:",
        r"^deprecate(\(.*\))?:",
    ],
    "Security": [
        r"^sec(\(.*\))?:",
        r"^security(\(.*\))?:",
    ],
}


def run_git_command(args, cwd=None):
    """Run a git command and return its stdout as string."""
    try:
        res = subprocess.run(
            ["git"] + args,
            cwd=cwd or os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""
    except Exception as e:
        return ""


def get_latest_tag(cwd=None):
    """Retrieve the most recent git tag, or None if no tags exist."""
    tag = run_git_command(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    if not tag:
        tags = run_git_command(["tag", "--sort=-creatordate"], cwd=cwd)
        if tags:
            tag = tags.splitlines()[0].strip()
    return tag if tag else None


def get_commits_since(tag=None, cwd=None):
    """Get list of commits since tag (or all commits if tag is None)."""
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    log_output = run_git_command(
        ["log", rev_range, '--pretty=format:%h%x09%an%x09%ad%x09%s', "--date=short", "--no-merges"],
        cwd=cwd
    )
    if not log_output:
        return []

    commits = []
    for line in log_output.splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "date": parts[2],
                "subject": parts[3]
            })
    return commits


def categorize_commit(subject):
    """Determine the Keep a Changelog category and clean subject."""
    clean_sub = subject.strip()
    
    # Check prefixes
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            match = re.match(pat, clean_sub, re.IGNORECASE)
            if match:
                # Strip prefix
                trimmed = clean_sub[match.end():].strip()
                # Capitalize first letter
                if trimmed:
                    trimmed = trimmed[0].upper() + trimmed[1:]
                return cat, trimmed or clean_sub

    # Heuristic matching if conventional commit prefix is missing
    lower_sub = clean_sub.lower()
    if any(k in lower_sub for k in ["fix", "bug", "issue", "resolve", "patch", "error", "crash"]):
        return "Fixed", clean_sub
    elif any(k in lower_sub for k in ["add", "feat", "new", "create", "support", "initial"]):
        return "Added", clean_sub
    elif any(k in lower_sub for k in ["remove", "deprecat", "delete", "drop", "revert"]):
        return "Removed", clean_sub
    elif any(k in lower_sub for k in ["security", "vulnerab", "cve"]):
        return "Security", clean_sub
    else:
        return "Changed", clean_sub


def build_changelog_section(version_title, commits, release_date=None):
    """Generate Markdown text for a single version/release section."""
    if not release_date:
        release_date = datetime.now().strftime("%Y-%m-%d")

    grouped = defaultdict(list)
    for c in commits:
        cat, msg = categorize_commit(c["subject"])
        grouped[cat].append((msg, c["hash"]))

    lines = []
    lines.append(f"## [{version_title}] - {release_date}")
    lines.append("")

    order = ["Added", "Changed", "Fixed", "Removed", "Security"]
    has_entries = False

    for cat in order:
        if grouped[cat]:
            has_entries = True
            lines.append(f"### {cat}")
            for msg, chash in grouped[cat]:
                lines.append(f"- {msg} (`{chash}`)")
            lines.append("")

    if not has_entries:
        lines.append("- No significant changes recorded.")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def generate_full_changelog(output_path="CHANGELOG.md", version="Unreleased", since_tag=None, cwd=None, release_date=None):
    """Generate or update the CHANGELOG.md file."""
    last_tag = since_tag if since_tag else get_latest_tag(cwd=cwd)
    commits = get_commits_since(tag=last_tag, cwd=cwd)

    new_section = build_changelog_section(version, commits, release_date=release_date)

    header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

    file_full_path = os.path.join(cwd or os.getcwd(), output_path)

    if os.path.exists(file_full_path):
        with open(file_full_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Check if header exists
        if "# Changelog" in existing_content:
            # Insert new section after header
            split_point = existing_content.find("## ")
            if split_point != -1:
                content = existing_content[:split_point] + new_section + "\n" + existing_content[split_point:]
            else:
                content = existing_content.rstrip() + "\n\n" + new_section
        else:
            content = header + new_section + "\n" + existing_content
    else:
        content = header + new_section

    with open(file_full_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_full_path, len(commits)


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured CHANGELOG.md from git commit history."
    )
    parser.add_argument(
        "-o", "--output", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)"
    )
    parser.add_argument(
        "-v", "--version", default="Unreleased", help="Version header (default: Unreleased)"
    )
    parser.add_argument(
        "-t", "--tag", default=None, help="Calculate commits since specific git tag"
    )
    parser.add_argument(
        "--stdout", action="store_true", help="Print changelog section to stdout instead of file"
    )
    parser.add_argument(
        "--date", default=None, help="Release date for the section header, YYYY-MM-DD (default: today)"
    )

    args = parser.parse_args()

    last_tag = args.tag if args.tag else get_latest_tag()
    commits = get_commits_since(tag=last_tag)

    if args.stdout:
        print(build_changelog_section(args.version, commits, release_date=args.date))
        return
    out_file, count = generate_full_changelog(
        output_path=args.output,
        version=args.version,
        since_tag=args.tag,
        release_date=args.date
    )
    print(f"Successfully processed {count} commits since '{last_tag or 'initial commit'}'.")
    print(f"Updated {out_file}")


if __name__ == "__main__":
    main()
