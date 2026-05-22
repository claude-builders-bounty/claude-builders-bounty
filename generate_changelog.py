#!/usr/bin/env python3
"""
Generate a structured CHANGELOG.md from git history.

Auto-categorizes commits by conventional-commit prefix or keyword matching
into: Added / Fixed / Changed / Removed.  Outputs a KeepAChangelog-formatted
CHANGELOG.md in the current directory.
"""

import subprocess
import re
import sys
from collections import defaultdict
from datetime import datetime


# ── categorization ────────────────────────────────────────────────

# (prefix, category) ordered so 'feature' matches before 'feat'
PREFIX_MAP = [
    ("feature:",  "Added"),
    ("feat(",     "Added"),
    ("feat:",     "Added"),
    ("add(",      "Added"),
    ("add:",      "Added"),
    ("new:",      "Added"),
    ("implement:", "Added"),
    ("introduce:","Added"),
    ("fix(",      "Fixed"),
    ("fix:",      "Fixed"),
    ("bugfix:",   "Fixed"),
    ("hotfix:",   "Fixed"),
    ("patch:",    "Fixed"),
    ("resolve:",  "Fixed"),
    ("correct:",  "Fixed"),
    ("remove:",   "Removed"),
    ("delete:",   "Removed"),
    ("drop:",     "Removed"),
    ("deprecate:","Removed"),
    ("eliminate:","Removed"),
    ("refactor:", "Changed"),
    ("update:",   "Changed"),
    ("change:",   "Changed"),
    ("improve:",  "Changed"),
    ("enhance:",  "Changed"),
    ("chore:",    "Changed"),
    ("style:",    "Changed"),
    ("docs:",     "Changed"),
    ("test(",     "Changed"),
    ("test:",     "Changed"),
    ("perf:",     "Changed"),
    ("ci:",       "Changed"),
    ("build:",    "Changed"),
    ("revert:",   "Changed"),
]

KEYWORD_MAP = [
    (["add", "new", "feature", "introduce", "implement", "create"], "Added"),
    (["fix", "fixed", "bug", "repair", "resolve", "correct", "patch"], "Fixed"),
    (["remove", "delete", "drop", "eliminate", "deprecated", "obsolete"], "Removed"),
    (["update", "change", "modify", "refactor", "improve", "enhance",
      "upgrade", "tweak", "cleanup", "chore", "docs", "style", "test",
      "ci", "build", "perf", "revert", "adjust", "polish"], "Changed"),
]


def categorize(message: str) -> str:
    """Return Added / Fixed / Changed / Removed for *message*."""
    lower = message.strip().lower()

    # 1 — conventional-commit prefix (exact start-of-line)
    for prefix, category in PREFIX_MAP:
        if lower.startswith(prefix):
            return category

    # 2 — keyword heuristic (first hit wins)
    for keywords, category in KEYWORD_MAP:
        for kw in keywords:
            # word-boundary-ish: spaces + start/end + punctuation
            if re.search(rf"(?<![a-z]){re.escape(kw)}(?![a-z])", lower):
                return category

    return "Changed"  # safe default


# ── git helpers ────────────────────────────────────────────────────

def git(*args: str) -> str | None:
    """Run `git ...` and return stripped stdout, or None on failure."""
    try:
        r = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return None
        return r.stdout.strip()
    except Exception:
        return None


def get_last_tag() -> str | None:
    return git("describe", "--tags", "--abbrev=0")


def get_commits(since_tag: str | None) -> list[dict]:
    """Return list of {hash, date, message} since *since_tag*."""
    range_spec = f"{since_tag}..HEAD" if since_tag else "HEAD"
    raw = git("log", range_spec, "--pretty=format:%H|%ad|%s", "--date=short")
    if not raw:
        return []

    commits: list[dict] = []
    for line in raw.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({"hash": parts[0][:7], "date": parts[1], "message": parts[2]})
    return commits


# ── output ─────────────────────────────────────────────────────────

def strip_prefix(message: str) -> str:
    """Remove conventional-commit prefix and scope for display."""
    return re.sub(
        r"^(feature|feat|fix|bugfix|add|new|remove|delete|drop|refactor|"
        r"update|change|improve|enhance|chore|style|docs|test|perf|ci|"
        r"build|revert|hotfix|patch|resolve|correct|deprecate|eliminate|"
        r"introduce|implement)"
        r"(\([^)]*\))?:\s*",
        "", message, count=1, flags=re.IGNORECASE,
    ).strip()


def build_changelog(commits: list[dict], tag: str | None) -> str:
    groups: dict[str, list[dict]] = defaultdict(list)
    for c in commits:
        groups[categorize(c["message"])].append(c)

    version = tag or "Unreleased"
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        f"## [{version}] - {today}",
        "",
    ]
    for cat in ("Added", "Fixed", "Changed", "Removed"):
        group = groups.get(cat, [])
        if not group:
            continue
        lines.append(f"### {cat}")
        lines.append("")
        for c in group:
            clean = strip_prefix(c["message"])
            lines.append(f"- {clean} ({c['hash']})")
        lines.append("")
    return "\n".join(lines)


# ── main ───────────────────────────────────────────────────────────

def main() -> None:
    if git("rev-parse", "--git-dir") is None:
        print("❌ Error: not a git repository", file=sys.stderr)
        sys.exit(1)

    tag = get_last_tag()
    if tag:
        print(f"📋 Last tag: {tag}")
    else:
        print("📋 No tags found — using all commits")

    commits = get_commits(tag)
    if not commits:
        print("⚠️  No commits found since last tag. Nothing to generate.")
        sys.exit(0)

    print(f"📥 Found {len(commits)} commits")

    changelog = build_changelog(commits, tag)
    with open("CHANGELOG.md", "w") as f:
        f.write(changelog)

    # summary
    counts: dict[str, int] = defaultdict(int)
    for c in commits:
        counts[categorize(c["message"])] += 1
    print(f"✅ CHANGELOG.md written")
    for cat in ("Added", "Fixed", "Changed", "Removed"):
        if counts.get(cat):
            print(f"   {cat}: {counts[cat]}")


if __name__ == "__main__":
    main()
