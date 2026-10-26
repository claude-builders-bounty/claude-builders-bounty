#!/usr/bin/env python3
"""Generate a categorized changelog from untagged Git commits."""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORY_ORDER = ["Added", "Fixed", "Changed", "Removed"]

CONVENTIONAL_TYPES = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "refactor": "Changed",
    "perf": "Changed",
    "style": "Changed",
    "docs": "Changed",
    "test": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "revert": "Changed",
}

FIXED_PREFIXES = (
    "fix ",
    "fixes ",
    "fixed ",
    "repair ",
    "resolve ",
    "resolves ",
    "resolved ",
    "bug: ",
)

REMOVED_PREFIXES = (
    "remove ",
    "removes ",
    "removed ",
    "delete ",
    "deletes ",
    "deleted ",
    "deprecate ",
    "drop ",
    "revert ",
)

ADDED_PREFIXES = (
    "add ",
    "adds ",
    "added ",
    "create ",
    "creates ",
    "created ",
    "introduce ",
    "introduces ",
    "support ",
    "supports ",
)

CHANGED_PREFIXES = (
    "update ",
    "updates ",
    "updated ",
    "improve ",
    "improves ",
    "improved ",
    "refactor ",
    "rename ",
    "move ",
    "migrate ",
    "optimize ",
    "optimise ",
    "change ",
    "changes ",
    "changed ",
)

CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?P<scope>\([^)]*\))?(?P<breaking>!)?:\s*(?P<description>.+)$"
)


@dataclass(frozen=True)
class Commit:
    hash: str
    date: str
    subject: str


def run_git(*arguments: str, repository: str) -> str:
    process = subprocess.run(
        ["git", "-C", repository, *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or "git command failed")
    return process.stdout


def latest_reachable_tag(repository: str) -> str | None:
    process = subprocess.run(
        ["git", "-C", repository, "describe", "--tags", "--abbrev=0"],
        text=True,
        capture_output=True,
        check=False,
    )
    return process.stdout.strip() if process.returncode == 0 else None


def parse_commits(raw_output: str) -> list[Commit]:
    commits: list[Commit] = []
    for record in raw_output.split("\x1e"):
        if not record.strip():
            continue
        fields = record.strip("\n").split("\x1f")
        if len(fields) != 3:
            continue
        commits.append(Commit(fields[0], fields[1], fields[2]))
    return commits


def get_commits(repository: str, tag: str | None) -> list[Commit]:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    raw_output = run_git(
        "log",
        "--no-merges",
        "--date=short",
        "--pretty=%H%x1f%ad%x1f%s%x1e",
        revision,
        repository=repository,
    )
    return parse_commits(raw_output)


def categorize(subject: str) -> str:
    match = CONVENTIONAL_PATTERN.match(subject)
    if match:
        commit_type = match.group("type").lower()
        description = match.group("description")
        if commit_type in {"remove", "delete", "deprecate"}:
            return "Removed"
        if commit_type in CONVENTIONAL_TYPES:
            return CONVENTIONAL_TYPES[commit_type]
        subject = description

    normalized_subject = subject.strip().lower()
    if normalized_subject.startswith(REMOVED_PREFIXES):
        return "Removed"
    if normalized_subject.startswith(FIXED_PREFIXES):
        return "Fixed"
    if normalized_subject.startswith(ADDED_PREFIXES):
        return "Added"
    if normalized_subject.startswith(CHANGED_PREFIXES):
        return "Changed"
    return "Changed"


def group_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    grouped: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)
    return grouped


def render_changelog(
    commits: list[Commit],
    tag: str | None,
    generated_date: date,
) -> str:
    title = tag if tag else "Unreleased"
    lines = [f"## {title} - {generated_date.isoformat()}"]

    if not commits:
        lines.append("")
        lines.append("No untagged commits found.")
        return "\n".join(lines) + "\n"

    grouped = group_commits(commits)
    for category in CATEGORY_ORDER:
        category_commits = grouped.get(category, [])
        if not category_commits:
            continue
        lines.append("")
        lines.append(f"### {category}")
        for commit in category_commits:
            lines.append(f"- {commit.subject} (`{commit.hash[:12]}`)")

    return "\n".join(lines) + "\n"


def generate_changelog(
    repository: str,
    generated_date: date | None = None,
    tag: str | None = None,
) -> str:
    latest_tag = tag or latest_reachable_tag(repository)
    commits = get_commits(repository, latest_tag)
    return render_changelog(commits, latest_tag, generated_date or date.today())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=".", help="Git repository to inspect")
    parser.add_argument("--tag", help="Use this tag instead of the latest reachable tag")
    parser.add_argument("--output", help="Write to a file instead of stdout")
    arguments = parser.parse_args()

    try:
        changelog = generate_changelog(arguments.repository, tag=arguments.tag)
    except (OSError, RuntimeError) as error:
        parser.error(str(error))

    if arguments.output:
        Path(arguments.output).write_text(changelog, encoding="utf-8")
    else:
        print(changelog, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
