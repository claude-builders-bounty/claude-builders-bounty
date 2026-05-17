#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")
PREFIX_TO_CATEGORY = {
    "add": "Added",
    "added": "Added",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "create": "Added",
    "delete": "Removed",
    "docs": "Changed",
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "improve": "Changed",
    "perf": "Changed",
    "refactor": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "resolve": "Fixed",
    "style": "Changed",
    "test": "Changed",
    "update": "Changed",
    "upgrade": "Changed",
}


@dataclass(frozen=True)
class CommitEntry:
    sha: str
    category: str
    summary: str
    fallback_used: bool


def run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def resolve_base_ref(repo: Path) -> tuple[str, str]:
    try:
        ref = run_git(repo, "describe", "--tags", "--abbrev=0")
        return ref, ref
    except subprocess.CalledProcessError:
        root = run_git(repo, "rev-list", "--max-parents=0", "HEAD").splitlines()[0]
        return root, f"initial commit ({root[:7]})"


def load_commits(repo: Path, base_ref: str) -> list[tuple[str, str]]:
    head = run_git(repo, "rev-parse", "HEAD")
    if base_ref == head:
        return []

    raw = run_git(
        repo,
        "log",
        "--reverse",
        "--format=%H%x1f%s%x1e",
        f"{base_ref}..HEAD",
    )
    commits: list[tuple[str, str]] = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        sha, subject = record.split("\x1f", 1)
        commits.append((sha.strip(), subject.strip()))
    return commits


def classify_commit(subject: str) -> tuple[str, str, bool]:
    cleaned = subject.strip()
    match = re.match(r"^(?P<prefix>[A-Za-z]+)(?:\([^)]+\))?:\s*(?P<summary>.+)$", cleaned)
    fallback_used = False
    if match:
        prefix = match.group("prefix").lower()
        summary = match.group("summary").strip()
    else:
        prefix = cleaned.split(":", 1)[0].split()[0].lower()
        summary = cleaned

    category = PREFIX_TO_CATEGORY.get(prefix, "Changed")
    fallback_used = prefix not in PREFIX_TO_CATEGORY
    if category in {"Added", "Fixed", "Removed"}:
        return category, summary, fallback_used
    return "Changed", summary, fallback_used


def build_entries(commits: Iterable[tuple[str, str]]) -> list[CommitEntry]:
    entries: list[CommitEntry] = []
    for sha, subject in commits:
        category, summary, fallback_used = classify_commit(subject)
        entries.append(
            CommitEntry(
                sha=sha,
                category=category,
                summary=summary,
                fallback_used=fallback_used,
            )
        )
    return entries


def render_changelog(
    repo: Path,
    entries: list[CommitEntry],
    base_label: str,
    base_ref: str,
    head_ref: str,
    generated_on: date,
    show_uncategorized_note: bool,
) -> str:
    del repo
    grouped: dict[str, list[str]] = OrderedDict((category, []) for category in CATEGORY_ORDER)
    for entry in entries:
        grouped[entry.category].append(entry.summary)

    lines = [
        "# CHANGELOG",
        "",
        f"Generated on {generated_on.isoformat()}",
        f"Range: `{base_label}` -> `{head_ref[:7]}`",
        "",
    ]

    if show_uncategorized_note:
        lines.append("> Commits that do not match a conventional prefix are grouped under Changed.")
        lines.append("")

    for category in CATEGORY_ORDER:
        items = grouped[category]
        if not items:
            continue
        lines.append(f"## {category}")
        lines.extend(f"- {item}" for item in items)
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()
    if not entries:
        lines.extend(["No commits were found in the selected range.", ""])
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root to inspect.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Path to write the generated changelog.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the changelog to stdout as well as writing the output file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo.resolve()
    base_ref, base_label = resolve_base_ref(repo)
    commits = load_commits(repo, base_ref)
    entries = build_entries(commits)
    head_ref = run_git(repo, "rev-parse", "HEAD")
    changelog = render_changelog(
        repo=repo,
        entries=entries,
        base_label=base_label,
        base_ref=base_ref,
        head_ref=head_ref,
        generated_on=date.today(),
        show_uncategorized_note=any(entry.fallback_used for entry in entries),
    )

    write_output = args.output != Path("-")
    if write_output:
        output_path = args.output if args.output.is_absolute() else repo / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(changelog, encoding="utf-8")

    if args.stdout or not write_output:
        sys.stdout.write(changelog)
    else:
        sys.stdout.write(f"Wrote {output_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
