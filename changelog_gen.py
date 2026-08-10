#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
changelog_gen.py — Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog_gen.py [--out CHANGELOG.md] [--from-tag <tag>]

Fetches commits since the last git tag (or --from-tag), auto-categorizes
them into Added / Fixed / Changed / Removed, and writes a properly
formatted CHANGELOG.md.

Requirements: git must be installed and the command must run inside a
git repository (or any subdirectory of one).
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime


# Keyword → category mapping. Order matters: first match wins.
# A commit is categorized by scanning its subject + body for these patterns.
RULES = [
    ("Removed", re.compile(r"\b(remove|removed|removal|drop|dropped|delete|deleted|deprecat)\w*", re.IGNORECASE)),
    ("Fixed", re.compile(r"\b(fix|fixed|fixes|bugfix|bug|hotfix|repair|patch)\w*", re.IGNORECASE)),
    ("Changed", re.compile(r"\b(change|changed|update|updated|upgrade|upgraded|migrat|refactor|improv|bump)\w*", re.IGNORECASE)),
    ("Added", re.compile(r"\b(add|added|feat|feature|new|introduce|implement|support|create)\w*", re.IGNORECASE)),
]


def git(*args: str) -> str:
    """Run a git command and return its stdout (stripped)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
    except FileNotFoundError:
        sys.exit("Error: git is not installed or not on PATH.")
    except subprocess.TimeoutExpired:
        sys.exit("Error: git command timed out.")
    if proc.returncode != 0:
        sys.exit(f"Error: git {' '.join(args)} failed:\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def last_tag() -> str | None:
    """Return the most recent tag reachable from HEAD, or None."""
    tag = git("describe", "--tags", "--abbrev=0", "--always")
    return None if tag == "HEAD" else tag


def categorize(subject: str, body: str) -> str:
    """Classify a commit into Added / Fixed / Changed / Removed."""
    text = f"{subject}\n{body}"
    for category, pattern in RULES:
        if pattern.search(text):
            return category
    return "Changed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--out", default="CHANGELOG.md", help="Output file (default: CHANGELOG.md)")
    parser.add_argument("--from-tag", default=None, help="Generate entries since this tag (default: last tag, or all history)")
    args = parser.parse_args()

    # Determine the range of commits.
    tag = args.from_tag or last_tag()
    if tag:
        range_spec = f"{tag}..HEAD"
        source = f"since tag `{tag}`"
    else:
        range_spec = "HEAD"
        source = "from the beginning of history"

    # Subject/body per commit, in reverse chronological order.
    fmt = "%H%x00%s%x00%b%x00%an%x00%aI"
    log = git("log", range_spec, "--no-merges", f"--pretty=format:{fmt}")
    entries: dict[str, list[tuple[str, str, str]]] = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}

    if log:
        for chunk in log.split("\x00\x00"):
            chunk = chunk.strip("\x00").strip()
            if not chunk:
                continue
            parts = chunk.split("\x00")
            if len(parts) < 5:
                continue
            sha, subject, body, author, iso_date = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                date = datetime.fromisoformat(iso_date).strftime("%Y-%m-%d")
            except ValueError:
                date = iso_date[:10]
            category = categorize(subject, body)
            short_sha = sha[:7]
            line = f"- {subject.strip()} ([`{short_sha}`](https://github.com/REPLACE_ME/REPLACE_ME/commit/{sha})) — {author}"
            entries[category].append((date, line))

    lines = [
        "# Changelog",
        "",
        f"All notable changes to this project, {source}.",
        "",
    ]
    for category in ("Added", "Fixed", "Changed", "Removed"):
        if entries[category]:
            lines.append(f"## {category}")
            lines.append("")
            for _, line in sorted(entries[category], reverse=True):
                lines.append(line)
            lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Wrote {args.out} with {sum(len(v) for v in entries.values())} entries ({source}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
