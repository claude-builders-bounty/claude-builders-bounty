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


def run_git(repo: Path, args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def last_tag(repo: Path) -> str | None:
    tag = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    return tag or None


def collect_commits(repo: Path, since: str | None) -> list[Commit]:
    range_arg = f"{since}..HEAD" if since else "HEAD"
    raw = run_git(repo, ["log", range_arg, "--pretty=format:%H%x1f%s%x1f%b%x1e"], check=False)
    if not raw:
        return []

    commits: list[Commit] = []
    for record in raw.rstrip("\x1e").split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f", 2)
        if len(parts) < 2:
            continue
        sha = parts[0].strip()
        subject = parts[1].strip()
        body = parts[2].strip() if len(parts) > 2 else ""
        commits.append(Commit(sha=sha, subject=subject, body=body))
    return commits


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^\w+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return subject[:1].upper() + subject[1:] if subject else "Update project"


def categorize(commit: Commit) -> str:
    text = f"{commit.subject}\n{commit.body}".lower()
    subject = commit.subject.lower()

    if subject.startswith(("feat", "add")) or re.search(r"\b(add|adds|added|new|introduce|create)\b", text):
        return "Added"
    if subject.startswith(("fix", "bug")) or re.search(r"\b(fix|fixes|fixed|bug|repair|resolve|resolved)\b", text):
        return "Fixed"
    if subject.startswith(("remove", "delete")) or re.search(r"\b(remove|removes|removed|delete|deleted|drop|deprecate)\b", text):
        return "Removed"
    return "Changed"


def render_changelog(commits: list[Commit], since: str | None, title: str = "Unreleased") -> str:
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit)].append(commit)

    today = dt.date.today().isoformat()
    range_label = f" since `{since}`" if since else ""
    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        f"## {title} - {today}",
        "",
        f"_Generated from {len(commits)} commit(s){range_label}._",
        "",
    ]

    for category in CATEGORIES:
        lines.append(f"### {category}")
        entries = grouped[category]
        if entries:
            for commit in entries:
                lines.append(f"- {clean_subject(commit.subject)} (`{commit.sha[:7]}`)")
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Path to the git repository. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path. Defaults to CHANGELOG.md in repo.")
    parser.add_argument("--since", default=None, help="Git ref/tag to start from. Defaults to the latest tag, or all history.")
    parser.add_argument("--title", default="Unreleased", help="Release heading title.")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing a file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 2

    since = args.since if args.since is not None else last_tag(repo)
    commits = collect_commits(repo, since)
    changelog = render_changelog(commits, since, args.title)

    if args.stdout:
        print(changelog, end="")
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output} from {len(commits)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
