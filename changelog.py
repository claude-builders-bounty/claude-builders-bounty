#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from the Git history."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


SECTIONS = ("Added", "Fixed", "Changed", "Removed")

CONVENTIONAL_TYPES = {
    "add": "Added",
    "build": "Changed",
    "chore": "Changed",
    "ci": "Changed",
    "change": "Changed",
    "docs": "Changed",
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "hotfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "remove": "Removed",
    "revert": "Changed",
    "test": "Changed",
}

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<description>.+)$",
    re.IGNORECASE,
)

KEYWORD_RULES = (
    ("Removed", re.compile(r"\b(remove|removed|removes|delete|deleted|drop|dropped|deprecat(?:e|ed|ion))\b", re.I)),
    ("Fixed", re.compile(r"\b(fix|fixed|fixes|bug|bugs|hotfix|patch|patched|repair|resolved?|resolve)\b", re.I)),
    ("Added", re.compile(r"\b(add|added|adds|feature|feat|new|introduc(?:e|ed)|implement(?:ed|s)?|creat(?:e|ed|es)|support(?:ed|s)?)\b", re.I)),
    ("Changed", re.compile(r"\b(change|changed|changes|update|updated|updates|refactor|improv(?:e|ed|es)|document(?:ed|ation)?|docs|chore|perf|test|build|ci)\b", re.I)),
)


class ChangelogError(RuntimeError):
    """An actionable error while reading the repository history."""


def run_git(repo: Path, *arguments: str, allow_failure: bool = False) -> str:
    """Run Git in *repo* and return stdout, with a useful error on failure."""

    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode and not allow_failure:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise ChangelogError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout.strip()


def latest_tag(repo: Path) -> Optional[str]:
    """Return the most recent reachable tag, if the repository has one."""

    tag = run_git(repo, "describe", "--tags", "--abbrev=0", allow_failure=True)
    return tag or None


def commit_records(repo: Path, tag: Optional[str]) -> list[dict[str, str]]:
    """Read commits after *tag* (or all commits when no tag exists)."""

    revision = f"{tag}..HEAD" if tag else "HEAD"
    # Record and field separators are control characters, so commit subjects
    # can safely contain spaces and punctuation without fragile shell parsing.
    raw = run_git(
        repo,
        "log",
        "--no-merges",
        "--date=short",
        "--format=%H%x1f%ad%x1f%s%x1e",
        revision,
    )
    records: list[dict[str, str]] = []
    for record in raw.split("\x1e"):
        fields = record.strip("\r\n\x00").split("\x1f")
        if len(fields) != 3 or not fields[0]:
            continue
        records.append({"sha": fields[0], "date": fields[1], "subject": fields[2].strip()})
    return records


def categorize(subject: str) -> str:
    """Map a commit subject to one of the four changelog sections."""

    match = CONVENTIONAL_RE.match(subject)
    if match:
        section = CONVENTIONAL_TYPES.get(match.group("type").lower())
        if section:
            return section

    for section, pattern in KEYWORD_RULES:
        if pattern.search(subject):
            return section
    return "Changed"


def format_changelog(
    records: list[dict[str, str]],
    tag: Optional[str],
    version: Optional[str] = None,
    generated_on: Optional[dt.date] = None,
) -> str:
    """Render records as a predictable Markdown changelog."""

    generated_on = generated_on or dt.date.today()
    grouped: dict[str, list[dict[str, str]]] = {section: [] for section in SECTIONS}
    for record in records:
        grouped[categorize(record["subject"])].append(record)

    label = version or "Unreleased"
    lines = ["# Changelog", "", f"## [{label}] - {generated_on.isoformat()}", ""]
    if tag:
        lines.extend([f"Changes since `{tag}`.", ""])
    else:
        lines.extend(["Changes from the repository history.", ""])

    for section in SECTIONS:
        lines.extend([f"### {section}", ""])
        entries = grouped[section]
        if entries:
            for record in entries:
                lines.append(f"- {record['subject']} ([{record['sha'][:7]}])")
        else:
            lines.append("- _No changes in this category._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_atomic(path: Path, content: str) -> None:
    """Write the output without leaving a partially-written changelog."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as temporary:
            temporary.write(content)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from commits since the latest Git tag."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("."),
        help="Repository to inspect (default: current directory).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Markdown file to write (default: CHANGELOG.md).",
    )
    parser.add_argument(
        "--tag",
        help="Use this tag as the starting point instead of the latest reachable tag.",
    )
    parser.add_argument(
        "--version",
        help="Heading label for this release (default: Unreleased).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a Git repository", file=sys.stderr)
        return 2

    try:
        tag = args.tag or latest_tag(repo)
        records = commit_records(repo, tag)
        content = format_changelog(records, tag, args.version)
        write_atomic(args.output.resolve(), content)
    except ChangelogError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Generated {args.output.resolve()} from {len(records)} commit(s).")
    if tag:
        print(f"Starting point: {tag}")
    else:
        print("Starting point: repository history (no reachable tag found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
