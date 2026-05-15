#!/usr/bin/env python3
"""Generate a CHANGELOG.md section from git commits.

The script reads commits since the latest tag by default, classifies commit
subjects into common changelog sections, and writes a Keep-a-Changelog-style
release block to CHANGELOG.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass


SECTION_ORDER = ("Added", "Fixed", "Changed", "Removed")
SECTION_KEYWORDS = {
    "Added": ("add", "added", "feat", "feature", "create", "introduce", "implement", "new"),
    "Fixed": ("fix", "fixed", "bugfix", "bug", "repair", "resolve", "patch"),
    "Changed": ("change", "changed", "update", "updated", "refactor", "improve", "enhance", "docs", "doc", "test", "ci", "build", "chore"),
    "Removed": ("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecate"),
}


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def latest_tag() -> str | None:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"])
    except RuntimeError:
        return None
    return tag or None


def current_version(from_ref: str | None) -> str:
    if from_ref:
        return f"Unreleased since {from_ref}"
    return "Unreleased"


def commit_range(from_ref: str | None) -> list[str]:
    if from_ref:
        return [f"{from_ref}..HEAD"]
    return ["HEAD"]


def get_commits(from_ref: str | None) -> list[Commit]:
    fmt = "%h%x00%s"
    output = run_git(["log", "--no-merges", f"--pretty=format:{fmt}", *commit_range(from_ref)])
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\0")
        if subject:
            commits.append(Commit(sha=sha, subject=subject.strip()))
    return commits


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^\w+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    if not subject:
        return "Update project"
    return subject[0].upper() + subject[1:]


def classify(subject: str) -> str:
    normalized = subject.lower().strip()
    type_match = re.match(r"^(\w+)(?:\([^)]+\))?!?:", normalized)
    first_word = type_match.group(1) if type_match else re.split(r"[\s:-]+", normalized, maxsplit=1)[0]

    for section, keywords in SECTION_KEYWORDS.items():
        if first_word in keywords:
            return section
    return "Changed"


def group_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    groups = {section: [] for section in SECTION_ORDER}
    for commit in commits:
        groups[classify(commit.subject)].append(commit)
    return groups


def render_block(commits: list[Commit], version: str) -> str:
    today = dt.date.today().isoformat()
    lines = [f"## {version} - {today}", ""]
    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    groups = group_commits(commits)
    for section in SECTION_ORDER:
        section_commits = groups[section]
        if not section_commits:
            continue
        lines.extend([f"### {section}", ""])
        for commit in section_commits:
            lines.append(f"- {clean_subject(commit.subject)} ({commit.sha})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def merge_with_existing(output_path: pathlib.Path, block: str) -> str:
    title = "# Changelog\n\n"
    if not output_path.exists():
        return title + block

    existing = output_path.read_text(encoding="utf-8")
    if existing.startswith("# Changelog"):
        rest = existing.split("\n", 1)[1].lstrip()
        return title + block + "\n" + rest
    return title + block + "\n" + existing.lstrip()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits.")
    parser.add_argument("--from", dest="from_ref", help="Start ref/tag. Defaults to latest git tag.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output changelog path.")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog block without writing a file.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    from_ref = args.from_ref or latest_tag()
    try:
        commits = get_commits(from_ref)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    block = render_block(commits, current_version(from_ref))
    if args.dry_run:
        print(block, end="")
        return 0

    output_path = pathlib.Path(args.output)
    output_path.write_text(merge_with_existing(output_path, block), encoding="utf-8")
    print(f"Wrote {output_path} with {len(commits)} commits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
