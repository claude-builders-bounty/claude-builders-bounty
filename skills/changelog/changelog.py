#!/usr/bin/env python3
"""
changelog.py — Generate a structured CHANGELOG.md from git history.

Auto-categorizes commits into Added / Fixed / Changed / Removed sections
with version grouping, commit links, and proper markdown formatting.

Usage:
    python changelog.py                     # Last tag → HEAD
    python changelog.py --since v1.0.0      # Specific tag → HEAD
    python changelog.py --full              # Full history (no tags)
    python changelog.py --output RELEASES.md
    python changelog.py --repo /path/to/repo
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone


def run_git(cmd: list[str], cwd: str | None = None) -> str:
    """Run a git command and return stdout. Exit on failure."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
            timeout=30,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: git {' '.join(cmd)} failed:\n{e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: git is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)


def get_tags(cwd: str | None = None) -> list[str]:
    """Get all tags sorted by creation date (newest first)."""
    output = run_git(["tag", "--sort=-creatordate"], cwd=cwd)
    return output.split("\n") if output else []


def get_commits(
    since: str | None = None,
    cwd: str | None = None,
) -> list[dict]:
    """Get commits with hash, subject, body, author, date."""
    range_arg = f"{since}..HEAD" if since else "HEAD"
    # We collect enough context to categorize properly
    fmt = "--format=----COMMIT----%n%H%n%an%n%aI%n%s%n%b"
    args = ["log", fmt, "--no-merges"]
    if since:
        args.append(range_arg)
    else:
        # Full history from the beginning
        args.append("--all")

    output = run_git(args, cwd=cwd)
    if not output:
        return []

    commits = []
    for block in output.split("----COMMIT----\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n", 4)
        if len(lines) < 5:
            continue
        commits.append({
            "hash": lines[0],
            "author": lines[1],
            "date": lines[2],
            "subject": lines[3],
            "body": lines[4].strip() if len(lines) > 4 else "",
        })
    return commits


def categorize_commit(subject: str, body: str) -> str:
    """Categorize a commit into Added/Fixed/Changed/Removed/Other.

    Uses conventional commit prefixes first, then falls back to
    natural language pattern matching.
    """
    lower_subject = subject.lower().strip()
    lower_body = body.lower().strip() if body else ""

    # Conventional commit prefixes
    cc_match = re.match(
        r"^(feat|fix|refactor|perf|docs|style|test|chore|ci|build|revert)"
        r"(?:\([^)]*\))?:\s*(.*)",
        lower_subject,
    )
    if cc_match:
        prefix = cc_match.group(1)
        if prefix == "feat":
            return "Added"
        elif prefix == "fix":
            return "Fixed"
        elif prefix == "perf":
            return "Changed"
        elif prefix == "revert":
            return "Removed"
        elif prefix in ("refactor", "docs", "style", "test", "chore", "ci", "build"):
            return "Changed"

    # Natural language prefixes
    if re.match(r"^(add|new|implement|create|introduce|support|enable)\b", lower_subject):
        return "Added"
    if re.match(r"^(fix|patch|hotfix|bugfix|resolve|correct)\b", lower_subject):
        return "Fixed"
    if re.match(r"^(remove|delete|drop|deprecate|revert|cleanup|purge)\b", lower_subject):
        return "Removed"
    if re.match(r"^(update|change|refactor|improve|enhance|upgrade|migrate|redesign|simplify)\b", lower_subject):
        return "Changed"
    if re.match(r"^(bump|upgrade|downgrade|pin)\b", lower_subject):
        return "Changed"

    # Check body for clues
    if re.search(r"\b(break|breaking|incompatible)\b", lower_subject + " " + lower_body):
        return "Changed"

    return "Other"


def strip_prefix(subject: str) -> str:
    """Strip conventional commit prefix for clean display."""
    return re.sub(
        r"^(feat|fix|refactor|perf|docs|style|test|chore|ci|build|revert)"
        r"(?:\([^)]*\))?:\s*",
        "",
        subject,
        flags=re.IGNORECASE,
    ).strip()


def format_commit_line(commit: dict) -> str:
    """Format a single commit as a markdown list item with hash link."""
    short_hash = commit["hash"][:7]
    display = strip_prefix(commit["subject"])
    # Link to commit if remote origin exists
    return f"- {display} ([`{short_hash}`]({get_commit_url(commit['hash'], commit.get('cwd'))}))"


def get_commit_url(hash: str, cwd: str | None = None) -> str:
    """Build a commit URL from git remote."""
    try:
        remote = run_git(["config", "--get", "remote.origin.url"], cwd=cwd)
        if not remote:
            return f"#{hash[:7]}"
        # Handle various remote URL formats
        if remote.startswith("git@github.com:"):
            remote = remote.replace("git@github.com:", "https://github.com/")
        elif remote.startswith("git@") and ":" in remote:
            parts = remote.split(":")
            remote = f"https://{parts[0].replace('git@', '')}/{parts[1]}"
        remote = remote.replace(".git", "")
        return f"{remote}/commit/{hash}"
    except Exception:
        return f"#{hash[:7]}"


def group_by_version(commits: list[dict], cwd: str | None = None) -> list[dict]:
    """Group commits by version (tag boundaries).

    Returns list of dicts with 'version', 'date', and 'commits' keys.
    If no tags, returns a single "Unreleased" group.
    """
    tags = get_tags(cwd=cwd)
    if not tags:
        return [{"version": "Unreleased", "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "commits": commits}]

    # Get commit hash for each tag
    tag_commits = {}
    for tag in tags:
        try:
            tag_commits[tag] = run_git(["rev-list", "-n", "1", tag], cwd=cwd)
        except SystemExit:
            continue

    # Map each commit to its version
    versions = []
    remaining = list(commits)

    for i, tag in enumerate(tags):
        tag_hash = tag_commits.get(tag)
        if not tag_hash:
            continue

        # Get tag date
        try:
            tag_date = run_git(["log", "-1", "--format=%aI", tag_hash], cwd=cwd)
            tag_date_short = tag_date[:10] if tag_date else "unknown"
        except SystemExit:
            tag_date_short = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Commits between this tag and the next newer tag (or HEAD)
        group_commits = []
        new_remaining = []
        for c in remaining:
            if c["hash"] == tag_hash:
                # The tag commit itself — include it then stop
                group_commits.append(c)
                break
            group_commits.append(c)
        else:
            # If we never hit the tag, all remaining are before this tag
            versions.append({"version": tag, "date": tag_date_short, "commits": group_commits})
            remaining = new_remaining
            continue

        # Remove grouped commits from remaining
        remaining = remaining[len(group_commits):]
        versions.append({"version": tag, "date": tag_date_short, "commits": group_commits})

    # Any remaining commits go under "Unreleased"
    if remaining:
        versions.append({
            "version": "Unreleased",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "commits": remaining,
        })

    return versions


def generate_changelog(
    since: str | None = None,
    full: bool = False,
    repo_path: str | None = None,
) -> str:
    """Generate a complete CHANGELOG.md string."""
    cwd = repo_path or os.getcwd()

    # Determine the since point
    resolved_since = since
    if not resolved_since and not full:
        tags = get_tags(cwd=cwd)
        if tags:
            resolved_since = tags[0]
        # If no tags, fall back to full history

    # Get repo name
    repo_name = ""
    try:
        remote = run_git(["config", "--get", "remote.origin.url"], cwd=cwd)
        if remote:
            match = re.search(r"[/:]([^/]+/[^/.]+?)(?:\.git)?$", remote)
            if match:
                repo_name = match.group(1)
    except SystemExit:
        pass

    if not repo_name:
        repo_name = os.path.basename(os.path.abspath(cwd or "."))

    # Fetch commits
    commits = get_commits(since=resolved_since, cwd=cwd)
    if not commits:
        return f"# Changelog\n\n*No commits found.*\n"

    # Group by version
    version_groups = group_by_version(commits, cwd=cwd)

    # Build the changelog
    lines = ["# Changelog", f"", f"> Generated for **{repo_name}**"]

    if resolved_since and not full:
        lines.append(f"> Commits since `{resolved_since}`")
    elif full:
        lines.append("> Full project history")

    lines.append("")

    for vg in version_groups:
        # Version header
        if vg["version"] == "Unreleased":
            lines.append(f"## [Unreleased]")
        else:
            lines.append(f"## [{vg['version']}] — {vg['date']}")
        lines.append("")

        # Categorize
        categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}
        for c in vg["commits"]:
            cat = categorize_commit(c["subject"], c["body"])
            c["cwd"] = cwd
            categories[cat].append(c)

        # Write categories (skip empty ones)
        has_content = False
        emoji_map = {"Added": "✨", "Fixed": "🐛", "Changed": "🔄", "Removed": "🗑️", "Other": "🔧"}
        for cat_name in ["Added", "Fixed", "Changed", "Removed", "Other"]:
            cat_commits = categories[cat_name]
            if not cat_commits:
                continue
            has_content = True
            lines.append(f"### {emoji_map.get(cat_name, '')} {cat_name}")
            lines.append("")
            for c in cat_commits:
                lines.append(format_commit_line(c))
            lines.append("")

        if not has_content:
            lines.append("_No significant changes._")
            lines.append("")

    # Add a stats footer
    total = sum(len(vg["commits"]) for vg in version_groups)
    lines.append("---")
    lines.append(f"_{total} commits processed._")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history",
    )
    parser.add_argument("--since", help="Start point (tag or commit). Default: latest tag.")
    parser.add_argument("--full", action="store_true", help="Include full history (ignore tags)")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("--repo", help="Path to git repository (default: current directory)")
    args = parser.parse_args()

    changelog = generate_changelog(since=args.since, full=args.full, repo_path=args.repo)

    with open(args.output, "w") as f:
        f.write(changelog)

    commit_count = len(get_commits(since=args.since, cwd=args.repo))
    print(f"✓ CHANGELOG.md generated ({commit_count} commits, {len(get_tags(cwd=args.repo))} tags)")
    print(f"  Output: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
