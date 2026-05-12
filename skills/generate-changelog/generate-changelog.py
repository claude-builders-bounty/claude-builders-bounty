#!/usr/bin/env python3
"""Auto-generate a structured CHANGELOG.md from git history.

Usage:
    python3 generate-changelog.py [--repo PATH] [--output FILE] [--since TAG] [--dry-run]
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CATEGORIES = {
    "Added":   [r"^feat\b", r"\badd\b", r"\bintroduce", r"\bnew\b", r"\bimplement", r"\bcreate"],
    "Fixed":   [r"^fix\b", r"\bbugfix", r"\bresolve", r"\bpatch\b", r"\bhotfix", r"\bcorrect"],
    "Changed": [r"^refactor\b", r"^perf\b", r"^chore\b", r"^style\b", r"^docs\b", r"^test\b",
                r"\bupdate", r"\bmodify", r"\bimprove", r"\benhance", r"\bupgrade", r"\bchange\b"],
    "Removed": [r"^remove\b", r"^delete\b", r"^drop\b", r"\bdeprecate", r"\brevert", r"\bclean\b"],
}


def run_git(args, cwd=None):
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"git error: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def categorize(subject):
    s = subject.lower()
    for cat, patterns in CATEGORIES.items():
        if any(re.search(p, s) for p in patterns):
            return cat
    return "Other"


def get_commits(since, repo):
    ref = f"{since}..HEAD" if since else "HEAD"
    out = run_git(["log", ref, "--pretty=format:%H|%s|%an|%ad", "--date=short"], cwd=repo)
    commits = []
    for line in out.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append(parts)
    return commits


def build_md(commits, name, since):
    groups = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}
    for hsh, subject, author, date in commits:
        groups[categorize(subject)].append((hsh, subject, author, date))

    today = datetime.now().strftime("%Y-%m-%d")
    label = f"[{since} → HEAD]" if since else "[unreleased]"

    lines = [f"# Changelog\n", f"All notable changes to `{name}` will be documented in this file.\n"]
    lines.append(f"## {label} — {today}\n")

    for cat in ("Added", "Changed", "Fixed", "Removed", "Other"):
        items = groups[cat]
        if not items:
            continue
        lines.append(f"### {cat}\n")
        for hsh, subject, author, _ in items:
            lines.append(f"- {subject} (`{hsh[:7]}`) — @{author}\n")
        lines.append("")

    if not any(groups.values()):
        lines.append("_No changes found._\n")

    return "".join(lines)


def main():
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    p.add_argument("--repo", default=".", help="Path to git repository")
    p.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    p.add_argument("--since", help="Start from this tag/commit")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout")
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"Error: {repo} is not a git repository.", file=sys.stderr)
        sys.exit(1)

    since = args.since
    if not since:
        since = run_git(["describe", "--tags", "--abbrev=0"], cwd=str(repo)) or None

    commits = get_commits(since, str(repo))
    if not commits:
        print("No commits found.")
        sys.exit(0)

    md = build_md(commits, repo.name, since)

    if args.dry_run:
        print(md)
    else:
        out = repo / args.output
        out.write_text(md, encoding="utf-8")
        total = len(commits)
        cats = {k: sum(1 for c in commits if categorize(c[1]) == k) for k in CATEGORIES}
        cats["Other"] = total - sum(cats.values())
        print(f"✅ {out}  ({total} commits)")
        print(f"   Added:{cats['Added']} Fixed:{cats['Fixed']} Changed:{cats['Changed']} Removed:{cats['Removed']} Other:{cats['Other']}")
        if since:
            print(f"   Since: {since}")


if __name__ == "__main__":
    main()
