#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git commits."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import pathlib
import re
import subprocess
import sys
from collections import OrderedDict


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclasses.dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str = ""


class ChangelogError(RuntimeError):
    """Raised when changelog generation cannot continue."""


def run_git(repo: pathlib.Path, args: list[str], allow_failure: bool = False) -> str:
    try:
        process = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise ChangelogError("git is not installed or is not available on PATH") from error

    if process.returncode != 0:
        if allow_failure:
            return ""
        raise ChangelogError(process.stderr.strip() or "git command failed")

    return process.stdout.strip()


def ensure_git_repo(repo: pathlib.Path) -> None:
    result = run_git(repo, ["rev-parse", "--is-inside-work-tree"], allow_failure=True)
    if result != "true":
        raise ChangelogError(f"{repo} is not a git repository")


def latest_tag(repo: pathlib.Path) -> str | None:
    tag = run_git(repo, ["describe", "--tags", "--abbrev=0"], allow_failure=True)
    return tag or None


def commit_range(since: str | None) -> str:
    if since:
        return f"{since}..HEAD"
    return "HEAD"


def get_commits(repo: pathlib.Path, since: str | None) -> list[Commit]:
    fields = "%H%x1f%s%x1f%b%x1e"
    raw = run_git(
        repo,
        ["log", "--reverse", f"--format={fields}", commit_range(since)],
        allow_failure=True,
    )

    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue

        parts = record.split("\x1f", 2)
        if len(parts) < 2:
            continue

        sha, subject = parts[0], parts[1]
        body = parts[2] if len(parts) == 3 else ""
        commits.append(Commit(sha=sha, subject=subject.strip(), body=body.strip()))

    return commits


def strip_noise(subject: str) -> str:
    subject = re.sub(r"^\s*(?:[-*]|\[[^\]]+\])\s*", "", subject)
    subject = re.sub(r"^\s*(?:feat|fix|chore|docs|refactor|test|ci|build|perf)(?:\([^)]+\))?!?:\s*", "", subject, flags=re.I)
    subject = re.sub(r"\s+", " ", subject)
    return subject.strip().rstrip(".")


def categorize(subject: str) -> str:
    normalized = subject.lower().strip()

    if re.match(r"^(feat|feature|add|create|introduce)(\(.+\))?!?:?\s", normalized):
        return "Added"
    if re.match(r"^(fix|bug|resolve|repair|correct)(\(.+\))?!?:?\s", normalized):
        return "Fixed"
    if re.match(r"^(remove|delete|drop|deprecate)(\(.+\))?!?:?\s", normalized):
        return "Removed"

    added_words = (" add ", " adds ", " added ", " support ", " enable ", " implement ")
    fixed_words = (" fix ", " fixes ", " fixed ", " bug ", " resolve ", " resolved ")
    removed_words = (" remove ", " removes ", " removed ", " delete ", " deleted ", " drop ")
    padded = f" {normalized} "

    if any(word in padded for word in removed_words):
        return "Removed"
    if any(word in padded for word in fixed_words):
        return "Fixed"
    if any(word in padded for word in added_words):
        return "Added"

    return "Changed"


def grouped_commits(commits: list[Commit]) -> OrderedDict[str, list[Commit]]:
    grouped: OrderedDict[str, list[Commit]] = OrderedDict((name, []) for name in CATEGORIES)
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)
    return grouped


def render_changelog(
    commits: list[Commit],
    version: str,
    date: str,
    since: str | None,
    include_empty: bool,
) -> str:
    title = ["# Changelog", "", f"## {version} - {date}"]
    if since:
        title.extend(["", f"_Changes since `{since}`._"])

    sections: list[str] = []
    for category, items in grouped_commits(commits).items():
        if not items and not include_empty:
            continue

        sections.extend(["", f"### {category}"])
        if not items:
            sections.append("- No changes.")
            continue

        for commit in items:
            subject = strip_noise(commit.subject)
            sections.append(f"- {subject} ({commit.sha[:7]})")

    if not sections:
        sections = ["", "No changes found."]

    return "\n".join([*title, *sections, ""])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Path to the git repository.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output Markdown path.")
    parser.add_argument("--since", help="Git tag or revision to start from. Defaults to latest tag.")
    parser.add_argument("--version", default="Unreleased", help="Version heading to write.")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Release date.")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog without writing.")
    parser.add_argument("--include-empty", action="store_true", help="Keep empty sections.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo = pathlib.Path(args.repo).resolve()

    try:
        ensure_git_repo(repo)
        since = args.since or latest_tag(repo)
        commits = get_commits(repo, since)
        changelog = render_changelog(
            commits=commits,
            version=args.version,
            date=args.date,
            since=since,
            include_empty=args.include_empty,
        )

        if args.dry_run:
            print(changelog, end="")
            return 0

        output = pathlib.Path(args.output)
        if not output.is_absolute():
            output = repo / output
        output.write_text(changelog, encoding="utf-8")
        print(f"Wrote {output}")
        return 0
    except ChangelogError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
