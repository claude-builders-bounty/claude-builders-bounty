#!/usr/bin/env python3
"""Generate a Keep a Changelog-style CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def latest_tag(cwd: Path) -> str | None:
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], cwd)
    except subprocess.CalledProcessError:
        return None


def commits_since(ref: str | None, cwd: Path) -> list[Commit]:
    rev_range = f"{ref}..HEAD" if ref else "HEAD"
    output = run_git(["log", "--no-merges", "--pretty=format:%h%x09%s", rev_range], cwd)
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, subject = line.split("\t", 1)
        commits.append(Commit(sha=sha, subject=subject))
    return commits


def category_for(subject: str) -> str:
    clean = subject.lower().strip()
    if re.match(r"^(fix|bugfix|hotfix)(\(.+\))?:", clean) or "fix" in clean or "bug" in clean:
        return "Fixed"
    if re.match(r"^(feat|feature|add)(\(.+\))?:", clean) or clean.startswith(("add ", "added ")):
        return "Added"
    if re.match(r"^(remove|delete|drop)(\(.+\))?:", clean) or clean.startswith(("remove ", "delete ", "drop ")):
        return "Removed"
    return "Changed"


def display_subject(subject: str) -> str:
    cleaned = re.sub(r"^(feat|feature|fix|bugfix|hotfix|chore|refactor|docs|test|remove|delete|drop)(\(.+\))?:\s*", "", subject, flags=re.I)
    cleaned = cleaned.strip()
    if not cleaned:
        return subject.strip()
    return cleaned[0].upper() + cleaned[1:]


def render(commits: list[Commit], since: str | None, repo_name: str) -> str:
    grouped: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git history.",
        "",
        f"## Unreleased - {date.today().isoformat()}",
        "",
        f"_Repository: {repo_name}_",
        f"_Range: {since or 'initial commit'}..HEAD_",
        "",
    ]

    if not commits:
        lines.extend(["No changes since the last tag.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.append("")
        entries = grouped.get(category, [])
        if entries:
            for commit in entries:
                lines.append(f"- {display_subject(commit.subject)} ({commit.sha})")
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines)


def repo_name(cwd: Path) -> str:
    try:
        remote = run_git(["config", "--get", "remote.origin.url"], cwd)
    except subprocess.CalledProcessError:
        return cwd.name
    return remote.rstrip("/").removesuffix(".git").split("/")[-1] or cwd.name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest git tag.")
    parser.add_argument("--repo", default=".", help="Path to the git repository. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path. Defaults to CHANGELOG.md.")
    parser.add_argument("--since", default=None, help="Override the starting tag/ref. Defaults to latest git tag.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path(args.repo).resolve()
    if not (cwd / ".git").exists():
        raise SystemExit(f"{cwd} is not a git repository")

    since = args.since or latest_tag(cwd)
    changelog = render(commits_since(since, cwd), since, repo_name(cwd))
    output = Path(args.output)
    if not output.is_absolute():
        output = cwd / output
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
