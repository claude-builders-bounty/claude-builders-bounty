#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import subprocess
import sys


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def run_git(args: list[str], cwd: pathlib.Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def repo_root() -> pathlib.Path:
    try:
        result = run_git(["rev-parse", "--show-toplevel"])
    except subprocess.CalledProcessError as exc:
        raise SystemExit("generate_changelog.py must be run inside a git repository.") from exc

    return pathlib.Path(result.stdout.strip())


def latest_tag(root: pathlib.Path) -> str | None:
    result = run_git(["describe", "--tags", "--abbrev=0"], cwd=root, check=False)
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def commit_rows(root: pathlib.Path, tag: str | None) -> list[tuple[str, str, str]]:
    range_args = [f"{tag}..HEAD"] if tag else []
    result = run_git(
        ["log", "--no-merges", "--date=short", "--pretty=format:%h%x09%ad%x09%s", *range_args],
        cwd=root,
    )
    rows = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        short_hash, commit_date, subject = line.split("\t", 2)
        rows.append((short_hash, commit_date, subject))
    return rows


def categorize(subject: str) -> str:
    normalized = subject.lower()
    added_words = ("feat", "add", "added", "create", "implement", "introduce")
    fixed_words = ("fix", "fixed", "bugfix", "repair", "resolve", "correct", "patch")
    removed_words = ("remove", "removed", "delete", "drop", "dropped", "deprecate")

    def matches(words: tuple[str, ...]) -> bool:
        return any(re.match(rf"^{word}(\([^)]+\))?[: ]", normalized) for word in words)

    if matches(added_words):
        return "Added"
    if matches(fixed_words):
        return "Fixed"
    if matches(removed_words):
        return "Removed"
    return "Changed"


def render_changelog(rows: list[tuple[str, str, str]], tag: str | None) -> str:
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    for short_hash, commit_date, subject in rows:
        grouped[categorize(subject)].append(f"- {subject} ({short_hash}, {commit_date})")

    generated_date = dt.date.today().isoformat()
    scope = f"commits since `{tag}`" if tag else "the entire git history"
    lines = [
        "# Changelog",
        "",
        f"## Unreleased - {generated_date}",
        "",
        f"Generated from {scope}.",
        "",
    ]

    if not rows:
        lines.append("No commits found for this release window.")
        lines.append("")
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.append("")
        lines.extend(grouped[category] or ["- No changes."])
        lines.append("")

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    parser.add_argument(
        "output",
        nargs="?",
        default="CHANGELOG.md",
        help="Output file path. Defaults to CHANGELOG.md in the repository root.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = repo_root()
    tag = latest_tag(root)
    rows = commit_rows(root, tag)
    output = pathlib.Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_changelog(rows, tag), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
