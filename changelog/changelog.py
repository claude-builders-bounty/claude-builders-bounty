#!/usr/bin/env python3
"""changelog.py — Generate a structured CHANGELOG.md from git history

Bounty: claude-builders-bounty issue #1 ($50)
Usage: python changelog.py [--output CHANGELOG.md] [--project-dir .]
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import List, Tuple


GIT_CMD = os.environ.get("GIT_CMD", None) or "git"


def _find_git() -> str:
    """Try to locate git executable on common paths."""
    candidates = [
        "git",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files\Git\cmd\git.exe",
        "/usr/bin/git",
        "/usr/local/bin/git",
    ]
    for c in candidates:
        try:
            r = subprocess.run([c, "--version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return c
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return "git"  # fallback, will fail gracefully later


def run_git(cmd: List[str], cwd: str) -> str:
    """Run a git command and return stdout."""
    global GIT_CMD
    if GIT_CMD == "git" and not os.path.exists(GIT_CMD):
        found = _find_git()
        if found != GIT_CMD:
            GIT_CMD = found
    try:
        result = subprocess.run(
            [GIT_CMD] + cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_last_tag(cwd: str) -> str:
    """Get the most recent git tag, or first commit hash if no tags."""
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd)
    if tag:
        return tag
    # Fall back to first commit
    first = run_git(["rev-list", "--max-parents=0", "HEAD"], cwd)
    return first or ""


def get_commits_since(ref: str, cwd: str) -> List[Tuple[str, str, str, str]]:
    """Get commits since the given ref (tag or commit hash)."""
    if not ref:
        return []

    raw = run_git(
        ["log", f"{ref}..HEAD", "--no-merges",
         "--format=%H||%s||%an||%ai"],
        cwd,
    )
    if not raw:
        return []

    commits = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("||", 3)
        if len(parts) == 4:
            commits.append(tuple(parts))  # (hash, subject, author, date)
    return commits


def categorize(subject: str) -> str:
    """Categorize a commit by its subject prefix."""
    lower = subject.lower().strip()

    patterns = {
        "Added": r"^(feat|feature|add|new|implement|introduce|create)",
        "Fixed": r"^(fix|bugfix|bug|patch|hotfix|correct|resolve)",
        "Changed": r"^(change|update|refactor|perf|improve|modify|rewrite|bump|upgrade|migrate)",
        "Removed": r"^(remove|delete|drop|deprecate|cleanup|retire)",
    }

    for category, pattern in patterns.items():
        if re.match(pattern, lower):
            return category

    # Check for conventional commit scope prefix: feat(scope): message
    scope_match = re.match(r"^(\w+)\(.*\):", lower)
    if scope_match:
        scope_type = scope_match.group(1)
        if scope_type in ("feat", "feature"):
            return "Added"
        elif scope_type in ("fix", "bugfix"):
            return "Fixed"
        elif scope_type in ("refactor", "perf", "style", "chore"):
            return "Changed"

    return "Uncategorized"


def generate_changelog(
    commits: List[Tuple[str, str, str, str]],
    version: str,
    date_str: str,
) -> str:
    """Generate CHANGELOG.md content from commits."""
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Uncategorized": [],
    }

    for h, subject, author, date in commits:
        cat = categorize(subject)
        short_hash = h[:7]
        categories[cat].append((subject, short_hash, author, date))

    lines = ["# Changelog", "", f"## [{version}] - {date_str}", ""]

    for cat_name in ["Added", "Fixed", "Changed", "Removed", "Uncategorized"]:
        items = categories[cat_name]
        if items:
            lines.append(f"### {cat_name}")
            lines.append("")
            for subject, short_hash, author, date in items:
                lines.append(f"- {subject} ({short_hash})")
            lines.append("")

    if not any(categories.values()):
        lines.append("No changes since the last release.")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history"
    )
    parser.add_argument(
        "--output", "-o",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--project-dir", "-d",
        default=".",
        help="Project directory (default: current directory)",
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)

    # Verify git repo
    if not os.path.isdir(os.path.join(project_dir, ".git")):
        # Check parent directories
        top_level = run_git(["rev-parse", "--show-toplevel"], project_dir)
        if not top_level:
            print("Error: Not a git repository.", file=sys.stderr)
            sys.exit(1)
        project_dir = top_level

    last_tag = get_last_tag(project_dir)
    if not last_tag:
        print("Error: No commits found in repository.", file=sys.stderr)
        sys.exit(1)

    print(f"Generating CHANGELOG from {last_tag} → HEAD")
    print(f"Output: {args.output}")

    commits = get_commits_since(last_tag, project_dir)
    version = last_tag
    date_str = datetime.now().strftime("%Y-%m-%d")

    content = generate_changelog(commits, version, date_str)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)

    total = len(commits)
    print(f"Done! {total} commits → {args.output}")

    # Category breakdown
    cats = {}
    for h, s, a, d in commits:
        c = categorize(s)
        cats[c] = cats.get(c, 0) + 1
    for c, n in cats.items():
        print(f"  {c}: {n}")

    if total == 0:
        print("(No new commits found — empty changelog generated)")


if __name__ == "__main__":
    main()
