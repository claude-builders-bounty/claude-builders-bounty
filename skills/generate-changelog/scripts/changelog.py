#!/usr/bin/env python3
"""
changelog.py — Python implementation of the generate-changelog skill.

Same feature set as changelog.sh, exposed as a module + CLI.

Usage:
    python3 changelog.py [--repo DIR] [--since TAG] [--output FILE]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


HEADER = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

CONVENTIONAL_RE = re.compile(r"^([a-zA-Z]+)(\([^)]+\))?!?:")


@dataclass
class Commit:
    subject: str
    body: str


@dataclass
class Section:
    added: List[str] = field(default_factory=list)
    fixed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.added or self.fixed or self.changed or self.removed)


def categorize(commit: Commit) -> Optional[str]:
    """Return one of: added, fixed, changed, removed, ignored. None → ignore."""
    if "BREAKING CHANGE" in commit.body:
        return "changed"
    m = CONVENTIONAL_RE.match(commit.subject)
    if not m:
        return "changed"
    prefix = m.group(1).lower()
    return {
        "feat": "added",
        "fix": "fixed",
        "refactor": "changed",
        "perf": "changed",
        "style": "changed",
        "revert": "removed",
        "removed": "removed",
        "docs": "ignored",
        "test": "ignored",
        "chore": "ignored",
        "build": "ignored",
        "ci": "ignored",
    }.get(prefix, "changed")


def run_git_log(repo: Path, range_: Optional[str]) -> List[Commit]:
    args = ["git", "log", "--no-merges", "--format=%H%x00%s%x00%b%x00---END---"]
    if range_:
        args.append(range_)
    try:
        out = subprocess.check_output(args, cwd=repo, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"git log failed: {e.stderr}\n")
        return []

    commits = []
    for block in out.split("---END---\n"):
        block = block.strip("\x00\n ")
        if not block:
            continue
        parts = block.split("\x00", 2)
        if len(parts) < 2:
            continue
        subject = parts[1] if len(parts) >= 2 else ""
        body = parts[2] if len(parts) >= 3 else ""
        commits.append(Commit(subject=subject, body=body))
    return commits


def list_tags(repo: Path) -> List[str]:
    try:
        out = subprocess.check_output(
            ["git", "tag", "--sort=-v:refname"], cwd=repo, text=True
        )
    except subprocess.CalledProcessError:
        return []
    return [t for t in out.splitlines() if t]


def build_section(repo: Path, range_: Optional[str], title: str) -> str:
    commits = run_git_log(repo, range_)
    section = Section()
    for c in commits:
        cat = categorize(c)
        if cat in (None, "ignored"):
            continue
        getattr(section, cat).append(f"- {c.subject}")

    out = [f"\n## [{title}]\n"]
    for label, key in [
        ("Added", "added"),
        ("Fixed", "fixed"),
        ("Changed", "changed"),
        ("Removed", "removed"),
    ]:
        items = getattr(section, key)
        if items:
            out.append(f"\n### {label}\n")
            out.extend(f"{i}\n" for i in items)
    if section.is_empty():
        out.append("\n_No notable changes._\n")
    return "".join(out)


def render(repo: Path, since: Optional[str]) -> str:
    tags = [t for t in list_tags(repo) if not t.startswith("-")]
    body = [HEADER]

    if not tags:
        body.append(build_section(repo, None, "Unreleased"))
    else:
        body.append(build_section(repo, f"{tags[0]}..HEAD", "Unreleased"))
        # walk tag pairs (newer, older) → section per tag
        for i in range(len(tags) - 1):
            newer, older = tags[i], tags[i + 1]
            body.append(build_section(repo, f"{older}..{newer}", newer))
        # initial range (oldest tag → its first parent commit)
        body.append(build_section(repo, tags[-1], f"{tags[-1]} — initial and prior"))

    return "".join(body)


def _is_valid_refish(value: str) -> bool:
    """Reject values that git could interpret as command-line options."""
    if not value:
        return False
    if value.startswith("-"):
        return False
    if " " in value or "\t" in value:
        return False
    return True


def main() -> int:
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    p.add_argument("--repo", default=".", help="Path to a git repository.")
    p.add_argument("--since", default=None, help="Override: emit commits since this tag.")
    p.add_argument("--output", default="CHANGELOG.md", help="Output file path.")
    args = p.parse_args()

    if args.since and not _is_valid_refish(args.since):
        sys.stderr.write("ERROR: --since must be a valid tag/ref and cannot start with '-' or contain spaces\n")
        return 1

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        sys.stderr.write(f"ERROR: {repo} is not a git repo\n")
        return 1

    out = render(repo, args.since)
    Path(args.output).write_text(out, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())