#!/usr/bin/env python3
"""Generate CHANGELOG.md from commits since the latest git tag."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    hash: str
    subject: str


def run_git(args: list[str], repo: Path) -> str:
    command = [os.environ.get("GIT", "git"), *args]
    try:
        result = subprocess.run(
            command,
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError:
        if not is_wsl() or not shutil.which("git.exe") or command[0] == "git.exe":
            raise
        result = subprocess.run(
            ["git.exe", *args],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    return result.stdout.strip()


def is_wsl() -> bool:
    if os.name == "nt":
        return False
    try:
        release = Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return "microsoft" in release or "wsl" in release


def normalize_git_path(path: str) -> Path:
    match = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
    if is_wsl() and match:
        drive = match.group(1).lower()
        tail = match.group(2).replace("\\", "/")
        return Path(f"/mnt/{drive}/{tail}")
    return Path(path)


def repo_root(path: Path) -> Path:
    return normalize_git_path(run_git(["rev-parse", "--show-toplevel"], path))


def latest_tag(repo: Path) -> str | None:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"], repo)
    except subprocess.CalledProcessError:
        return None
    return tag or None


def commits_since(repo: Path, since: str | None, include_merges: bool) -> list[Commit]:
    log_range = f"{since}..HEAD" if since else "HEAD"
    args = ["log", log_range, "--format=%H%x1f%s"]
    if not include_merges:
        args.insert(1, "--no-merges")

    output = run_git(args, repo)
    if not output:
        return []

    commits = []
    for line in output.splitlines():
        full_hash, subject = line.split("\x1f", 1)
        commits.append(Commit(hash=full_hash[:7], subject=subject.strip()))
    return commits


def category_for(subject: str) -> str:
    normalized = subject.lower().strip()
    commit_type = normalized.split(":", 1)[0].split("(", 1)[0].replace("!", "")

    if commit_type in {"feat", "feature", "add"}:
        return "Added"
    if commit_type in {"fix", "bugfix", "hotfix"}:
        return "Fixed"
    if commit_type in {"remove", "removed", "delete", "deleted"}:
        return "Removed"
    if commit_type in {"refactor", "change", "changed", "chore", "docs", "perf", "style", "test"}:
        return "Changed"

    if any(word in normalized for word in ("remove", "delete", "drop", "deprecate")):
        return "Removed"
    if any(word in normalized for word in ("fix", "bug", "resolve", "correct")):
        return "Fixed"
    if any(word in normalized for word in ("add", "implement", "introduce", "create", "new ")):
        return "Added"
    return "Changed"


def grouped_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)
    return grouped


def render_changelog(grouped: dict[str, list[Commit]], since: str | None) -> str:
    comparison = f"Changes since `{since}`." if since else "Changes from all reachable commits."
    lines = [
        "# Changelog",
        "",
        f"## {date.today().isoformat()}",
        "",
        comparison,
        "",
    ]

    for category in CATEGORIES:
        lines.append(f"### {category}")
        entries = grouped[category]
        if entries:
            lines.extend(f"- {commit.subject} (`{commit.hash}`)" for commit in entries)
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Repository path. Defaults to current directory.")
    parser.add_argument("--since", help="Tag or ref to start from. Defaults to the latest git tag.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path.")
    parser.add_argument("--include-merges", action="store_true", help="Include merge commits.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = repo_root(Path(args.repo).resolve())
    since = args.since or latest_tag(repo)
    commits = commits_since(repo, since, args.include_merges)
    changelog = render_changelog(grouped_commits(commits), since)

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
