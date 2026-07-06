#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history grouped by tag or month/year."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Commit:
    short_hash: str
    date: str
    subject: str


@dataclass
class Section:
    title: str
    date: str
    commits: list[Commit]


def run_git(args: list[str], cwd: Path, *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def parse_commits(raw: str) -> list[Commit]:
    commits: list[Commit] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        commits.append(Commit(parts[0], parts[1], parts[2]))
    return commits


def get_commits(repo: Path, rev_range: str | None = None) -> list[Commit]:
    args = ["log", '--pretty=format:%h|%ad|%s', "--date=short"]
    if rev_range:
        args.append(rev_range)
    raw = run_git(args, cwd=repo, check=False)
    if not raw:
        return []
    return parse_commits(raw)


def has_tags(repo: Path) -> bool:
    return bool(run_git(["tag", "-l"], cwd=repo, check=False))


def tag_date(repo: Path, tag: str) -> str:
    return run_git(["log", "-1", "--format=%ad", "--date=short", tag], cwd=repo)


def month_year_key(date: str) -> str:
    year, month, _day = date.split("-")
    return f"{year}-{month}"


def group_by_tags(repo: Path, commits: list[Commit]) -> list[Section]:
    tags = [t for t in run_git(["tag", "-l", "--sort=version:refname"], cwd=repo).splitlines() if t]
    if not tags:
        return []

    sections: list[Section] = []
    latest_tag = tags[-1]
    after_latest = get_commits(repo, f"{latest_tag}..HEAD")
    if after_latest:
        sections.append(Section("Unreleased", after_latest[0].date, after_latest))

    for index in range(len(tags) - 1, -1, -1):
        tag = tags[index]
        rev_range = tag if index == 0 else f"{tags[index - 1]}..{tag}"
        tag_commits = get_commits(repo, rev_range)
        if tag_commits:
            sections.append(Section(tag, tag_date(repo, tag), tag_commits))

    return sections


def group_by_month_year(commits: list[Commit]) -> list[Section]:
    grouped: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        grouped[month_year_key(commit.date)].append(commit)

    sections: list[Section] = []
    for key in sorted(grouped.keys(), reverse=True):
        month_commits = grouped[key]
        sections.append(Section(key, month_commits[0].date, month_commits))
    return sections


def build_sections(repo: Path) -> list[Section]:
    commits = get_commits(repo)
    if not commits:
        return []

    if has_tags(repo):
        return group_by_tags(repo, commits)
    return group_by_month_year(commits)


def format_section_title(title: str) -> str:
    if title == "Unreleased":
        return "Unreleased"
    if title[0].isdigit():
        return title
    if not title.startswith("v"):
        return f"v{title}"
    return title


def render_changelog(sections: list[Section]) -> str:
    lines = ["# Changelog", ""]
    for section in sections:
        label = format_section_title(section.title)
        lines.append(f"## [{label}] - {section.date}")
        for commit in section.commits:
            lines.append(f"- {commit.subject}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_changelog(repo: Path, output: Path) -> str:
    content = render_changelog(build_sections(repo))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return content


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from git history grouped by tag or month/year."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="CHANGELOG.md",
        help="Path for the generated changelog (default: CHANGELOG.md)",
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Path to the git repository (default: current directory)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()

    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repository", file=sys.stderr)
        return 1

    generate_changelog(repo, output)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
