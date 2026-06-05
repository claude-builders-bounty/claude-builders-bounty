#!/usr/bin/env python3
"""
generate_changelog.py — Generate a structured CHANGELOG.md from git history.

Categorizes commits into Added / Fixed / Changed / Removed / Deprecated / Security
by parsing Conventional Commits (feat:, fix:, etc.) and fallback keyword detection.

Usage:
    python generate_changelog.py                   # prints to stdout
    python generate_changelog.py --output CHANGELOG.md
    python generate_changelog.py --tag v1.0.0      # start from a specific tag
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# ── Conventional Commit type → category mapping ──────────────────────────

CATEGORY_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "bug": "Fixed",
    "hotfix": "Fixed",
    "change": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "performance": "Changed",
    "optimize": "Changed",
    "optimization": "Changed",
    "style": "Changed",
    "chore": "Changed",
    "remove": "Removed",
    "delete": "Removed",
    "deprecate": "Deprecated",
    "deprecated": "Deprecated",
    "security": "Security",
    "docs": "Documentation",
    "doc": "Documentation",
    "test": "Testing",
    "tests": "Testing",
    "ci": "Changed",
    "build": "Changed",
    "revert": "Fixed",
}

FALLBACK_KEYWORDS = {
    "Added": ["add", "new", "create", "implement", "introduce", "support", "init"],
    "Fixed": ["fix", "bug", "patch", "correct", "resolve", "repair", "hotfix"],
    "Changed": ["update", "change", "refactor", "improve", "migrate", "upgrade", "bump", "optimize"],
    "Removed": ["remove", "delete", "drop", "deprecat", "cleanup", "strip"],
    "Security": ["security", "vulnerability", "cve", "xss", "csrf", "inject"],
    "Documentation": ["docs", "readme", "documentation", "comment"],
}


def run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd or os.getcwd(),
        )
        return result.stdout.strip()
    except FileNotFoundError:
        print("Error: git is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)


def get_tags(cwd: str | None = None) -> list[str]:
    """Return sorted list of git tags (most recent first)."""
    tags = run_git(["tag", "--sort=-v:refname"], cwd=cwd)
    return [t for t in tags.split("\n") if t.strip()]


def get_log(start: str | None, end: str = "HEAD", cwd: str | None = None) -> list[dict]:
    """
    Return parsed commit log between start and end (exclusive of start).
    
    Each commit dict: {sha, date, author, subject, body, raw_type, category}
    """
    if start:
        range_spec = f"{start}..{end}"
    else:
        # No start tag: use the first commit
        first = run_git(["rev-list", "--max-parents=0", "HEAD"], cwd=cwd)
        if not first:
            return []
        range_spec = f"{first.split(chr(10))[0]}..{end}"

    # Format: SHA||date||author||subject||body_separator||body
    fmt = "%H||%ci||%an||%s||%b"
    raw = run_git(["log", range_spec, f"--format={fmt}", "--no-merges"], cwd=cwd)
    if not raw:
        return []

    commits = []
    for entry in raw.split("\n"):
        if not entry.strip():
            continue
        parts = entry.split("||", 4)
        if len(parts) < 4:
            continue
        sha, date, author, subject = parts[0], parts[1], parts[2], parts[3]
        body = parts[4] if len(parts) > 4 else ""

        raw_type, category = classify_commit(subject, body)
        commits.append({
            "sha": sha[:7],
            "date": date,
            "author": author,
            "subject": subject,
            "body": body,
            "raw_type": raw_type,
            "category": category,
        })
    return commits


def classify_commit(subject: str, body: str) -> tuple[str, str]:
    """
    Classify a commit into a category using Conventional Commits parsing
    and keyword fallback.
    """
    full_text = f"{subject}\n{body}".lower()

    # Try Conventional Commit pattern: type(scope)!: description
    # Also: type: description, type!: description
    cc_match = re.match(
        r"^\s*(\w+)"           # type
        r"(?:\([^)]*\))?"       # optional (scope)
        r"(!)?\s*:\s*",         # optional !, then colon
        subject,
    )
    if cc_match:
        raw_type = cc_match.group(1).lower()
        category = CATEGORY_MAP.get(raw_type, "Changed")
        return raw_type, category

    # Keyword fallback: check each category's keywords
    scores = defaultdict(int)
    for cat, keywords in FALLBACK_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", full_text):
                scores[cat] += 1

    if scores:
        best = max(scores, key=scores.get)
        return "unknown", best

    return "unknown", "Changed"


def group_commits(commits: list[dict]) -> dict[str, list[dict]]:
    """Group commits by category, preserving order within each group."""
    order = ["Added", "Fixed", "Changed", "Deprecated", "Removed", "Security", "Documentation", "Testing", "Other"]
    groups = defaultdict(list)
    has_other = False

    for c in commits:
        cat = c["category"]
        if cat in order:
            groups[cat].append(c)
        else:
            groups["Other"].append(c)
            has_other = True

    # Return in canonical order, skipping empty categories
    result = {}
    for cat in order:
        if cat in groups:
            result[cat] = groups[cat]
    if has_other:
        result["Other"] = groups["Other"]
    return result


def format_changelog(
    commits: list[dict],
    repo_url: str | None = None,
    version: str | None = None,
) -> str:
    """Generate the full CHANGELOG.md content."""
    groups = group_commits(commits)

    # Determine version and date
    ver = version or "Unreleased"
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Changelog\n"]
    lines.append(f"## [{ver}] — {today}\n")

    if repo_url:
        lines.append(f"> Repository: [{repo_url}]({repo_url})\n")

    if not commits:
        lines.append("_No significant changes._\n")
        return "\n".join(lines)

    for category, cat_commits in groups.items():
        emoji_map = {
            "Added": "✨",
            "Fixed": "🐛",
            "Changed": "🔧",
            "Deprecated": "⚠️",
            "Removed": "🗑️",
            "Security": "🔒",
            "Documentation": "📝",
            "Testing": "🧪",
            "Other": "📦",
        }
        emoji = emoji_map.get(category, "📦")
        lines.append(f"### {emoji} {category}\n")

        for c in cat_commits:
            sha_link = f"[`{c['sha']}`]({repo_url}/commit/{c['sha']})" if repo_url else f"`{c['sha']}`"
            lines.append(f"- {sha_link} {c['subject']}")

        lines.append("")  # blank line after section

    # Stats footer
    total = len(commits)
    contributors = len(set(c["author"] for c in commits))
    lines.append(f"---\n")
    lines.append(f"> {total} commits · {contributors} contributors\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history",
    )
    parser.add_argument("-o", "--output", type=str, help="Output file (default: stdout)")
    parser.add_argument("-t", "--tag", type=str, help="Starting tag (default: latest tag)")
    parser.add_argument("-r", "--repo-url", type=str, help="Repository URL for commit links")
    parser.add_argument("-v", "--version", type=str, help="Version string (default: from tag or 'Unreleased')")
    parser.add_argument("-c", "--cwd", type=str, default=None, help="Git repository path (default: current dir)")

    args = parser.parse_args()

    cwd = args.cwd
    if not os.path.isdir(os.path.join(cwd or ".", ".git")):
        print("Error: not a git repository. Run from a git repo or use --cwd.", file=sys.stderr)
        sys.exit(1)

    # Determine starting point
    tags = get_tags(cwd=cwd)
    start_tag = args.tag or (tags[0] if tags else None)

    version = args.version or start_tag or "Unreleased"

    if start_tag:
        print(f"Scanning commits since {start_tag}...", file=sys.stderr)
    else:
        print("Scanning all commits (no tags found)...", file=sys.stderr)

    repo_url = args.repo_url or run_git(["remote", "get-url", "origin"], cwd=cwd) or ""
    # Clean up repo URL for display
    if repo_url:
        repo_url = repo_url.replace("git@github.com:", "https://github.com/").replace(".git", "")
    else:
        repo_url = None

    commits = get_log(start_tag, cwd=cwd)

    if not commits:
        print("No commits found in range.", file=sys.stderr)
        changelog = format_changelog([], repo_url, version)
    else:
        print(f"Found {len(commits)} commits.", file=sys.stderr)
        changelog = format_changelog(commits, repo_url, version)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(changelog)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(changelog)


if __name__ == "__main__":
    main()
