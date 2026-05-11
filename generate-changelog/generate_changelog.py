#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
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


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def ensure_git_repo(cwd: Path) -> None:
    run_git(["rev-parse", "--is-inside-work-tree"], cwd)


def latest_tag(cwd: Path) -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def current_repo_name(cwd: Path) -> str:
    remote = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    ).stdout.strip()

    if remote:
        normalized = remote.removesuffix(".git").replace("\\", "/")
        return normalized.rsplit("/", 2)[-2] + "/" + normalized.rsplit("/", 1)[-1] if "/" in normalized else normalized

    return cwd.name


def commits_since_tag(cwd: Path, tag: str | None) -> list[Commit]:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    output = run_git(["log", revision, "--pretty=format:%H%x1f%s"], cwd)
    if not output:
        return []

    commits: list[Commit] = []
    for line in output.splitlines():
        sha, subject = line.split("\x1f", 1)
        commits.append(Commit(sha=sha, subject=subject.strip()))
    return commits


def category_for(subject: str) -> str:
    normalized = subject.lower()
    conventional = re.match(r"^(?P<kind>[a-z]+)(?:\([^)]+\))?!?:", normalized)
    kind = conventional.group("kind") if conventional else ""

    if kind in {"feat", "feature", "add"} or normalized.startswith(("add ", "adds ", "implement ")):
        return "Added"
    if kind in {"fix", "bugfix"} or any(word in normalized for word in ("fix", "bug", "repair", "resolve")):
        return "Fixed"
    if kind in {"remove", "delete"} or any(word in normalized for word in ("remove", "delete", "drop", "deprecate")):
        return "Removed"
    return "Changed"


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-z]+(?:\([^)]+\))?!?:\s*", "", subject, flags=re.IGNORECASE)
    return subject[:1].upper() + subject[1:] if subject else subject


def render_changelog(repo_name: str, tag: str | None, commits: list[Commit]) -> str:
    today = dt.date.today().isoformat()
    title = f"Changes since `{tag}`" if tag else "Changes from full git history"
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}

    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"_Repository: {repo_name}_",
        f"_Range: {title}_",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.append("")
        items = grouped[category]
        if not items:
            lines.append("- No changes.")
        else:
            for commit in items:
                lines.append(f"- {clean_subject(commit.subject)} (`{commit.sha[:7]}`)")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_changelog(content: str, output_path: Path, dry_run: bool) -> None:
    if dry_run:
        print(content, end="")
        return
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote {output_path}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the git repository to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Output file path. Defaults to CHANGELOG.md in the current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated changelog instead of writing a file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = Path.cwd() / output_path

    try:
        ensure_git_repo(repo)
        tag = latest_tag(repo)
        commits = commits_since_tag(repo, tag)
        changelog = render_changelog(current_repo_name(repo), tag, commits)
        write_changelog(changelog, output_path, args.dry_run)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
