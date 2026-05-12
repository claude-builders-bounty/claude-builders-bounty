#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SECTIONS = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    author: str
    date: str


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def resolve_repo(path: str) -> Path:
    repo = Path(path).expanduser().resolve()
    result = run_git(repo, ["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip())


def latest_tag(repo: Path) -> str | None:
    result = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def collect_commits(repo: Path, tag: str | None) -> list[Commit]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    pretty = "%H%x1f%s%x1f%an%x1f%ad%x1e"
    result = run_git(repo, ["log", "--date=short", f"--pretty=format:{pretty}", revision_range])
    commits: list[Commit] = []
    for record in result.stdout.strip("\x1e\n").split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip().split("\x1f")
        if len(parts) != 4:
            continue
        commits.append(Commit(*parts))
    return commits


def category_for(subject: str) -> str:
    lowered = subject.lower()
    prefix = lowered.split(":", 1)[0].split("(", 1)[0].strip()

    if prefix in {"feat", "feature", "add"}:
        return "Added"
    if prefix in {"fix", "bugfix", "hotfix"}:
        return "Fixed"
    if prefix in {"remove", "removed", "delete", "deleted"}:
        return "Removed"
    if prefix in {"refactor", "perf", "docs", "doc", "style", "test", "tests", "build", "ci", "chore"}:
        return "Changed"

    removed_words = ("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecate")
    fixed_words = ("fix", "fixed", "bug", "crash", "regression", "repair", "resolve")
    added_words = ("add", "added", "introduce", "create", "new", "support")

    if any(word in lowered for word in removed_words):
        return "Removed"
    if any(word in lowered for word in fixed_words):
        return "Fixed"
    if any(word in lowered for word in added_words):
        return "Added"
    return "Changed"


def commit_url(repo: Path, sha: str) -> str | None:
    result = run_git(repo, ["remote", "get-url", "origin"], check=False)
    if result.returncode != 0:
        return None
    remote = result.stdout.strip()
    if remote.endswith(".git"):
        remote = remote[:-4]
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.removeprefix("git@github.com:")
    if remote.startswith("https://github.com/"):
        return f"{remote}/commit/{sha}"
    return None


def format_changelog(repo: Path, commits: list[Commit], tag: str | None) -> str:
    today = dt.date.today().isoformat()
    grouped: dict[str, list[Commit]] = {section: [] for section in SECTIONS}
    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)

    if tag:
        source = f"Commits since `{tag}`."
    else:
        source = "All commits in this repository because no git tag was found."

    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git history.",
        "",
        f"## Unreleased - {today}",
        "",
        source,
        "",
    ]

    base_commit_url = commit_url(repo, "")
    for section in SECTIONS:
        lines.append(f"### {section}")
        if grouped[section]:
            for commit in grouped[section]:
                short_sha = commit.sha[:7]
                if base_commit_url:
                    link = f"[`{short_sha}`]({base_commit_url}{commit.sha})"
                else:
                    link = f"`{short_sha}`"
                lines.append(f"- {commit.subject} ({link}, {commit.date})")
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest git tag.")
    parser.add_argument("-r", "--repo", default=".", help="Git repository path. Defaults to current directory.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output markdown path. Defaults to CHANGELOG.md.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        repo = resolve_repo(args.repo)
        tag = latest_tag(repo)
        commits = collect_commits(repo, tag)
        changelog = format_changelog(repo, commits, tag)
        if args.stdout:
            sys.stdout.write(changelog)
            return 0

        output = Path(args.output)
        if not output.is_absolute():
            output = Path(os.getcwd()) / output
        output.write_text(changelog, encoding="utf-8")
        print(f"Wrote {output}")
        return 0
    except subprocess.CalledProcessError as error:
        sys.stderr.write(error.stderr or str(error))
        return error.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
