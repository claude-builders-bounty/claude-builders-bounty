#!/usr/bin/env python3
"""Generate a Keep-a-Changelog style CHANGELOG.md from git history.

Zero third-party deps. Safe: commit subjects are never executed, only printed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

# Conventional-commit type → category. Checked before free-text heuristics.
CONV_TYPE_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "style": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "docs": "Changed",
    "test": "Changed",
    "revert": "Changed",
    "remove": "Removed",
    "rm": "Removed",
    "delete": "Removed",
    "deprecate": "Removed",
}

# Free-text keyword rules: (regex, category). First match wins.
# Order matters: Fixed before Removed so "fix remove button" → Fixed.
HEURISTICS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(fix|bug|hotfix|patch|resolv|correct)\b", re.I), "Fixed"),
    (re.compile(r"\b(add|added|new|implement|introduc|support|creat)\w*\b", re.I), "Added"),
    (re.compile(r"\b(remov|delet|drop|deprecat|uninstall)\w*\b", re.I), "Removed"),
    (re.compile(r"\b(chang|updat|improv|refactor|renam|migrat|bump|adjust|tweak)\w*\b", re.I), "Changed"),
]

CONV_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?P<scope>\([^)]*\))?(?P<breaking>!)?:\s*(?P<rest>.+)$"
)


def run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or f"git {' '.join(args)} failed"
        raise RuntimeError(err)
    return proc.stdout


def last_tag(repo: Path) -> str | None:
    try:
        tag = run_git(repo, "describe", "--tags", "--abbrev=0").strip()
        return tag or None
    except RuntimeError:
        return None


def collect_commits(repo: Path, since: str | None) -> list[tuple[str, str]]:
    if since:
        run_git(repo, "rev-parse", "--verify", since)  # validate ref
        range_spec = f"{since}..HEAD"
    else:
        range_spec = "HEAD"
    out = run_git(
        repo,
        "log",
        range_spec,
        "--pretty=tformat:%h%x00%s",
        "--no-merges",
    )
    commits: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        if "\x00" not in line:
            continue
        h, s = line.split("\x00", 1)
        # Never interpret subject as shell — strip NULs just in case
        commits.append((h.strip(), s.replace("\x00", "").strip()))
    return commits


def categorize(subject: str) -> tuple[str, str, bool]:
    """Return (category, display_subject, is_breaking).

    Display keeps the original subject (safe literal). Category comes from
    Conventional Commits when present, else keyword heuristics.
    """
    display = subject
    m = CONV_RE.match(subject)
    breaking = False
    if m:
        ctype = m.group("type").lower()
        breaking = bool(m.group("breaking")) or ctype == "breaking"
        rest = m.group("rest").strip()
        if ctype in CONV_TYPE_MAP:
            cat = CONV_TYPE_MAP[ctype]
            if breaking and cat != "Removed":
                cat = "Changed"
            return cat, display, breaking
        subject_for_heur = rest
    else:
        subject_for_heur = subject

    lower = subject_for_heur.lower()
    if "breaking change" in lower or lower.startswith("break"):
        return "Changed", display, True

    for rx, cat in HEURISTICS:
        if rx.search(subject_for_heur):
            return cat, display, breaking
    return "Changed", display, breaking


def render(
    commits: list[tuple[str, str]],
    *,
    since: str | None,
    title: str,
    date: str,
) -> str:
    buckets: dict[str, list[str]] = defaultdict(list)
    for h, subject in commits:
        cat, display, breaking = categorize(subject)
        flag = " ⚠️ BREAKING" if breaking else ""
        # Escape nothing special for markdown bullets; avoid leading/trailing spaces
        buckets[cat].append(f"- {display} (`{h}`){flag}")

    lines: list[str] = [
        "# Changelog",
        "",
        "All notable changes are documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).",
        "",
        f"## [{title}] - {date}",
        "",
    ]
    if since:
        lines.append(f"_Commits since `{since}` → `HEAD`._")
    else:
        lines.append("_Full repository history (no tags found)._")
    lines.append("")

    any_items = False
    for cat in CATEGORIES:
        items = buckets.get(cat) or []
        if not items:
            continue
        any_items = True
        lines.append(f"### {cat}")
        lines.append("")
        lines.extend(items)
        lines.append("")

    if not any_items:
        lines.append("_No non-merge commits in this range._")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def prepend_into_existing(path: Path, section: str) -> str:
    """Insert the new ## section after the title block of an existing CHANGELOG."""
    if not path.exists():
        return section
    existing = path.read_text(encoding="utf-8")
    # Extract just the ## [..] block from freshly rendered section (skip top title)
    m = re.search(r"(## \[.+?)(?=\n## |\Z)", section, re.S)
    new_block = (m.group(1).rstrip() + "\n\n") if m else section
    # If file already starts with # Changelog, insert after intro
    if re.match(r"#\s*Changelog", existing, re.I):
        # Find first ## heading
        hm = re.search(r"^##\s", existing, re.M)
        if hm:
            return existing[: hm.start()] + new_block + existing[hm.start() :]
        return existing.rstrip() + "\n\n" + new_block
    return new_block + existing


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history since the last tag.",
    )
    p.add_argument("-o", "--output", default="CHANGELOG.md", help="Output path (default: CHANGELOG.md)")
    p.add_argument("--since", default=None, help="Start ref/tag (default: latest tag, or full history)")
    p.add_argument("--repo", default=".", help="Path to git repository (default: .)")
    p.add_argument("--title", default="Unreleased", help="Section title (default: Unreleased)")
    p.add_argument("--date", default=None, help="Section date ISO (default: today UTC)")
    p.add_argument(
        "--prepend",
        action="store_true",
        help="Prepend the new section into an existing CHANGELOG.md instead of overwriting",
    )
    p.add_argument("--dry-run", action="store_true", help="Print to stdout only; do not write a file")
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists() and not (repo / ".git").is_file():
        # worktree / submodule: still ask git
        try:
            run_git(repo, "rev-parse", "--git-dir")
        except RuntimeError as e:
            print(f"error: '{repo}' is not a git repository ({e})", file=sys.stderr)
            return 1

    since = args.since
    if since is None:
        since = last_tag(repo)

    try:
        commits = collect_commits(repo, since)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    text = render(commits, since=since, title=args.title, date=date)

    out = Path(args.output)
    if not out.is_absolute():
        out = Path.cwd() / out

    if args.prepend and out.exists() and not args.dry_run:
        text = prepend_into_existing(out, text)

    if args.dry_run:
        sys.stdout.write(text)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        range_label = f"{since} → HEAD" if since else "full history"
        print(f"wrote {out} ({len(commits)} commits from {range_label})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
