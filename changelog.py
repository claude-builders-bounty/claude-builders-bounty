#!/usr/bin/env python3
"""Generate a Keep-a-Changelog document from git history.

The script intentionally uses only Python's standard library and git's CLI so
it can run in a repository without installing a package or exposing tokens.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("git is required but was not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout).strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}") from exc
    return result.stdout


def latest_tag() -> str | None:
    tags = run_git("tag", "--sort=-creatordate").splitlines()
    return tags[0].strip() if tags and tags[0].strip() else None


def commits_since(tag: str | None, limit: int | None) -> list[Commit]:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    raw = run_git("log", revision, "--no-merges", "--format=%H%x09%s")
    commits: list[Commit] = []
    for line in raw.splitlines():
        sha, _, subject = line.partition("\t")
        if sha and subject:
            commits.append(Commit(sha[:12], subject.strip()))
        if limit is not None and len(commits) >= limit:
            break
    return commits


def classify(subject: str) -> str:
    text = subject.lower().strip()
    conventional = re.match(r"^(?P<kind>[a-z]+)(?:\([^)]*\))?!?:\s*", text)
    kind = conventional.group("kind") if conventional else text.split()[0]

    if kind in {"feat", "feature", "add", "added", "new", "create", "implement"}:
        return "Added"
    if kind in {"fix", "fixed", "bug", "patch", "resolve", "repair", "security"}:
        return "Fixed"
    if kind in {"remove", "removed", "delete", "deleted", "drop", "deprecate"}:
        return "Removed"
    return "Changed"


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-z]+(?:\([^)]*\))?!?:\s*", "", subject, flags=re.I)
    subject = re.sub(r"\s+", " ", subject).strip()
    return subject[:200].rstrip(".") or "Unspecified change"


def render(commits: list[Commit], source_tag: str | None) -> str:
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[classify(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project are documented in this file.",
        "",
        "## [Unreleased]",
        "",
    ]
    if source_tag:
        lines.extend([f"_Since `{source_tag}`._", ""])
    else:
        lines.extend(["_Since the beginning of the repository history._", ""])

    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        entries = grouped[category]
        if entries:
            lines.extend(f"- {clean_subject(commit.subject)} ({commit.sha})" for commit in entries)
        else:
            lines.append("- No entries.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="output path (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "--from-tag",
        help="use this tag instead of the newest tag",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        help="limit the number of commits included, useful for previews",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the generated changelog without writing a file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tag = args.from_tag if args.from_tag is not None else latest_tag()
    changelog = render(commits_since(tag, args.max_commits), tag)
    if args.stdout:
        sys.stdout.write(changelog)
    else:
        args.output.write_text(changelog, encoding="utf-8")
        print(f"Generated {args.output} from {tag or 'repository history'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
