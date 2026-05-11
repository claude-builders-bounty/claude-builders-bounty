#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import re
import subprocess
import sys


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message)
    return result.stdout.strip()


def _repo_root(path: Path) -> Path:
    root = _git(path, "rev-parse", "--show-toplevel")
    return Path(root)


def _latest_tag(repo: Path) -> str | None:
    tag = _git(repo, "describe", "--tags", "--abbrev=0", check=False)
    return tag or None


def _commit_range(repo: Path, since: str | None) -> tuple[str, str]:
    if since:
        return f"{since}..HEAD", f"changes since `{since}`"

    first_commit = _git(repo, "rev-list", "--max-parents=0", "HEAD").splitlines()[0]
    short = first_commit[:7]
    return "HEAD", f"all commits, no git tag found (from `{short}`)"


def _read_commits(repo: Path, revision_range: str) -> list[dict[str, str]]:
    raw = _git(
        repo,
        "log",
        revision_range,
        "--reverse",
        "--date=short",
        "--pretty=format:%H%x1f%s%x1f%an%x1f%ad%x1e",
    )
    commits: list[dict[str, str]] = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue

        parts = record.split("\x1f")
        if len(parts) != 4:
            continue

        sha, subject, author, date = parts
        commits.append(
            {
                "sha": sha,
                "short_sha": sha[:7],
                "subject": subject.strip(),
                "author": author.strip(),
                "date": date.strip(),
            }
        )
    return commits


def _clean_subject(subject: str) -> str:
    subject = re.sub(r"^\w+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    subject = re.sub(r"\s+\(#\d+\)$", "", subject).strip()
    if not subject:
        return "Update project"
    return subject[0].upper() + subject[1:]


def _category(subject: str) -> str:
    normalized = subject.strip().lower()
    conventional = re.match(r"^(\w+)(?:\([^)]+\))?!?:", normalized)
    commit_type = conventional.group(1) if conventional else ""

    if "breaking change" in normalized or re.search(r"^\w+(?:\([^)]+\))!:", normalized):
        return "Changed"

    if commit_type in {"feat", "feature", "add"} or normalized.startswith(("add ", "added ", "new ")):
        return "Added"

    if commit_type in {"fix", "bugfix", "hotfix"} or normalized.startswith(("fix ", "fixed ", "repair ")):
        return "Fixed"

    if commit_type in {"remove", "removed", "delete", "deleted"} or normalized.startswith(
        ("remove ", "removed ", "delete ", "deleted ", "drop ")
    ):
        return "Removed"

    return "Changed"


def _render_changelog(repo: Path, commits: list[dict[str, str]], range_note: str) -> str:
    today = dt.date.today().isoformat()
    repo_name = repo.name

    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        category = _category(commit["subject"])
        subject = _clean_subject(commit["subject"])
        grouped[category].append(f"- {subject} ({commit['short_sha']})")

    lines = [
        "# Changelog",
        "",
        "All notable changes to this project are documented in this file.",
        "",
        f"## Unreleased - {today}",
        "",
        f"_Generated for `{repo_name}` from {range_note}._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        entries = grouped[category]
        if entries:
            lines.extend(entries)
        else:
            lines.append("- No notable changes.")
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest git tag.")
    parser.add_argument("--repo", default=".", help="Path to the git repository. Defaults to the current directory.")
    parser.add_argument("--since", help="Optional tag or revision to use instead of the latest git tag.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md.")
    parser.add_argument("--stdout", action="store_true", help="Print the changelog instead of writing a file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        repo = _repo_root(Path(args.repo).resolve())
        since = args.since or _latest_tag(repo)
        revision_range, range_note = _commit_range(repo, since)
        commits = _read_commits(repo, revision_range)
        changelog = _render_changelog(repo, commits, range_note)
    except Exception as exc:
        print(f"Failed to generate changelog: {exc}", file=sys.stderr)
        return 1

    if args.stdout:
        print(changelog)
        return 0

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo / output_path
    output_path.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
