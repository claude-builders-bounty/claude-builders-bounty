#!/usr/bin/env python3
"""
changelog.py — Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py [--repo PATH] [--output FILE] [--from-tag TAG] [--to-ref REF]

Dependencies: git (must be installed and available in PATH)
"""

import argparse
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime


CATEGORIES = OrderedDict([
    ("Added", ["add", "feat", "feature", "implement", "create", "new", "+"]),
    ("Changed", ["change", "update", "refactor", "improve", "migrate", "bump", "upgrade", "deprecate"]),
    ("Fixed", ["fix", "bug", "hotfix", "patch", "correct", "resolve", "~"]),
    ("Removed", ["remove", "delete", "drop", "deprecate", "cleanup", "strip", "-"]),
])

CONVENTIONAL_PREFIX = re.compile(
    r'^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?\s*:\s*(?P<subject>.+)',
    re.IGNORECASE
)


def run_git(cmd, cwd=None):
    """Run a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, cwd=cwd, timeout=30
        )
        if result.returncode != 0:
            return None
        return result.stdout.rstrip("\n")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def get_last_tag(repo_path):
    """Get the most recent git tag, sorted by version. Returns None if no tags."""
    # Try semantic version sort first
    tag = run_git(
        ["git", "describe", "--tags", "--abbrev=0", "--match", "v*"], cwd=repo_path
    )
    if not tag:
        tag = run_git(
            ["git", "describe", "--tags", "--abbrev=0"], cwd=repo_path
        )
    if not tag:
        # Fall back to first commit if no tags
        tag = run_git(
            ["git", "rev-list", "--max-parents=0", "HEAD"], cwd=repo_path
        )
        if tag:
            tag = "initial-commit"
    return tag


def get_commits_since(repo_path, since_ref=None, to_ref="HEAD"):
    """Get git log entries since a given ref."""
    if since_ref and since_ref != "initial-commit":
        log_range = f"{since_ref}..{to_ref}"
    else:
        # No tag or first commit - include all commits
        log_range = to_ref

    raw = run_git(
        ["git", "log", log_range, "--format=%H||%ai||%an||%s", "--no-merges"],
        cwd=repo_path,
    )
    if not raw:
        # If log_range fails (e.g., tag not ancestor of HEAD), try full log
        raw = run_git(
            ["git", "log", to_ref, "--format=%H||%ai||%an||%s", "--no-merges"],
            cwd=repo_path,
        )
    if not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        parts = line.split("||", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0][:7],
                "date": parts[1],
                "author": parts[2],
                "message": parts[3],
            })
    return commits


def categorize_commit(message):
    """Categorize a commit message into Added/Fixed/Changed/Removed."""
    # Check for breaking changes
    is_breaking = False

    m = CONVENTIONAL_PREFIX.match(message)
    if m:
        commit_type = m.group("type").lower()
        scope = m.group("scope") or ""
        subject = m.group("subject")
        is_breaking = bool(m.group("breaking"))

        # Map conventional commit types to our categories
        if commit_type in ("feat", "feature"):
            return "Added", subject, scope
        elif commit_type in ("fix", "bugfix", "hotfix"):
            return "Fixed", subject, scope
        elif commit_type in ("refactor", "perf", "improve"):
            return "Changed", subject, scope
        elif commit_type in ("remove", "delete", "deprecate"):
            return "Removed", subject, scope
        elif commit_type in ("chore", "ci", "build", "style"):
            return "Changed", f"({scope}) {subject}" if scope else subject, scope
        elif commit_type in ("docs", "doc"):
            return "Changed", f"docs: {subject}", scope
        elif commit_type in ("test", "tests"):
            return "Changed", f"test: {subject}", scope
        else:
            return "Changed", subject, scope

    # Fallback: keyword matching for non-conventional commits
    msg_lower = message.lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if msg_lower.startswith(kw):
                # Strip the keyword prefix
                rest = message[len(kw):].lstrip(":/() ")
                return category, rest, ""

    # Default
    return "Changed", message, ""


def format_changelog(commits, last_tag, repo_name="", repo_url=""):
    """Generate CHANGELOG.md content."""
    categorized = OrderedDict()
    for cat in CATEGORIES:
        categorized[cat] = []

    for commit in commits:
        category, subject, scope = categorize_commit(commit["message"])
        if category not in categorized:
            category = "Changed"
        date = commit["date"][:10] if commit["date"] else "unknown"
        categorized[category].append((subject, commit["hash"], date, scope))

    lines = []
    lines.append("# Changelog")
    lines.append("")
    if repo_name:
        lines.append(f"> {repo_name}")
        lines.append("")
    lines.append(f"## [{last_tag or 'initial'}] — {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")

    has_entries = any(items for items in categorized.values())
    if not has_entries:
        lines.append("*No changes recorded.*")
        lines.append("")
        return "\n".join(lines)

    for category, items in categorized.items():
        if not items:
            continue
        # Emoji prefix
        emoji_map = {"Added": "✨", "Changed": "🔄", "Fixed": "🐛", "Removed": "🗑️"}
        emoji = emoji_map.get(category, "•")
        lines.append(f"### {emoji} {category}")
        lines.append("")
        for subject, hash_val, date, scope in items:
            scope_str = f"**{scope}:** " if scope else ""
            line = f"- {scope_str}{subject}"
            if hash_val:
                line += f" ([`{hash_val}`]"
                if repo_url:
                    line += f"({repo_url}/commit/{hash_val})"
                line += ")"
            lines.append(line)
        lines.append("")

    lines.append("---")
    lines.append(f"*Auto-generated by changelog.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    return "\n".join(lines)


def get_repo_info(repo_path):
    """Get repo name and URL."""
    origin = run_git(["git", "remote", "get-url", "origin"], cwd=repo_path)
    name = ""
    url = ""
    if origin:
        # Handle both HTTPS and SSH URLs
        m = re.search(r'(?:github\.com[:/])([^/]+/[^/.]+?)(?:\.git)?$', origin)
        if m:
            name = m.group(1)
            url = f"https://github.com/{name}"
    else:
        name = os.path.basename(os.path.abspath(repo_path))
    return name, url


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--repo", default=".", help="Path to git repository (default: current dir)")
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    parser.add_argument("--from-tag", help="Start tag (default: auto-detect last tag)")
    parser.add_argument("--to-ref", default="HEAD", help="End ref (default: HEAD)")
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo)

    # Verify it's a git repo
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"Error: {repo_path} is not a git repository", file=sys.stderr)
        sys.exit(1)

    # Get repo info
    repo_name, repo_url = get_repo_info(repo_path)

    # Get the tag range
    last_tag = args.from_tag or get_last_tag(repo_path)
    print(f"📦 Last tag: {last_tag}", file=sys.stderr)

    # Get commits
    commits = get_commits_since(repo_path, last_tag, args.to_ref)
    print(f"📝 Commits found: {len(commits)}", file=sys.stderr)

    if not commits:
        print("⚠️  No new commits found since last tag.", file=sys.stderr)
        # Still write a minimal changelog
        changelog = f"# Changelog\n\n*No new commits since {last_tag}.*\n"
    else:
        # Generate changelog
        changelog = format_changelog(commits, last_tag, repo_name, repo_url)

    # Write output
    output_path = os.path.abspath(args.output)
    with open(output_path, "w") as f:
        f.write(changelog)
    print(f"✅ CHANGELOG written to: {output_path}", file=sys.stderr)

    # Print a preview
    preview_lines = changelog.strip().split("\n")[:10]
    print("\n📋 Preview:", file=sys.stderr)
    for line in preview_lines:
        print(f"  {line}", file=sys.stderr)


if __name__ == "__main__":
    main()
