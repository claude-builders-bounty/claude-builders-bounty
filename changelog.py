#!/usr/bin/env python3
"""
changelog.py — Generate a structured CHANGELOG.md from git history

Usage:
  python changelog.py                  # output to CHANGELOG.md
  python changelog.py --preview        # print to stdout
  python changelog.py --since v1.0.0   # specify a starting tag
  python changelog.py --repo user/repo # repo URL for commit links
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from collections import defaultdict


def run_git(*args: str) -> str:
    """Run a git command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""
    except FileNotFoundError:
        print("❌ Git not found. Are you in a git repository?")
        sys.exit(1)


def get_last_tag() -> str | None:
    """Find the most recent git tag, or None."""
    tag = run_git("describe", "--tags", "--abbrev=0")
    return tag or None


def get_initial_commit() -> str | None:
    """Get the initial (root) commit hash."""
    return run_git("rev-list", "--max-parents=0", "HEAD") or None


def get_commits_since(ref: str) -> list[dict]:
    """
    Get commits since `ref`.
    Returns list of dicts with keys: message, hash, author, date
    """
    raw = run_git("log", f"{ref}..HEAD", "--format=%s|||%h|||%an|||%ai")
    if not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|||")
        if len(parts) >= 4:
            commits.append({
                "message": parts[0].strip(),
                "hash": parts[1].strip(),
                "author": parts[2].strip(),
                "date": parts[3].strip(),
            })
    return commits


def categorize(message: str) -> str:
    """Categorize a commit message into: Added, Fixed, Changed, Removed, or Other."""
    lower = message.lower()
    # Conventional commits: feat:, fix:, chore:, refactor:, etc.
    if re.match(r"^(feat|feature)(\(.*\))?[!:]\s", lower):
        return "Added"
    if re.match(r"^(fix|bug|hotfix)(\(.*\))?[!:]\s", lower):
        return "Fixed"
    if re.match(r"^(chore|refactor|update|perf|style|ci|build|test|docs)(\(.*\))?[!:]\s", lower):
        return "Changed"
    if re.match(r"^(remove|delete|deprecat)(\(.*\))?[!:]\s", lower):
        return "Removed"

    # Fallback keyword matching
    if any(lower.startswith(w) for w in ["add", "feat", "feature", "new", "implement", "introduce", "create", "support"]):
        return "Added"
    if any(lower.startswith(w) for w in ["fix", "bug", "hotfix", "patch", "correct", "resolve"]):
        return "Fixed"
    if any(lower.startswith(w) for w in ["chore", "refactor", "update", "perf", "improve", "bump", "upgrade", "migrate"]):
        return "Changed"
    if any(lower.startswith(w) for w in ["remove", "delete", "deprecat", "drop", "revert"]):
        return "Removed"

    return "Other"


def format_entry(commit: dict, repo_url: str | None) -> str:
    """Format a single commit entry as a markdown list item."""
    msg = commit["message"]
    hash_short = commit["hash"]
    author = commit["author"]

    if repo_url:
        commit_link = f"[{hash_short}]({repo_url}/commit/{hash_short})"
    else:
        # Try to detect remote origin
        origin = run_git("remote", "get-url", "origin")
        if origin:
            # Convert git@github.com:user/repo.git → https://github.com/user/repo
            origin = origin.strip()
            if origin.startswith("git@"):
                origin = origin.replace(":", "/").replace("git@", "https://").replace(".git", "")
            elif origin.endswith(".git"):
                origin = origin[:-4]
            if "github.com" in origin or "gitlab" in origin:
                commit_link = f"[{hash_short}]({origin}/commit/{hash_short})"
            else:
                commit_link = f"`{hash_short}`"
        else:
            commit_link = f"`{hash_short}`"

    return f"- {msg} ({commit_link})"


HEADERS = {
    "Added": "✨ Added",
    "Fixed": "🐛 Fixed",
    "Changed": "🔄 Changed",
    "Removed": "🗑️ Removed",
    "Other": "📦 Other",
}

EMOJIS = {
    "Added": "✨",
    "Fixed": "🐛",
    "Changed": "🔄",
    "Removed": "🗑️",
    "Other": "📦",
}


def generate_changelog(
    commits: list[dict],
    since_ref: str,
    repo_url: str | None = None,
    version: str | None = None,
) -> str:
    """Generate the full CHANGELOG.md content."""

    if version is None:
        version = datetime.date.today().strftime("%Y.%m.%d")

    date_str = datetime.date.today().isoformat()

    # Categorize
    categorized: dict[str, list[str]] = defaultdict(list)
    for c in commits:
        cat = categorize(c["message"])
        categorized[cat].append(format_entry(c, repo_url))

    # Build markdown
    lines = ["# Changelog\n", f"## [{version}] - {date_str}\n"]

    # Stats
    total = len(commits)
    lines.append(f"_Generated from {total} commit{'s' if total != 1 else ''} since `{since_ref}`._\n")

    # Category order
    for cat in ["Added", "Fixed", "Changed", "Removed", "Other"]:
        items = categorized.get(cat, [])
        if items:
            lines.append(f"### {HEADERS[cat]}\n")
            lines.extend(items)
            lines.append("")

    return "\n".join(lines)


def detect_repo_url() -> str | None:
    """Try to detect the GitHub/GitLab repo URL from git remote."""
    origin = run_git("remote", "get-url", "origin")
    if not origin:
        return None
    origin = origin.strip()
    # git@github.com:user/repo.git → https://github.com/user/repo
    m = re.match(r"git@([^:]+):(.+)\.git$", origin)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    # https://github.com/user/repo.git → https://github.com/user/repo
    m = re.match(r"(https?://[^/]+/[^/]+/[^/]+?)\.git$", origin)
    if m:
        return m.group(1)
    # Already a URL
    if origin.startswith("http"):
        return origin.rstrip("/")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history"
    )
    parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="Print to stdout instead of writing to CHANGELOG.md",
    )
    parser.add_argument(
        "--since", "-s",
        type=str,
        default=None,
        help="Starting ref (tag, commit hash, or branch). Defaults to last tag.",
    )
    parser.add_argument(
        "--repo", "-r",
        type=str,
        default=None,
        help="Repo URL for commit links (e.g., user/repo or full URL)",
    )
    parser.add_argument(
        "--version", "-v",
        type=str,
        default=None,
        help="Version string for the new release. Defaults to today's date.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    args = parser.parse_args()

    # Determine since_ref
    since_ref = args.since
    if since_ref is None:
        since_ref = get_last_tag()
        if since_ref is None:
            since_ref = get_initial_commit()
    if since_ref is None:
        print("❌ No commits found in this repository.")
        sys.exit(1)

    # Get commits
    commits = get_commits_since(since_ref)
    if not commits:
        print(f"ℹ️  No new commits since {since_ref}. Nothing to generate.")
        sys.exit(0)

    # Determine repo URL
    repo_url = args.repo
    if repo_url is None:
        repo_url = detect_repo_url()
    if repo_url and "/" in repo_url and not repo_url.startswith("http"):
        repo_url = f"https://github.com/{repo_url}"

    # Generate
    changelog = generate_changelog(commits, since_ref, repo_url, args.version)

    # Output
    if args.preview:
        print(changelog)
    else:
        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(changelog)
            f.write("\n")
        print(f"✅ Generated {os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
