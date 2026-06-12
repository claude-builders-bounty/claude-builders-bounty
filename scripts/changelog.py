#!/usr/bin/env python3
"""
changelog.py — Generate a structured CHANGELOG.md from git history.

Categorizes commits into Added / Fixed / Changed / Removed based on
conventional commit prefixes (feat:, fix:, refactor:, chore:, BREAKING CHANGE, etc.)

Works on any git repo. Fetches commits since the last tag (or all commits
if no tag exists).

Usage:
  ./scripts/changelog.py                  # generate CHANGELOG.md in repo root
  ./scripts/changelog.py --since=v1.0.0   # generate since a specific tag
  ./scripts/changelog.py --output=NEWS.md # custom output file
  ./scripts/changelog.py --help

Exit codes:
  0 success
  1 not in a git repo
  2 invalid arguments
"""
from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BREAKING_RE = re.compile(r"BREAKING CHANGE|breaking-change", re.IGNORECASE)
PREFIXES = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "chore": "Changed",
    "docs": "Changed",
    "style": "Changed",
    "test": "Changed",
    "build": "Changed",
    "ci": "Changed",
}


def run(cmd: list[str], cwd: str) -> str:
    """Run a command, return stdout, raise on non-zero exit."""
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{r.stderr}")
    return r.stdout


def get_last_tag(repo: str) -> str:
    """Return last tag name, or '' if no tags exist."""
    try:
        out = run(["git", "-C", repo, "describe", "--tags", "--abbrev=0"], repo)
        return out.strip()
    except RuntimeError:
        return ""


def get_commits(repo: str, since: str) -> list[tuple[str, str, str]]:
    """Return list of (hash, subject, body) commits since <since> (or all if empty)."""
    rng = f"{since}..HEAD" if since else "HEAD"
    sep = "<<<SEP>>>"
    fmt = f"%H{sep}%s{sep}%b"
    out = run(["git", "-C", repo, "log", rng, f"--pretty=format:{fmt}"], repo)
    commits = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        parts = line.split(sep, 2)
        if len(parts) < 2:
            continue
        h = parts[0].strip()
        subject = parts[1].strip() if len(parts) > 1 else ""
        body = parts[2].strip() if len(parts) > 2 else ""
        if h:
            commits.append((h, subject, body))
    return commits


def categorize(commits: list[tuple[str, str, str]]) -> dict[str, list[str]]:
    """Return {'Added': [...], 'Fixed': [...], 'Changed': [...], 'Removed': [...]}."""
    buckets: dict[str, list[str]] = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for h, subject, body in commits:
        short = h[:7]
        line = f"- {subject} ({short})"
        if BREAKING_RE.search(subject + " " + body):
            buckets["Removed"].append(line)
            continue
        prefix = subject.split(":", 1)[0].split("(", 1)[0].strip().lower()
        cat = PREFIXES.get(prefix, "Changed")  # uncategorized → Changed
        buckets[cat].append(line)
    return buckets


def render(version: str, since: str, buckets: dict[str, list[str]]) -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sections = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        f"## [{version}] — {date}",
        "",
    ]
    for cat, label in [("Added", "Added"), ("Fixed", "Fixed"),
                       ("Changed", "Changed"),
                       ("Removed", "Removed (BREAKING CHANGES)")]:
        items = buckets[cat]
        if items:
            sections.append(f"### {label}")
            sections.extend(items)
            sections.append("")
    total = sum(len(v) for v in buckets.values())
    sections.append("---")
    sections.append(f"*{total} commits since {since or '<beginning>'}*")
    sections.append("")
    return "\n".join(sections)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    ap.add_argument("--since", help="Generate from <ref> (default: last tag, or all)")
    ap.add_argument("--output", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    ap.add_argument("--repo", default=".", help="Repo path (default: current dir)")
    ap.add_argument("--version", help="Override version label")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if not subprocess.run(["git", "-C", repo, "rev-parse", "--is-inside-work-tree"],
                          capture_output=True).returncode == 0:
        print(f"Error: {repo} is not a git repository", file=sys.stderr)
        return 1

    since = args.since or get_last_tag(repo)
    version = args.version or since or "Unreleased"

    commits = get_commits(repo, since)
    if not commits:
        print(f"No commits found in range: {since or 'HEAD'}", file=sys.stderr)
        return 0

    buckets = categorize(commits)
    md = render(version, since, buckets)

    Path(args.output).write_text(md)
    total = sum(len(v) for v in buckets.values())
    print(f"✅ Wrote {args.output}")
    print(f"   Added: {len(buckets['Added'])} | Fixed: {len(buckets['Fixed'])} | "
          f"Changed: {len(buckets['Changed'])} | Removed: {len(buckets['Removed'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
