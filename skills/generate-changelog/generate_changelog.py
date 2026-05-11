#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def last_tag(repo: Path) -> str | None:
    proc = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else None


def commits_since_last_tag(repo: Path, tag: str | None) -> list[Commit]:
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    output = run_git(repo, "log", "--reverse", "--format=%H%x01%s%x01%b%x02", rev_range)
    commits: list[Commit] = []
    for record in output.split("\x02"):
        record = record.strip()
        if not record:
            continue
        sha, subject, body = (record.split("\x01", 2) + ["", ""])[:3]
        commits.append(Commit(sha=sha, subject=subject.strip(), body=body.strip()))
    return commits


def category_for(commit: Commit) -> str:
    text = f"{commit.subject}\n{commit.body}".lower()
    subject = commit.subject.lower()
    conventional_type = subject.split(":", 1)[0].split("(", 1)[0]

    if "breaking change" in text or any(word in subject for word in ("remove", "delete", "drop", "deprecate")):
        return "Removed"
    if conventional_type in {"fix", "bugfix"} or any(word in subject for word in ("fix", "bug", "repair", "patch")):
        return "Fixed"
    if conventional_type in {"feat", "feature"} or any(
        word in subject for word in ("add", "create", "implement", "introduce", "support")
    ):
        return "Added"
    return "Changed"


def grouped_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    groups = {category: [] for category in CATEGORIES}
    for commit in commits:
        groups[category_for(commit)].append(commit)
    return groups


def format_entry(commit: Commit) -> str:
    subject = commit.subject.rstrip(".")
    return f"- {subject} ({commit.sha[:7]})"


def render_changelog(repo: Path, commits: list[Commit], tag: str | None, today: dt.date | None = None) -> str:
    today = today or dt.date.today()
    source = f"commits since `{tag}`" if tag else "all commits (no git tags found)"
    lines = [
        "# Changelog",
        "",
        f"## {today.isoformat()}",
        f"_Source: {source}._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found since the last git tag.", ""])
        return "\n".join(lines)

    groups = grouped_commits(commits)
    for category in CATEGORIES:
        lines.append(f"### {category}")
        if groups[category]:
            lines.extend(format_entry(commit) for commit in groups[category])
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the last git tag.")
    parser.add_argument("--repo", default=".", help="Git repository path. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md.")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog instead of writing it.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    tag = last_tag(repo)
    commits = commits_since_last_tag(repo, tag)
    changelog = render_changelog(repo, commits, tag)

    if args.dry_run:
        print(changelog, end="")
    else:
        output = Path(args.output)
        if not output.is_absolute():
            output = repo / output
        output.write_text(changelog, encoding="utf-8")
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
