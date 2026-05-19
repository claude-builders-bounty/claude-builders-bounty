#!/usr/bin/env python3
"""
CHANGELOG Generator — Claude Code Skill
Generates a structured CHANGELOG.md from git history since the last tag.
"""

import subprocess
import re
import sys
import argparse
from datetime import datetime

DEFAULT_OUTPUT = "CHANGELOG.md"

def get_last_tag():
    """Get the last git tag"""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def get_all_tags():
    """Get all git tags sorted by date"""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-creatordate"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            return [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
        return []
    except Exception:
        return []

def get_commits_since_tag(tag=None):
    """Get all commits since the last tag (or all commits if no tag)"""
    cmd = ["git", "log", "--pretty=format:%H|%s|%an|%ai"]
    if tag:
        cmd.append(f"{tag}..HEAD")

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0][:8],
                "subject": parts[1],
                "author": parts[2],
                "date": parts[3]
            })
    return commits

def get_tag_date(tag):
    """Get the date of a specific tag"""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ai", tag],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""
    except Exception:
        return ""

def categorize_commit(subject):
    """Categorize commit based on conventional commit prefixes"""
    subject_lower = subject.lower()
    clean_subject = re.sub(r'^[a-z]+(\([^)]+\))?:', '', subject_lower).strip()

    if subject_lower.startswith("feat"):
        return "Added"
    elif subject_lower.startswith("fix"):
        return "Fixed"
    elif subject_lower.startswith("docs"):
        return "Changed"
    elif subject_lower.startswith("style"):
        return "Changed"
    elif subject_lower.startswith("refactor"):
        return "Changed"
    elif subject_lower.startswith("perf"):
        return "Changed"
    elif subject_lower.startswith("test"):
        return "Changed"
    elif subject_lower.startswith("chore"):
        return "Changed"
    elif subject_lower.startswith("remove") or subject_lower.startswith("del"):
        return "Removed"
    elif subject_lower.startswith("initial") or clean_subject.startswith("initial"):
        return "Added"
    elif "add" in clean_subject or "new" in clean_subject:
        return "Added"
    elif "fix" in clean_subject or "bug" in clean_subject:
        return "Fixed"
    elif "remove" in clean_subject or "delet" in clean_subject:
        return "Removed"
    else:
        return "Changed"

def group_commits(commits):
    """Group commits by category"""
    groups = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for commit in commits:
        category = categorize_commit(commit["subject"])
        groups[category].append(commit)
    return groups

def format_changelog(groups, since_tag=None, all_tags=None, output_file=None):
    """Generate formatted CHANGELOG.md content"""
    lines = []
    lines.append("# Changelog")
    lines.append("")

    if since_tag:
        lines.append(f"## [{since_tag}] - {datetime.now().strftime('%Y-%m-%d')}")
    else:
        lines.append(f"## Unreleased - {datetime.now().strftime('%Y-%m-%d')}")

    lines.append("")

    has_content = False
    for category in ["Added", "Fixed", "Changed", "Removed"]:
        commits = groups[category]
        if commits:
            has_content = True
            lines.append(f"### {category}")
            lines.append("")
            for commit in commits:
                # Clean up commit message for changelog
                subject = re.sub(r'^[a-z]+(\([^)]+\))?:\s*', '', commit["subject"])
                lines.append(f"- {subject} ({commit['hash']})")
            lines.append("")

    if not has_content:
        lines.append("*No significant changes.*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Add previous tags section if available
    if all_tags and len(all_tags) > 1:
        lines.append("## Previous Releases")
        lines.append("")
        for tag in all_tags[1:6]:  # Show last 5 previous tags
            lines.append(f"- [{tag}]()")
        lines.append("")

    lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from git history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python changelog.py                    # Generate CHANGELOG.md for commits since last tag
  python changelog.py -o my_changelog.md # Custom output file
  python changelog.py --all              # Include all commits (no tag filter)
  python changelog.py --list-tags        # List all available tags
        """
    )
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT,
                        help=f"Output file path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--all", action="store_true",
                        help="Include all commits, not just since last tag")
    parser.add_argument("--list-tags", action="store_true",
                        help="List all available tags and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print to stdout instead of writing file")

    args = parser.parse_args()

    # List tags mode
    if args.list_tags:
        tags = get_all_tags()
        if tags:
            print("Available tags:")
            for tag in tags:
                print(f"  - {tag}")
        else:
            print("No tags found in this repository.")
        return 0

    # Get tag and commits
    since_tag = None if args.all else get_last_tag()
    commits = get_commits_since_tag(since_tag)
    all_tags = get_all_tags()

    if not commits:
        print("No commits found.", file=sys.stderr)
        if not since_tag and not args.all:
            print("Hint: No tags found. Use --all to include all commits.", file=sys.stderr)
        return 1

    # Group and format
    groups = group_commits(commits)
    content = format_changelog(groups, since_tag, all_tags, args.output)

    # Output
    if args.dry_run or args.output == "-":
        print(content)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ CHANGELOG generated: {args.output}")
        print(f"   Found {len(commits)} commits" + (f" since tag '{since_tag}'" if since_tag else ""))

    return 0

if __name__ == "__main__":
    sys.exit(main())
