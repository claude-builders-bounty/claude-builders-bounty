#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history since the latest tag."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SECTIONS = ("Added", "Fixed", "Changed", "Removed")

CONVENTIONAL = re.compile(
    r"^(?P<kind>[a-zA-Z]+)(?:\([^)]*\))?(?:!)?:\s*(?P<text>.+)$"
)

PREFIX_TO_SECTION = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "added": "Added",
    "new": "Added",
    "create": "Added",
    "created": "Added",
    "introduce": "Added",
    "introduced": "Added",
    "fix": "Fixed",
    "fixed": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "repair": "Fixed",
    "repaired": "Fixed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
    "drop": "Removed",
    "dropped": "Removed",
}

WORD_PREFIX = re.compile(r"^[^A-Za-z0-9]*([A-Za-z]+)\b")


class GitError(RuntimeError):
    pass


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode:
        message = proc.stderr.strip() or proc.stdout.strip() or "git command failed"
        raise GitError(message)
    return proc.stdout.rstrip("\n")


def ensure_repo(repo: Path) -> None:
    git(repo, "rev-parse", "--is-inside-work-tree")


def latest_tag(repo: Path) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "describe", "--tags", "--abbrev=0"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    tag = proc.stdout.strip()
    return tag if proc.returncode == 0 and tag else None


def classify(subject: str) -> tuple[str, str]:
    match = CONVENTIONAL.match(subject.strip())
    if match:
        kind = match.group("kind").lower()
        text = match.group("text").strip()
        return PREFIX_TO_SECTION.get(kind, "Changed"), text

    word = WORD_PREFIX.match(subject.strip())
    if word:
        kind = word.group(1).lower()
        if kind in PREFIX_TO_SECTION:
            return PREFIX_TO_SECTION[kind], subject.strip()

    return "Changed", subject.strip()


def commits_since_tag(
    repo: Path, tag: str | None, max_commits: int | None = None
) -> list[tuple[str, str]]:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    args = [
        "log",
        revision,
        "--no-merges",
        "--format=%H%x09%s",
    ]
    if max_commits is not None:
        args.insert(2, f"--max-count={max_commits}")

    raw = git(repo, *args)
    commits: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        sha, sep, subject = line.partition("\t")
        if not sep:
            continue
        commits.append((sha, subject.strip()))
    return commits


def render(tag: str | None, commits: list[tuple[str, str]]) -> str:
    grouped: dict[str, list[tuple[str, str]]] = {name: [] for name in SECTIONS}
    for sha, subject in commits:
        section, clean_subject = classify(subject)
        grouped[section].append((sha, clean_subject))

    source = f"`{tag}..HEAD`" if tag else "repository history through `HEAD`"
    lines = [
        "# Changelog",
        "",
        f"_Generated from {source}; merge commits are excluded._",
        "",
    ]

    if not commits:
        lines += ["No non-merge commits were found in this range.", ""]
        return "\n".join(lines)

    for section in SECTIONS:
        lines += [f"## {section}", ""]
        items = grouped[section]
        if items:
            lines.extend(
                f"- {subject} (`{sha[:7]}`)"
                for sha, subject in items
            )
        else:
            lines.append("- _None._")
        lines.append("")

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a structured changelog from commits since the latest git tag."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Git repository to inspect (default: current directory).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Output path (default: CHANGELOG.md relative to --repo).",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=None,
        help="Optional review/sample limit. Default processes the full tag..HEAD range.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the generated changelog instead of writing a file.",
    )
    args = parser.parse_args(argv)
    if args.max_commits is not None and args.max_commits < 1:
        parser.error("--max-commits must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo.expanduser().resolve()

    try:
        ensure_repo(repo)
        tag = latest_tag(repo)
        commits = commits_since_tag(repo, tag, args.max_commits)
        content = render(tag, commits)
    except (GitError, OSError) as exc:
        print(f"changelog: {exc}", file=sys.stderr)
        return 2

    if args.stdout:
        sys.stdout.write(content)
        return 0

    output = args.output.expanduser()
    if not output.is_absolute():
        output = repo / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(
        f"Wrote {output} from "
        f"{tag + '..HEAD' if tag else 'repository history'} "
        f"({len(commits)} non-merge commit{'s' if len(commits) != 1 else ''})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
