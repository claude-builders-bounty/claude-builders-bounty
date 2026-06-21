#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import os
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
    body: str


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def last_tag(repo: Path) -> str | None:
    result = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    tag = result.stdout.strip()
    return tag or None


def collect_commits(repo: Path, since: str | None) -> list[Commit]:
    commit_range = [f"{since}..HEAD"] if since else ["HEAD"]
    result = run_git(
        repo,
        [
            "log",
            *commit_range,
            "--reverse",
            "--format=%H%x1f%s%x1f%b%x1e",
        ],
    )
    commits: list[Commit] = []
    for raw in result.stdout.split("\x1e"):
        raw = raw.strip("\r\n")
        if not raw:
            continue
        parts = raw.split("\x1f", 2)
        if len(parts) != 3:
            continue
        commits.append(Commit(parts[0], parts[1].strip(), parts[2].strip()))
    return commits


def conventional_type(subject: str) -> str | None:
    match = re.match(r"^([a-zA-Z]+)(?:\([^)]+\))?!?:\s+", subject)
    return match.group(1).lower() if match else None


def categorize(commit: Commit) -> str:
    text = f"{commit.subject}\n{commit.body}".lower()
    ctype = conventional_type(commit.subject)

    if "breaking change" in text or (ctype and "!" in commit.subject.split(":", 1)[0]):
        return "Changed"
    if ctype in {"remove", "removed", "delete", "deleted"}:
        return "Removed"
    if ctype in {"fix", "bugfix", "hotfix"}:
        return "Fixed"
    if ctype in {"feat", "feature", "add", "added"}:
        return "Added"
    if ctype in {"refactor", "perf", "style", "test", "docs", "build", "ci", "chore"}:
        return "Changed"

    if re.search(r"\b(remove|removed|delete|deleted|deprecate|deprecated)\b", text):
        return "Removed"
    if re.search(r"\b(fix|fixed|bug|bugfix|hotfix|patch|repair|resolve|resolved)\b", text):
        return "Fixed"
    if re.search(r"\b(add|added|new|create|created|implement|implemented|introduce|introduced)\b", text):
        return "Added"
    return "Changed"


def clean_subject(subject: str) -> str:
    return re.sub(r"\s+", " ", subject).strip()


def render_changelog(commits: list[Commit], version: str, since: str | None, include_empty: bool) -> str:
    today = dt.date.today().isoformat()
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit)].append(commit)

    lines = [
        "# Changelog",
        "",
        f"## {version} - {today}",
        "",
        f"_Generated from {'commits after `' + since + '`' if since else 'all commits'}._",
        "",
    ]

    for category in CATEGORIES:
        entries = grouped[category]
        if not entries and not include_empty:
            continue
        lines.append(f"### {category}")
        if entries:
            for commit in entries:
                lines.append(f"- {clean_subject(commit.subject)} (`{commit.sha[:7]}`)")
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Git repository path. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output Markdown file. Defaults to CHANGELOG.md.")
    parser.add_argument("--version", default="Unreleased", help="Changelog version heading. Defaults to Unreleased.")
    parser.add_argument("--since", help="Git tag or revision to use instead of auto-detecting the last tag.")
    parser.add_argument(
        "--no-empty-sections",
        action="store_true",
        help="Omit categories that have no matching commits.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the generated changelog instead of writing it to disk.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 1

    since = args.since if args.since is not None else last_tag(repo)
    commits = collect_commits(repo, since)
    changelog = render_changelog(
        commits,
        version=args.version,
        since=since,
        include_empty=not args.no_empty_sections,
    )

    if args.stdout:
        print(changelog, end="")
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8", newline="\n")
    print(f"Wrote {os.path.relpath(output, repo)} with {len(commits)} commits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
