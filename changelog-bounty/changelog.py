#!/usr/bin/env python3
"""
changelog.py — Generate a structured CHANGELOG.md from git history.

Usage:
    python3 changelog.py [--since v1.0.0] [--output CHANGELOG.md] [--repo .]
    python3 changelog.py --from-tag v0.9.0 --to-tag v1.0.0

Groups commits by Conventional Commit type (feat, fix, docs, refactor, ...)
and emits a Keep-a-Changelog flavored markdown file. Unreleased commits are
summarized too. Designed to be wrapped by a Claude Code SKILL.

Exit codes:
    0  success
    1  no git repo / no commits
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

TYPE_HEADINGS = {
    "feat": "Added",
    "fix": "Fixed",
    "docs": "Documentation",
    "refactor": "Changed",
    "perf": "Performance",
    "test": "Tests",
    "build": "Build",
    "ci": "CI",
    "chore": "Chores",
    "style": "Style",
}
DEFAULT_TYPES = ", ".join(TYPE_HEADINGS)


def run_git(args: list[str], repo: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"git error: {e.stderr.strip()}\n")
        sys.exit(1)


def parse_commit(line: str) -> tuple[str, str, str]:
    """line looks like:  <hash>\u0001<title>"""
    try:
        h, title = line.split("\u0001", 1)
    except ValueError:
        return ("chore", line, "")
    # strip scope: feat(api): ... -> feat / (api)
    head = title.split(":", 1)[0].strip().lower()
    ctype = head.split("(", 1)[0]
    return (ctype, title.strip(), h)


def collect_commits(repo: str, since: str | None, from_tag: str | None, to_tag: str | None) -> list[tuple[str, str, str]]:
    rev = ""
    if from_tag and to_tag:
        rev = f"{from_tag}..{to_tag}"
    elif since:
        rev = f"--since={since}"
    fmt = "%H%x01%s"
    args = ["log", f"--pretty=format:{fmt}", "--no-merges"]
    if rev:
        args.append(rev)
    raw = run_git(args, repo).strip()
    if not raw:
        return []
    return [parse_commit(l) for l in raw.splitlines()]


def render(commits: list[tuple[str, str, str]], title: str) -> str:
    buckets: dict[str, list[str]] = {v: [] for v in TYPE_HEADINGS.values()}
    for ctype, title_txt, _h in commits:
        heading = TYPE_HEADINGS.get(ctype, "Changed")
        buckets[heading].append(f"- {title_txt}")

    lines = [
        "# Changelog",
        "",
        f"## {title} — {date.today().isoformat()}",
        "",
    ]
    for heading, items in buckets.items():
        if items:
            lines.append(f"### {heading}")
            lines.extend(items)
            lines.append("")
    if not any(buckets.values()):
        lines.append("_No notable changes._")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--output", default="CHANGELOG.md")
    ap.add_argument("--since", default=None, help="e.g. 2026-01-01 or '2 weeks ago'")
    ap.add_argument("--from-tag", default=None)
    ap.add_argument("--to-tag", default=None)
    ap.add_argument("--title", default="Unreleased")
    ap.add_argument("--print", action="store_true", help="print to stdout instead of writing")
    args = ap.parse_args()

    commits = collect_commits(args.repo, args.since, args.from_tag, args.to_tag)
    if not commits:
        sys.stderr.write("No commits found for the given range.\n")
        sys.exit(1)

    doc = render(commits, args.title)
    if args.print:
        print(doc)
    else:
        Path(args.output).write_text(doc, encoding="utf-8")
        print(f"Wrote {len(commits)} commits to {args.output}")


if __name__ == "__main__":
    main()
