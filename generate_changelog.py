#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import subprocess
import sys


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def category(subject: str) -> str:
    normalized = subject.lower()
    if normalized.startswith(("feat:", "feature:", "add:", "added:")):
        return "Added"
    if normalized.startswith(("fix:", "bugfix:", "hotfix:")):
        return "Fixed"
    if normalized.startswith(("remove:", "removed:", "delete:", "deleted:", "drop:")):
        return "Removed"
    if any(token in normalized for token in (" add ", " adds ", " introduce ", " introduces ")):
        return "Added"
    if any(token in normalized for token in (" fix ", " fixes ", " bug ", " repair ")):
        return "Fixed"
    if any(token in normalized for token in (" remove ", " removes ", " delete ", " deletes ")):
        return "Removed"
    return "Changed"


def collect_commits() -> tuple[str, list[tuple[str, str]]]:
    latest_tag = git("describe", "--tags", "--abbrev=0")
    if latest_tag:
        commit_range = f"{latest_tag}..HEAD"
        label = f"since {latest_tag}"
    else:
        commit_range = "HEAD"
        label = "from repository history"

    raw = git("log", commit_range, "--no-merges", "--pretty=format:%s%x09%h")
    commits: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        if "\t" in line:
            subject, short_hash = line.rsplit("\t", 1)
        else:
            subject, short_hash = line, ""
        commits.append((subject.strip(), short_hash.strip()))
    return label, commits


def render(output_path: pathlib.Path, range_label: str, commits: list[tuple[str, str]]) -> str:
    repo_root = pathlib.Path(git("rev-parse", "--show-toplevel") or ".")
    repo_name = repo_root.name
    today = dt.date.today().isoformat()
    buckets = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}

    for subject, short_hash in commits:
        entry = f"- {subject}"
        if short_hash:
            entry += f" (`{short_hash}`)"
        buckets[category(subject)].append(entry)

    lines = [
        "# Changelog",
        "",
        f"## {today}",
        "",
        f"Generated for `{repo_name}` {range_label}.",
        "",
    ]

    if not commits:
        lines.append(f"_No commits found {range_label}._")
        lines.append("")
        return "\n".join(lines)

    for heading in ("Added", "Fixed", "Changed", "Removed"):
        lines.extend([f"### {heading}", ""])
        lines.extend(buckets[heading] or ["_No entries._"])
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("output", nargs="?", default="CHANGELOG.md", help="Output file path")
    args = parser.parse_args()

    if not git("rev-parse", "--is-inside-work-tree"):
        print("error: generate_changelog.py must be run inside a git repository", file=sys.stderr)
        return 1

    output_path = pathlib.Path(args.output)
    range_label, commits = collect_commits()
    output_path.write_text(render(output_path, range_label, commits), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
