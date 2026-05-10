#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass
class Commit:
    full_hash: str
    short_hash: str
    subject: str


def run_git(repo: Path, args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def ensure_git_repo(repo: Path) -> None:
    run_git(repo, ["rev-parse", "--is-inside-work-tree"])


def last_tag(repo: Path) -> str | None:
    tag = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    return tag or None


def clean_subject(subject: str) -> str:
    cleaned = subject.strip()
    if ":" in cleaned:
        prefix, rest = cleaned.split(":", 1)
        if len(prefix) <= 32 and all(char.isalnum() or char in "()-_! " for char in prefix):
            cleaned = rest.strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else subject


def categorize(subject: str) -> str:
    lower = subject.lower()
    prefix = lower.split(":", 1)[0].strip() if ":" in lower else ""

    if prefix.startswith("feat") or lower.startswith(("add ", "adds ", "added ", "create ", "implement ")):
        return "Added"
    if prefix.startswith("fix") or any(word in lower for word in ("bug", "crash", "broken", "regression", "repair")):
        return "Fixed"
    if any(word in lower for word in ("remove", "delete", "drop", "deprecate")):
        return "Removed"
    return "Changed"


def collect_commits(repo: Path, since: str | None) -> list[Commit]:
    range_arg = f"{since}..HEAD" if since else "HEAD"
    raw = run_git(
        repo,
        [
            "log",
            "--reverse",
            "--pretty=format:%H%x1f%h%x1f%s%x1e",
            range_arg,
        ],
        check=False,
    )
    commits: list[Commit] = []
    for entry in raw.split("\x1e"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("\x1f")
        if len(parts) != 3:
            continue
        commits.append(Commit(full_hash=parts[0], short_hash=parts[1], subject=parts[2]))
    return commits


def render_changelog(commits: list[Commit], since: str | None, include_hashes: bool) -> str:
    today = dt.date.today().isoformat()
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        f"## Unreleased - {today}",
        "",
    ]
    if since:
        lines.extend(
            [
                f"Generated from commits since `{since}`.",
                f"Compare range: `{since}..HEAD`.",
                "",
            ]
        )
    else:
        lines.extend(["Generated from all commits because no git tag was found.", ""])

    for category in CATEGORIES:
        lines.append(f"### {category}")
        if grouped[category]:
            for commit in grouped[category]:
                item = clean_subject(commit.subject)
                suffix = f" ({commit.short_hash})" if include_hashes else ""
                lines.append(f"- {item}{suffix}")
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Path to the git repository. Defaults to current directory.")
    parser.add_argument("--since", help="Git ref/tag to start from. Defaults to the latest tag.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md.")
    parser.add_argument("--dry-run", action="store_true", help="Print the changelog instead of writing a file.")
    parser.add_argument("--no-hashes", action="store_true", help="Do not include short commit hashes in bullet items.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).expanduser().resolve()
    output = Path(args.output)

    try:
        ensure_git_repo(repo)
        since = args.since if args.since is not None else last_tag(repo)
        commits = collect_commits(repo, since)
        changelog = render_changelog(commits, since, include_hashes=not args.no_hashes)
    except RuntimeError as error:
        print(f"changelog: {error}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(changelog, end="")
        return 0

    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
