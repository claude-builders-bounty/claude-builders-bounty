#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.

This script analyzes git commits and auto-categorizes them into:
- Added
- Fixed
- Changed
- Removed

Usage:
    generate_changelog.py [OPTIONS]

Options:
    -o, --output FILE    Output file path (default: CHANGELOG.md)
    -t, --tag TAG        Generate changelog from this tag (default: last tag)
    -a, --all            Generate changelog for all commits (ignore tags)
    -r, --repo PATH      Path to git repository (default: current directory)
    --no-links           Don't generate links to commits
    --version VERSION    Specify version for the new release
    -h, --help           Show help message

Example:
    python generate_changelog.py --version 1.0.0
    python generate_changelog.py --all
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def run_git_command(args: List[str], repo_path: str = ".") -> str:
    """Run a git command and return the output."""
    cmd = ["git", "-C", repo_path] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {' '.join(cmd)}", file=sys.stderr)
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def get_tags(repo_path: str = ".") -> List[str]:
    """Get all tags sorted by version (newest first)."""
    try:
        output = run_git_command(
            ["tag", "--sort=-version:refname"], repo_path
        )
        return output.split("\n") if output else []
    except Exception:
        return []


def get_commit_history(
    from_tag: Optional[str] = None, repo_path: str = "."
) -> List[Dict]:
    """Get commit history from a tag or from the beginning."""
    if from_tag:
        # Get commits since the tag
        log_format = "%H|%s|%an|%ad"
        cmd = [
            "log",
            f"{from_tag}..HEAD",
            f"--pretty=format:{log_format}",
            "--date=short",
        ]
    else:
        # Get all commits
        log_format = "%H|%s|%an|%ad"
        cmd = ["log", f"--pretty=format:{log_format}", "--date=short"]

    output = run_git_command(cmd, repo_path)

    commits = []
    for line in output.split("\n"):
        if line and "|" in line:
            parts = line.split("|", 3)
            if len(parts) >= 4:
                commits.append(
                    {
                        "hash": parts[0],
                        "subject": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                    }
                )
    return commits


def categorize_commit(subject: str) -> str:
    """Categorize a commit based on its subject line."""
    subject_lower = subject.lower()

    # Patterns for each category
    added_patterns = [
        r"^feat(?:\([^)]*\))?:",
        r"^feature(?:\([^)]*\))?:",
        r"^add(?:ed)?:",
        r"^new:",
        r"^introduce:",
        r"^\+\s*",
        r"^implement:",
        r"^create:",
    ]

    fixed_patterns = [
        r"^fix(?:\([^)]*\))?:",
        r"^bugfix(?:\([^)]*\))?:",
        r"^bug:",
        r"^resolve:",
        r"^patch:",
        r"^correct:",
    ]

    changed_patterns = [
        r"^change(?:\([^)]*\))?:",
        r"^update(?:\([^)]*\))?:",
        r"^refactor(?:\([^)]*\))?:",
        r"^improve(?:\([^)]*\))?:",
        r"^modify:",
        r"^optimize:",
        r"^enhance:",
        r"^perf(?:\([^)]*\))?:",
        r"^style(?:\([^)]*\))?:",
        r"^reformat:",
        r"^clean:",
        r"^cleanup:",
        r"^chore(?:\([^)]*\))?:",
        r"^build(?:\([^)]*\))?:",
        r"^ci(?:\([^)]*\))?:",
    ]

    removed_patterns = [
        r"^remove(?:\([^)]*\))?:",
        r"^delete(?:\([^)]*\))?:",
        r"^deprecate(?:\([^)]*\))?:",
        r"^drop:",
        r"^-\s*",
        r"^archive:",
    ]

    # Check each category
    for pattern in added_patterns:
        if re.search(pattern, subject_lower):
            return "Added"

    for pattern in fixed_patterns:
        if re.search(pattern, subject_lower):
            return "Fixed"

    for pattern in changed_patterns:
        if re.search(pattern, subject_lower):
            return "Changed"

    for pattern in removed_patterns:
        if re.search(pattern, subject_lower):
            return "Removed"

    # Default to "Other" for uncategorized commits
    return "Other"


def clean_commit_subject(subject: str) -> str:
    """Clean up the commit subject by removing prefixes."""
    # Remove conventional commit prefixes
    cleaned = re.sub(
        r"^(feat|feature|fix|bugfix|bug|change|update|refactor|improve|"
        r"remove|delete|deprecate|add|new|introduce|implement|create|"
        r"resolve|patch|correct|modify|optimize|enhance|perf|style|"
        r"reformat|clean|cleanup|chore|build|ci|drop|archive)"
        r"(\([^)]*\))?:\s*",
        "",
        subject,
        flags=re.IGNORECASE,
    )
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    # Capitalize first letter
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned or subject


def generate_changelog(
    commits: List[Dict],
    version: Optional[str] = None,
    include_links: bool = True,
    repo_url: Optional[str] = None,
) -> str:
    """Generate CHANGELOG content from commits."""
    changelog_lines = []

    # Header
    changelog_lines.append("# Changelog")
    changelog_lines.append("")
    changelog_lines.append(
        "All notable changes to this project will be documented in this file."
    )
    changelog_lines.append("")

    # Group commits by category
    categories: Dict[str, List[Dict]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Other": [],
    }

    for commit in commits:
        category = categorize_commit(commit["subject"])
        categories[category].append(commit)

    # Determine version and date
    today = datetime.now().strftime("%Y-%m-%d")
    version_str = version or "Unreleased"

    # Start with Unreleased or the new version
    changelog_lines.append(f"## [{version_str}]")
    if version:
        changelog_lines.append(f"### {today}")
    changelog_lines.append("")

    # Write each category
    for category in ["Added", "Fixed", "Changed", "Removed", "Other"]:
        if categories[category]:
            changelog_lines.append(f"### {category}")
            for commit in categories[category]:
                clean_subject = clean_commit_subject(commit["subject"])
                if include_links and repo_url:
                    short_hash = commit["hash"][:7]
                    link = f"{repo_url}/commit/{commit['hash']}"
                    changelog_lines.append(
                        f"- {clean_subject} ([{short_hash}]({link}))"
                    )
                elif include_links:
                    short_hash = commit["hash"][:7]
                    changelog_lines.append(f"- {clean_subject} ({short_hash})")
                else:
                    changelog_lines.append(f"- {clean_subject}")
            changelog_lines.append("")

    # Add footer
    changelog_lines.append(
        "<!-- Generated by git-changelog skill -->"
    )

    return "\n".join(changelog_lines)


def get_repo_url(repo_path: str = ".") -> Optional[str]:
    """Get the repository URL from git config."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        remote_url = result.stdout.strip()
        if remote_url:
            # Convert SSH URL to HTTPS
            if remote_url.startswith("git@"):
                remote_url = re.sub(
                    r"git@([^:]+):", r"https://\1/", remote_url
                )
            # Remove .git suffix
            remote_url = re.sub(r"\.git$", "", remote_url)
            return remote_url
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-o",
        "--output",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "-t",
        "--tag",
        help="Generate changelog from this tag (default: last tag)",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Generate changelog for all commits (ignore tags)",
    )
    parser.add_argument(
        "-r",
        "--repo",
        default=".",
        help="Path to git repository (default: current directory)",
    )
    parser.add_argument(
        "--no-links",
        action="store_true",
        help="Don't generate links to commits",
    )
    parser.add_argument(
        "--version",
        help="Specify version for the new release",
    )
    parser.add_argument(
        "--prepend",
        action="store_true",
        help="Prepend to existing CHANGELOG.md instead of overwriting",
    )

    args = parser.parse_args()

    # Get repository path
    repo_path = os.path.abspath(args.repo)

    # Verify it's a git repository
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(
            f"Error: {repo_path} is not a git repository",
            file=sys.stderr,
        )
        sys.exit(1)

    # Determine the starting tag
    from_tag = None
    if not args.all:
        if args.tag:
            from_tag = args.tag
        else:
            tags = get_tags(repo_path)
            if tags:
                from_tag = tags[0]  # Most recent tag
                print(
                    f"Generating changelog since tag: {from_tag}",
                    file=sys.stderr,
                )
            else:
                print(
                    "No tags found, generating changelog for all commits",
                    file=sys.stderr,
                )

    # Get commit history
    commits = get_commit_history(from_tag, repo_path)

    if not commits:
        print("No commits found", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(commits)} commits", file=sys.stderr)

    # Get repo URL for links
    repo_url = None if args.no_links else get_repo_url(repo_path)

    # Generate changelog
    changelog = generate_changelog(
        commits,
        version=args.version,
        include_links=not args.no_links,
        repo_url=repo_url,
    )

    # Write output
    output_path = os.path.join(repo_path, args.output)

    if args.prepend and os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        # Find the position after the header
        lines = existing_content.split("\n")
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("## ["):
                header_end = i
                break
        # Prepend new changelog
        new_content = changelog + "\n" + "\n".join(lines[header_end:])
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(changelog)

    print(f"Changelog written to: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()