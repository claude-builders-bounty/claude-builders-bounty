#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.

Part of the $50 bounty for claude-builders-bounty.
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def run_git(cmd: List[str], cwd: Optional[Path] = None) -> str:
    """Run a git command and return stripped stdout."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e.stderr.strip()}", file=sys.stderr)
        return ""


def get_last_tag(repo_path: Path) -> Optional[str]:
    """Get the most recent tag."""
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=repo_path)
    return tag if tag else None


def get_commits(repo_path: Path, since: Optional[str]) -> List[Dict]:
    """Get commits since a tag (or all if no tag). Robust parsing."""
    cmd = [
        "log",
        "--pretty=format:%H%n%s%n%an%n%ad%n%b%n---COMMIT---",
        "--date=short",
        "--no-merges"
    ]
    if since:
        cmd.append(f"{since}..HEAD")
    else:
        cmd.extend(["-n", "80"])

    output = run_git(cmd, cwd=repo_path)
    if not output:
        return []

    commits = []
    blocks = output.split("---COMMIT---")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [l for l in block.split("
") if l.strip()]
        if len(lines) < 2:
            continue
        subject = lines[1].strip()
        author = lines[2].strip() if len(lines) > 2 else ""
        date = lines[3].strip() if len(lines) > 3 else ""
        body = "
".join(lines[4:]).strip() if len(lines) > 4 else ""
        commits.append({
            "hash": lines[0][:8],
            "subject": subject,
            "body": body,
            "author": author,
            "date": date,
        })
    return commits


def categorize_commits(commits: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize commits into Added / Fixed / Changed / Removed / Other.
    Strips conventional commit prefixes for cleaner output.
    """
    categories: Dict[str, List[Dict]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Other": [],
    }

    added_patterns = re.compile(r"^(feat|add|new|implement)|^w+(w+)?:s*(feat|add)", re.I)
    fixed_patterns = re.compile(r"^(fix|bug|patch)|^w+(w+)?:s*(fix|bug)", re.I)
    changed_patterns = re.compile(r"^(refactor|update|change|improve|deps?|perf)", re.I)
    removed_patterns = re.compile(r"^(remove|delete|drop|deprecate)", re.I)
    ignore_in_other = re.compile(r"^(chore|docs|test|style|ci|build)", re.I)

    def clean_subject(s: str) -> str:
        # Remove common prefixes like "feat: ", "fix(scope): "
        return re.sub(r'^[a-z]+(([^)]+))?:s*', '', s, flags=re.I).strip()

    for commit in commits:
        raw_subject = commit["subject"]
        subject_lower = raw_subject.lower()
        cleaned = clean_subject(raw_subject)

        if added_patterns.search(subject_lower):
            commit["display"] = cleaned
            categories["Added"].append(commit)
        elif fixed_patterns.search(subject_lower):
            commit["display"] = cleaned
            categories["Fixed"].append(commit)
        elif removed_patterns.search(subject_lower):
            commit["display"] = cleaned
            categories["Removed"].append(commit)
        elif changed_patterns.search(subject_lower):
            commit["display"] = cleaned
            categories["Changed"].append(commit)
        elif not ignore_in_other.search(subject_lower):
            commit["display"] = cleaned
            categories["Other"].append(commit)
        # else: ignore chore/docs etc.

    return categories


def format_changelog(categories: Dict[str, List[Dict]], version: str = "Unreleased", date: Optional[str] = None) -> str:
    """Format categories into nice Markdown CHANGELOG."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# Changelog",
        "",
        f"## [{version}] - {date}",
        "",
    ]

    order = ["Added", "Fixed", "Changed", "Removed", "Other"]
    emoji = {
        "Added": "✨",
        "Fixed": "🐛",
        "Changed": "🔄",
        "Removed": "🗑️",
        "Other": "📝",
    }

    has_content = False
    for cat in order:
        items = categories.get(cat, [])
        if not items:
            continue
        has_content = True
        lines.append(f"### {emoji[cat]} {cat}")
        lines.append("")
        for c in items:
            subj = c.get("display", c["subject"]).strip()
            lines.append(f"- {subj} ({c['hash']})")
        lines.append("")

    if not has_content:
        lines.append("_No commits since last tag._")
        lines.append("")

    return "
".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured CHANGELOG.md from git history (for the claude-builders-bounty $50 task)"
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("."),
        help="Path to the git repository (default: current dir)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Output file path",
    )
    parser.add_argument(
        "--since",
        help="Override the 'since' tag (instead of auto-detecting latest tag)",
    )
    parser.add_argument(
        "--version",
        default="Unreleased",
        help="Version header to use (default: Unreleased)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print to stdout instead of writing file",
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(f"Error: {repo} is not a git repository", file=sys.stderr)
        sys.exit(1)

    since = args.since or get_last_tag(repo)
    print(f"Generating changelog since: {since or 'beginning of history'}", file=sys.stderr)

    commits = get_commits(repo, since)
    print(f"Found {len(commits)} commits", file=sys.stderr)

    categories = categorize_commits(commits)
    changelog = format_changelog(categories, version=args.version)

    if args.dry_run:
        print(changelog)
    else:
        args.output.write_text(changelog, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)

    # Also show a quick summary
    for cat, items in categories.items():
        if items:
            print(f"  {cat}: {len(items)}", file=sys.stderr)


if __name__ == "__main__":
    main()
