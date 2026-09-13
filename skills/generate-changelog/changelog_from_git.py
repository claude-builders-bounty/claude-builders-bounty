#!/usr/bin/env python3
"""Build CHANGELOG.md from git history (since last tag)."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

CATEGORY = {
    "feat": "Added", "add": "Added", "added": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "fixed": "Fixed",
    "changed": "Changed", "change": "Changed", "refactor": "Changed",
    "perf": "Changed", "docs": "Changed", "build": "Changed",
    "ci": "Changed", "test": "Changed", "chore": "Changed", "style": "Changed",
    "remove": "Removed", "removed": "Removed", "revert": "Removed",
}
ORDER = ["Added", "Fixed", "Changed", "Removed"]
CC = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\([^)]*\))?!?:\s*(?P<subject>.+)$")


def git(*args: str, cwd: Path) -> str:
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return p.stdout.strip()


def last_tag(cwd: Path) -> str | None:
    try:
        return git("describe", "--tags", "--abbrev=0", cwd=cwd) or None
    except subprocess.CalledProcessError:
        return None


def subjects(tag: str | None, cwd: Path) -> list[tuple[str, str]]:
    spec = f"{tag}..HEAD" if tag else "HEAD"
    out = git("log", spec, "--no-merges", "--pretty=format:%h\t%s", cwd=cwd)
    rows = []
    for line in out.splitlines():
        if "\t" in line:
            sha, subj = line.split("\t", 1)
            rows.append((sha.strip(), subj.strip()))
    return rows


def bucket(subject: str) -> tuple[str, str]:
    m = CC.match(subject)
    if m:
        section = CATEGORY.get(m.group("type").lower(), "Changed")
        return section, m.group("subject").strip()
    low = subject.lower()
    for prefix, section in (
        ("add ", "Added"), ("added ", "Added"),
        ("fix ", "Fixed"), ("fixed ", "Fixed"),
        ("remove ", "Removed"), ("removed ", "Removed"),
    ):
        if low.startswith(prefix):
            return section, subject[len(prefix):].strip()
    return "Changed", subject


def render(tag: str | None, rows: list[tuple[str, str]]) -> str:
    groups: dict[str, list[str]] = defaultdict(list)
    for sha, subj in rows:
        section, text = bucket(subj)
        groups[section].append(f"- {text} ({sha})")
    lines = ["# Changelog", "", f"## [{tag or 'Unreleased'}] - {date.today().isoformat()}", ""]
    if not rows:
        lines += ["_No commits in range._", ""]
    else:
        for section in ORDER:
            if section in groups:
                lines += [f"### {section}", ""]
                lines += groups[section]
                lines += [""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args(argv)
    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 1
    tag = last_tag(repo)
    rows = subjects(tag, repo)
    md = render(tag, rows)
    if args.stdout:
        sys.stdout.write(md)
        return 0
    out = args.output or (repo / "CHANGELOG.md")
    out.write_text(md, encoding="utf-8")
    print(f"wrote {out} ({len(rows)} commits, since={tag or 'beginning'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
