#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history since the last tag.

Usage:
  python3 bounty1/generate_changelog.py [--repo PATH] [--output PATH] [--since REF]

Categories: Added / Fixed / Changed / Removed (Conventional Commits + heuristics).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

SECTION_ORDER = ("Added", "Fixed", "Changed", "Removed", "Other")

# Conventional commit type → section
TYPE_MAP = {
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
    "remove": "Removed",
    "delete": "Removed",
    "deprecate": "Removed",
}

SUBJECT_HINTS: list[tuple[str, re.Pattern[str]]] = [
    ("Removed", re.compile(r"\b(remov|delet|drop|deprecat)\w*\b", re.I)),
    ("Fixed", re.compile(r"\b(fix|bug|hotfix|patch|resolv)\w*\b", re.I)),
    ("Added", re.compile(r"\b(add|introduc|creat|implement|support)\w*\b", re.I)),
    ("Changed", re.compile(r"\b(change|update|improv|refactor|rename|bump)\w*\b", re.I)),
]

CONV = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<sub>.*)$"
)


def run_git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)} failed")
    return r.stdout


def last_tag(repo: Path) -> str | None:
    out = subprocess.run(
        ["git", "-C", str(repo), "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def classify(subject: str) -> str:
    m = CONV.match(subject.strip())
    if m:
        t = m.group("type").lower()
        if m.group("breaking"):
            return "Changed"
        if t in TYPE_MAP:
            return TYPE_MAP[t]
        subject = m.group("sub")
    for section, pat in SUBJECT_HINTS:
        if pat.search(subject):
            return section
    return "Other"


def clean_subject(subject: str) -> str:
    m = CONV.match(subject.strip())
    body = m.group("sub").strip() if m else subject.strip()
    body = re.sub(r"\s*\(#\d+\)\s*$", "", body)
    body = body[0].upper() + body[1:] if body else body
    return body.rstrip(".")


def collect_commits(repo: Path, since: str | None) -> list[tuple[str, str, str]]:
    """Return list of (sha, subject, author_date)."""
    rng = f"{since}..HEAD" if since else "HEAD"
    fmt = "%H%x1f%s%x1f%ad"
    try:
        out = run_git(
            repo,
            "log",
            rng,
            f"--pretty=format:{fmt}",
            "--date=short",
            "--no-merges",
        )
    except RuntimeError:
        # empty range
        return []
    rows: list[tuple[str, str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        sha, subject, day = parts
        rows.append((sha[:7], subject, day))
    return rows


def render(version_label: str, commits: list[tuple[str, str, str]]) -> str:
    buckets: dict[str, list[str]] = defaultdict(list)
    seen: set[str] = set()
    for sha, subject, _day in commits:
        text = clean_subject(subject)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        sec = classify(subject)
        buckets[sec].append(f"- {text} ({sha})")

    lines = [
        f"## [{version_label}] - {date.today().isoformat()}",
        "",
    ]
    any_item = False
    for sec in SECTION_ORDER:
        items = buckets.get(sec) or []
        if not items:
            continue
        any_item = True
        lines.append(f"### {sec}")
        lines.append("")
        lines.extend(items)
        lines.append("")
    if not any_item:
        lines.append("_No commits in range._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def merge_into_changelog(path: Path, block: str) -> str:
    header = "# Changelog\n\nAll notable changes are documented in this file.\n\n"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        # strip leading H1 if present
        body = existing
        if body.lstrip().startswith("# "):
            # keep after first blank line following title
            parts = body.split("\n", 2)
            if len(parts) >= 3:
                body = parts[2]
            else:
                body = ""
        return header + block + "\n" + body.lstrip()
    return header + block


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--since", default=None, help="git ref (default: last tag)")
    p.add_argument("--stdout", action="store_true")
    p.add_argument("--version", default=None, help="version label for heading")
    args = p.parse_args(argv)

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(f"error: not a git repo: {repo}", file=sys.stderr)
        return 2

    since = args.since if args.since is not None else last_tag(repo)
    commits = collect_commits(repo, since)
    label = args.version or ("Unreleased" if since else "0.1.0")
    if since and not args.version:
        label = f"Unreleased (since {since})"

    block = render(label, commits)
    out_path = args.output or (repo / "CHANGELOG.md")

    if args.stdout:
        sys.stdout.write(block)
        return 0

    text = merge_into_changelog(out_path, block)
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote {out_path} ({len(commits)} commits, since={since or 'ROOT'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
