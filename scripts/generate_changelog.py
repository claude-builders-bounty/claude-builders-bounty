#!/usr/bin/env python3
"""Generate a Keep a Changelog-style CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: list[str], repo: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def last_tag(repo: Path) -> str | None:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"], repo)
    except SystemExit:
        return None
    return tag or None


def commits_since(ref: str | None, repo: Path) -> list[Commit]:
    revision = f"{ref}..HEAD" if ref else "HEAD"
    output = run_git(["log", "--no-merges", "--pretty=format:%h%x1f%s", revision], repo)
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\x1f")
        commits.append(Commit(sha=sha.strip(), subject=subject.strip()))
    return commits


def categorize(subject: str) -> str:
    lowered = subject.lower()
    conventional = re.match(r"^(?P<type>[a-z]+)(?:\([^)]+\))?!?:", lowered)
    commit_type = conventional.group("type") if conventional else ""

    if commit_type in {"feat", "feature", "add"} or lowered.startswith(("add ", "create ", "implement ")):
        return "Added"
    if commit_type in {"fix", "bugfix", "hotfix"} or lowered.startswith(("fix ", "repair ", "resolve ")):
        return "Fixed"
    if commit_type in {"remove", "delete", "drop", "deprecate"} or lowered.startswith(("remove ", "delete ", "drop ")):
        return "Removed"
    return "Changed"


def clean_subject(subject: str) -> str:
    cleaned = re.sub(r"^[a-z]+(?:\([^)]+\))?!?:\s*", "", subject, flags=re.IGNORECASE).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else subject


def grouped_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)
    return grouped


def render_changelog(commits: list[Commit], ref: str | None) -> str:
    today = dt.date.today().isoformat()
    source = f"since `{ref}`" if ref else "from all available git history"
    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git commit history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"_Generated {source}._",
        "",
    ]

    if not commits:
        lines.extend(["No changes found.", ""])
        return "\n".join(lines)

    grouped = grouped_commits(commits)
    for category in CATEGORIES:
        entries = grouped[category]
        if not entries:
            continue
        lines.extend([f"### {category}", ""])
        for commit in entries:
            lines.append(f"- {clean_subject(commit.subject)} ({commit.sha})")
        lines.append("")

    return "\n".join(lines)


def write_changelog(content: str, output: Path, dry_run: bool) -> None:
    if dry_run:
        print(content)
        return
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository path to inspect")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    parser.add_argument("--since", help="Git ref or tag to use instead of the latest tag")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog instead of writing")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    ref = args.since if args.since is not None else last_tag(repo)
    commits = commits_since(ref, repo)
    changelog = render_changelog(commits, ref)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    write_changelog(changelog, output, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
