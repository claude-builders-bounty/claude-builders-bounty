#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history since the last tag.

Dependency-free: only requires Python 3.8+ and git.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from typing import List, Optional


def sh(cmd: list[str]) -> str:
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out.decode("utf-8", errors="replace").strip()


def try_last_tag() -> Optional[str]:
    try:
        return sh(["git", "describe", "--tags", "--abbrev=0"]) or None
    except subprocess.CalledProcessError:
        return None


def subjects_since(tag: Optional[str]) -> List[str]:
    rev = "HEAD" if not tag else f"{tag}..HEAD"
    out = sh(["git", "log", "--no-merges", "--pretty=format:%s", rev])
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def bucket(subject: str) -> str:
    lower = subject.lower().strip()
    # Match conventional-commit-ish prefixes using a delimiter so we don't
    # accidentally treat "feature:" as "feat:" etc.
    def _starts(prefixes) -> bool:
        return any(lower.startswith(p) for p in prefixes)

    if _starts(("feat(", "feat:", "feat!", "feat ", "add(", "add:", "add!", "add ")):
        return "Added"
    if _starts(("fix(", "fix:", "fix!", "fix ")):
        return "Fixed"
    if _starts(
        (
            "remove(",
            "remove:",
            "remove!",
            "remove ",
            "delete(",
            "delete:",
            "delete!",
            "delete ",
        )
    ):
        return "Removed"
    return "Changed"


def render(subjects: List[str], tag: Optional[str]) -> str:
    today = dt.date.today().isoformat()
    since_line = "(all commits)" if not tag else f"since tag {tag}"

    buckets: dict[str, list[str]] = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for s in subjects:
        buckets[bucket(s)].append(s)

    def section(name: str) -> str:
        lines = [f"### {name}"]
        if not buckets[name]:
            lines.append("- (none)")
        else:
            lines.extend([f"- {s}" for s in buckets[name]])
        return "\n".join(lines)

    parts = [
        "# Changelog",
        "",
        f"## [Unreleased] - {today}",
        "",
        f"_Generated from git history {since_line}._",
        "",
        section("Added"),
        "",
        section("Fixed"),
        "",
        section("Changed"),
        "",
        section("Removed"),
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="CHANGELOG.md")
    args = ap.parse_args()

    try:
        sh(["git", "rev-parse", "--is-inside-work-tree"])
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"error: must run inside a git repository and have git installed ({exc})", file=sys.stderr)
        return 2

    tag = try_last_tag()
    subjects = subjects_since(tag)
    text = render(subjects, tag)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

