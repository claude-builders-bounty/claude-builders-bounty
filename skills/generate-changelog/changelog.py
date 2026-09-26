#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Usage:
    python3 changelog.py [--stdout] [--output FILE] [--since TAG] [--repo DIR]

Reads commits since the last git tag (or all history when no tag exists),
auto-categorizes them into Added / Fixed / Changed / Removed, and writes a
Keep-a-Changelog style CHANGELOG.md.
"""

import argparse
import re
import subprocess
import sys
from collections import OrderedDict

CATEGORIES = ["Added", "Fixed", "Changed", "Removed"]

# (category, regex) in priority order; first match wins.
RULES = [
    ("Added", re.compile(r"\b(feat|feature|add|new|implement|introduce|support)\b", re.I)),
    ("Fixed", re.compile(r"\b(fix|bug|patch|hotfix|resolve|correct)\b", re.I)),
    ("Removed", re.compile(r"\b(remove|delete|drop|deprecat|uninstall)\b", re.I)),
    ("Changed", re.compile(r"\b(refactor|change|update|improve|enhance|perf|optimi|docs|style|test|ci|build|chore|bump|migrat|rename|move)\b", re.I)),
]


def run_git(args, repo):
    return subprocess.run(
        ["git", "-C", repo] + args,
        capture_output=True, text=True, check=True,
    ).stdout


def last_tag(repo):
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], repo).strip()
    except subprocess.CalledProcessError:
        return None


def commits_since(repo, since):
    rev_range = f"{since}..HEAD" if since else "HEAD"
    fmt = "%H%x1f%h%x1f%s%x1f%b%x1e"
    try:
        out = run_git(["log", rev_range, f"--pretty=format:{fmt}", "--no-merges"], repo)
    except subprocess.CalledProcessError:
        # Empty repo (no commits yet) or unreadable range: nothing to report.
        return []
    commits = []
    for chunk in out.split("\x1e"):
        # Don't strip(): it would mutate commit bodies (indentation, blank
        # lines). Only drop the trailing newline git appends after the last
        # record separator.
        chunk = chunk.rstrip("\n")
        if not chunk:
            continue
        sha, short, subject, body = (chunk.split("\x1f") + ["", "", "", ""])[:4]
        commits.append({"sha": sha, "short": short, "subject": subject.strip(), "body": body})
    return commits


def categorize(subject, body=""):
    # BREAKING CHANGE footer wins over everything: it's a breaking change.
    if "BREAKING CHANGE" in body:
        return "Changed"
    # Conventional-commit prefix wins, e.g. "feat:", "fix(scope):".
    m = re.match(r"^(\w+)(?:\([^)]*\))?(!)?:", subject)
    if m:
        prefix = m.group(1).lower()
        breaking = m.group(2)
        if breaking:
            return "Changed"
        mapping = {
            "feat": "Added", "feature": "Added", "add": "Added",
            "fix": "Fixed", "bugfix": "Fixed", "patch": "Fixed", "hotfix": "Fixed",
            "remove": "Removed", "delete": "Removed", "drop": "Removed", "deprecate": "Removed",
        }
        if prefix in mapping:
            return mapping[prefix]
    text = subject
    for category, pattern in RULES:
        if pattern.search(text):
            return category
    return "Changed"


def render(grouped, version_label):
    lines = ["# Changelog", ""]
    lines.append(f"## [{version_label}] - auto-generated from git history")
    lines.append("")
    total = 0
    for cat in CATEGORIES:
        items = grouped[cat]
        if not items:
            continue
        lines.append(f"### {cat}")
        lines.append("")
        for c in items:
            lines.append(f"- {c['subject']} ({c['short']})")
            total += 1
        lines.append("")
    if total == 0:
        lines.append("_No categorized commits found in range._")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    ap.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing CHANGELOG.md")
    ap.add_argument("--output", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    ap.add_argument("--since", default=None, help="Start from this tag/ref instead of the last tag")
    ap.add_argument("--repo", default=".", help="Path to the git repository (default: .)")
    args = ap.parse_args()

    try:
        run_git(["rev-parse", "--git-dir"], args.repo)
    except subprocess.CalledProcessError:
        print(f"error: '{args.repo}' is not a git repository", file=sys.stderr)
        sys.exit(1)

    since = args.since or last_tag(args.repo)
    if since and since.startswith("-"):
        # Guard against git option injection via --since (e.g. "--since=-p"
        # would otherwise be parsed as a git flag).
        print(f"error: invalid --since value: {since!r}", file=sys.stderr)
        sys.exit(1)
    commits = commits_since(args.repo, since)

    grouped = OrderedDict((c, []) for c in CATEGORIES)
    for c in commits:
        grouped[categorize(c["subject"], c["body"])].append(c)

    version_label = "Unreleased" if since is None else f"Unreleased (since {since})"
    markdown = render(grouped, version_label)

    if args.stdout:
        print(markdown)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Wrote {sum(len(v) for v in grouped.values())} entries "
              f"to {args.output} (since: {since or 'beginning of history'})")


if __name__ == "__main__":
    main()
