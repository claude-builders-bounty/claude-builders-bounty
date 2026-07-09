#!/usr/bin/env python3
"""Generate a Keep a Changelog style CHANGELOG.md from git history.

Usage:
    python generate_changelog.py [output_file]
    python generate_changelog.py CHANGELOG.md

Fetches commits since the last git tag (or all commits if none),
auto-categorizes into Added / Fixed / Changed / Removed, and writes CHANGELOG.md.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

# Conventional commit type -> category
TYPE_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "adds": "Added",
    "added": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "bug": "Fixed",
    "hotfix": "Fixed",
    "patch": "Fixed",
    "remove": "Removed",
    "removed": "Removed",
    "rm": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
    "deprecate": "Removed",
    "deprecated": "Removed",
    "refactor": "Changed",
    "style": "Changed",
    "perf": "Changed",
    "performance": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "revert": "Changed",
    "change": "Changed",
    "changed": "Changed",
    "update": "Changed",
    "updated": "Changed",
    "docs": "Changed",
    "doc": "Changed",
    "test": "Changed",
    "tests": "Changed",
}

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\([^)]*\))?(!)?:\s*(?P<subject>.*)$"
)

KEYWORD_RULES: List[Tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"(^|[^a-z])(add|added|introduce|introduces|new feature|implement|implements|create|creates)([^a-z]|$)",
            re.I,
        ),
        "Added",
    ),
    (
        re.compile(
            r"(^|[^a-z])(fix|fixed|bug|hotfix|patch|resolve|resolves)([^a-z]|$)",
            re.I,
        ),
        "Fixed",
    ),
    (
        re.compile(
            r"(^|[^a-z])(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)([^a-z]|$)",
            re.I,
        ),
        "Removed",
    ),
    (
        re.compile(
            r"(^|[^a-z])(change|changed|update|updated|refactor|improve|improves|rename|renamed)([^a-z]|$)",
            re.I,
        ),
        "Changed",
    ),
]


def run_git(args: List[str], cwd: Optional[Path] = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def repo_root() -> Path:
    out = run_git(["rev-parse", "--show-toplevel"])
    return Path(out) if out else Path.cwd()


def last_git_tag(root: Path) -> Optional[str]:
    tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=root)
    return tag or None


def commit_log(root: Path, since_tag: Optional[str]) -> List[Tuple[str, str]]:
    """Return list of (short_hash, subject) newest-first."""
    fmt = "%h\t%s"
    args = ["log", "--no-merges", f"--pretty=format:{fmt}"]
    if since_tag:
        args.append(f"{since_tag}..HEAD")
    raw = run_git(args, cwd=root)
    commits: List[Tuple[str, str]] = []
    if not raw:
        return commits
    for line in raw.splitlines():
        line = line.strip()
        if not line or "\t" not in line:
            continue
        h, subject = line.split("\t", 1)
        if h and subject:
            commits.append((h.strip(), subject.strip()))
    return commits


def categorize(message: str) -> str:
    msg = message.strip()
    m = CONVENTIONAL_RE.match(msg)
    if m:
        ctype = m.group("type").lower()
        if ctype in TYPE_MAP:
            return TYPE_MAP[ctype]

    for pattern, cat in KEYWORD_RULES:
        if pattern.search(msg):
            return cat
    return "Changed"


def clean_subject(message: str) -> str:
    m = CONVENTIONAL_RE.match(message.strip())
    subject = m.group("subject").strip() if m else message.strip()
    subject = re.sub(r"\s*\(#\d+\)$", "", subject).strip()
    if subject:
        subject = subject[0].upper() + subject[1:]
    return subject or message.strip()


def remote_url(root: Path) -> Optional[str]:
    url = run_git(["remote", "get-url", "origin"], cwd=root)
    if not url:
        return None
    url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
    url = re.sub(r"\.git$", "", url)
    return url


def render(
    grouped: Dict[str, List[str]],
    last_tag: Optional[str],
    today: str,
) -> str:
    lines: List[str] = [
        "# Changelog",
        "",
        "All notable changes to this project are documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
        f"## [Unreleased] - {today}",
        "",
    ]
    if last_tag:
        lines.append(f"_Commits since `{last_tag}`._")
    else:
        lines.append("_Generated from full git history (no tags found)._")
    lines.append("")

    total = 0
    for cat in CATEGORIES:
        items = grouped.get(cat, [])
        if not items:
            continue
        total += len(items)
        lines.append(f"### {cat}")
        lines.append("")
        lines.extend(items)
        lines.append("")

    if total == 0:
        lines.append("_No commits found in range._")
        lines.append("")

    if last_tag:
        lines.extend(["---", "", f"Previous release tag: `{last_tag}`", ""])

    return "\n".join(lines)


def generate(output: Path, root: Optional[Path] = None) -> Path:
    root = root or repo_root()
    last_tag = last_git_tag(root)
    commits = commit_log(root, last_tag)
    grouped: Dict[str, List[str]] = defaultdict(list)

    for short_hash, subject in commits:
        cat = categorize(subject)
        cleaned = clean_subject(subject)
        bullet = f"- {cleaned} (`{short_hash}`)"
        grouped[cat].append(bullet)

    today = date.today().isoformat()
    text = render(grouped, last_tag, today)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    return output


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from git history since the last tag."
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="CHANGELOG.md",
        help="Output file path (default: CHANGELOG.md)",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    out = Path(args.output)
    if not out.is_absolute():
        out = root / out

    generate(out, root=root)

    last_tag = last_git_tag(root)
    commits = commit_log(root, last_tag)
    counts = defaultdict(int)
    for _, subject in commits:
        counts[categorize(subject)] += 1

    print(f"Wrote {out}")
    print(f"  Range : {last_tag + '..HEAD' if last_tag else 'FULL HISTORY'}")
    print(f"  Tag   : {last_tag or '<none>'}")
    print(
        "  Counts: "
        + " ".join(f"{c}={counts[c]}" for c in CATEGORIES)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
