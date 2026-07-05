#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

The script has no third-party dependencies. It reads commits since the last
git tag by default, groups them into common changelog sections, and writes a
Keep a Changelog-style Markdown file.
"""

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
SECTION_HINTS = {
    "Added": (
        "add",
        "added",
        "create",
        "created",
        "feature",
        "feat",
        "implement",
        "introduce",
        "new",
    ),
    "Fixed": (
        "bug",
        "fix",
        "fixed",
        "hotfix",
        "patch",
        "repair",
        "resolve",
        "resolved",
    ),
    "Removed": (
        "delete",
        "deleted",
        "deprecate",
        "drop",
        "remove",
        "removed",
    ),
}


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str = ""


def run_git(repo: Path, *args: str, check: bool = True) -> str:
    """Run a git command and return stdout."""
    command = ["git", "-C", str(repo), *args]
    try:
        result = subprocess.run(
            command,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git is required but was not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "git command failed"
        raise RuntimeError(detail) from exc
    return result.stdout.strip()


def discover_last_tag(repo: Path) -> str | None:
    output = run_git(repo, "describe", "--tags", "--abbrev=0", check=False)
    return output or None


def parse_commit_stream(raw: str) -> list[Commit]:
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        fields = record.split("\x1f")
        sha = fields[0].strip()
        subject = fields[1].strip() if len(fields) > 1 else ""
        body = fields[2].strip() if len(fields) > 2 else ""
        if sha and subject:
            commits.append(Commit(sha=sha, subject=subject, body=body))
    return commits


def collect_commits(repo: Path, since: str | None) -> list[Commit]:
    revision = f"{since}..HEAD" if since else "HEAD"
    raw = run_git(repo, "log", revision, "--format=%H%x1f%s%x1f%b%x1e")
    return parse_commit_stream(raw)


def normalize_subject(subject: str) -> str:
    cleaned = re.sub(r"^\w+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else subject


def classify_commit(commit: Commit) -> str:
    subject = commit.subject.lower()
    conventional_type = subject.split(":", 1)[0].split("(", 1)[0].strip()
    if conventional_type == "feat":
        return "Added"
    if conventional_type == "fix":
        return "Fixed"
    if conventional_type in {"remove", "removed"}:
        return "Removed"

    words = set(re.findall(r"[a-z]+", subject))
    for category, hints in SECTION_HINTS.items():
        if words.intersection(hints):
            return category
    return "Changed"


def group_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[classify_commit(commit)].append(commit)
    return grouped


def render_changelog(
    grouped: dict[str, list[Commit]],
    *,
    version: str,
    since: str | None,
    today: dt.date,
) -> str:
    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        f"## {version} - {today.isoformat()}",
        "",
    ]
    if since:
        lines.extend([f"_Changes since `{since}`._", ""])

    emitted = False
    for category in CATEGORIES:
        commits = grouped[category]
        if not commits:
            continue
        emitted = True
        lines.extend([f"### {category}", ""])
        for commit in commits:
            lines.append(f"- {normalize_subject(commit.subject)} ({commit.sha[:7]})")
        lines.append("")

    if not emitted:
        lines.extend(["No commits found for the selected range.", ""])
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git history."
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Repository path to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Markdown file to write. Defaults to CHANGELOG.md.",
    )
    parser.add_argument(
        "--since",
        help="Git ref to use as the start of the range. Defaults to the last tag.",
    )
    parser.add_argument(
        "--version",
        default="Unreleased",
        help="Heading version to use in the changelog.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated changelog instead of writing it.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists():
        print(f"Repository path does not exist: {repo}", file=sys.stderr)
        return 2

    try:
        since = args.since or discover_last_tag(repo)
        commits = collect_commits(repo, since)
        changelog = render_changelog(
            group_commits(commits),
            version=args.version,
            since=since,
            today=dt.date.today(),
        )
    except RuntimeError as exc:
        print(f"Unable to generate changelog: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(changelog, end="")
        return 0

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(changelog, encoding="utf-8")
    print(f"Wrote {os.path.relpath(output_path, repo)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
