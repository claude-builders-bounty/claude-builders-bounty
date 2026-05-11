#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")

CONVENTIONAL_TYPES = {
    "feat": "Added",
    "feature": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "perf": "Changed",
    "refactor": "Changed",
    "docs": "Changed",
    "doc": "Changed",
    "style": "Changed",
    "test": "Changed",
    "tests": "Changed",
    "chore": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "revert": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deleted": "Removed",
}

KEYWORD_PREFIXES = (
    ("Added", ("add", "adds", "added", "create", "creates", "created", "implement", "implements", "implemented", "introduce", "introduces", "introduced")),
    ("Fixed", ("fix", "fixes", "fixed", "repair", "repairs", "repaired", "patch", "patched", "resolve", "resolves", "resolved")),
    ("Removed", ("remove", "removes", "removed", "delete", "deletes", "deleted", "drop", "drops", "dropped", "deprecate", "deprecates", "deprecated")),
    ("Changed", ("change", "changes", "changed", "update", "updates", "updated", "refactor", "refactors", "refactored", "improve", "improves", "improved")),
)

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\([^)]+\))?(?P<breaking>!)?:\s*(?P<description>.+)$"
)


@dataclass(frozen=True)
class Commit:
    subject: str
    sha: str
    author: str
    date: str


def run_git(repo: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(message)
    return result


def normalize_repo(path: Path) -> Path:
    repo = path.expanduser().resolve()
    result = run_git(repo, ["rev-parse", "--is-inside-work-tree"], check=False)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise RuntimeError(f"{repo} is not inside a git work tree")
    root = run_git(repo, ["rev-parse", "--show-toplevel"]).stdout.strip()
    return Path(root)


def latest_tag(repo: Path) -> str | None:
    result = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def read_commits(repo: Path, since_tag: str | None) -> list[Commit]:
    revision = f"{since_tag}..HEAD" if since_tag else "HEAD"
    result = run_git(
        repo,
        [
            "log",
            "--reverse",
            "--pretty=format:%s%x1f%h%x1f%an%x1f%ad",
            "--date=short",
            revision,
        ],
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        if "does not have any commits yet" in message:
            return []
        raise RuntimeError(message)

    commits: list[Commit] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        commits.append(Commit(subject=parts[0], sha=parts[1], author=parts[2], date=parts[3]))
    return commits


def clean_description(subject: str) -> tuple[str, str | None]:
    subject = subject.strip()
    match = CONVENTIONAL_RE.match(subject)
    if not match:
        return subject, None

    commit_type = match.group("type").lower()
    description = match.group("description").strip()
    if match.group("breaking"):
        description = f"BREAKING: {description}"
    return description, commit_type


def categorize(subject: str) -> tuple[str, str]:
    description, commit_type = clean_description(subject)
    if commit_type and commit_type in CONVENTIONAL_TYPES:
        return CONVENTIONAL_TYPES[commit_type], description

    lowered = description.lower()
    first_word = re.split(r"[\s:/_-]+", lowered, maxsplit=1)[0]
    for category, prefixes in KEYWORD_PREFIXES:
        if first_word in prefixes:
            return category, description

    return "Changed", description


def grouped_entries(commits: list[Commit]) -> dict[str, list[str]]:
    groups = {category: [] for category in CATEGORY_ORDER}
    for commit in commits:
        category, description = categorize(commit.subject)
        groups[category].append(f"- {description} ({commit.sha})")
    return groups


def render_changelog(
    commits: list[Commit],
    *,
    since_tag: str | None,
    version: str,
    today: str,
) -> str:
    groups = grouped_entries(commits)
    if since_tag:
        scope = f"Generated from commits since `{since_tag}`."
    else:
        scope = "Generated from the full repository history because no git tags were found."

    lines = [
        "# Changelog",
        "",
        f"## [{version}] - {today}",
        "",
        scope,
        "",
    ]

    for category in CATEGORY_ORDER:
        lines.append(f"### {category}")
        entries = groups[category]
        if entries:
            lines.extend(entries)
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def output_path(repo: Path, requested: str) -> Path:
    path = Path(requested).expanduser()
    if path.is_absolute():
        return path
    return repo / path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git commits since the latest tag."
    )
    parser.add_argument("--repo", default=".", help="Git repository to inspect. Defaults to the current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md in the target repo.")
    parser.add_argument("--since-tag", help="Override the detected latest tag.")
    parser.add_argument("--version", default="Unreleased", help="Version heading to use in the generated changelog.")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="Date to print in the generated heading.")
    parser.add_argument("--stdout", action="store_true", help="Print the changelog instead of writing a file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        repo = normalize_repo(Path(args.repo))
        since_tag = args.since_tag if args.since_tag is not None else latest_tag(repo)
        commits = read_commits(repo, since_tag)
        changelog = render_changelog(
            commits,
            since_tag=since_tag,
            version=args.version,
            today=args.date,
        )
        if args.stdout:
            sys.stdout.write(changelog)
            return 0

        destination = output_path(repo, args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(changelog, encoding="utf-8")
        print(f"Wrote {destination}")
        return 0
    except RuntimeError as error:
        parser.exit(status=1, message=f"generate-changelog: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
