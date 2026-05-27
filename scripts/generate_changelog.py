#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git commits since the last tag."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def git(args: list[str], cwd: Path, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def fetch_tags(cwd: Path) -> None:
    remotes = git(["remote"], cwd, check=False)
    if remotes:
        git(["fetch", "--tags", "--quiet"], cwd, check=False)


def last_tag(cwd: Path) -> str | None:
    tag = git(["describe", "--tags", "--abbrev=0"], cwd, check=False)
    return tag or None


def commit_range(tag: str | None) -> str:
    return f"{tag}..HEAD" if tag else "HEAD"


def commits_since_tag(cwd: Path, tag: str | None) -> list[tuple[str, str]]:
    log_format = "%h%x09%s"
    output = git(["log", commit_range(tag), f"--format={log_format}"], cwd, check=False)
    commits: list[tuple[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        commit_hash, _, subject = line.partition("\t")
        commits.append((commit_hash.strip(), subject.strip()))
    return commits


def category_for(subject: str) -> str:
    normalized = subject.lower()
    prefix = normalized.split(":", 1)[0]

    if prefix.startswith("feat") or " add " in f" {normalized} ":
        return "Added"
    if prefix.startswith("fix") or " bug" in normalized or "patch" in normalized:
        return "Fixed"
    if (
        prefix.startswith("remove")
        or prefix.startswith("revert")
        or any(word in normalized for word in (" remove ", " delete ", " drop "))
    ):
        return "Removed"
    return "Changed"


def render_changelog(commits: list[tuple[str, str]], tag: str | None) -> str:
    today = dt.date.today().isoformat()
    source = f"commits since `{tag}`" if tag else "all commits because no git tag was found"
    grouped = {category: [] for category in CATEGORIES}
    for commit_hash, subject in commits:
        grouped[category_for(subject)].append(f"- {subject} (`{commit_hash}`)")

    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"Generated from {source}.",
        "",
    ]

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.append("")
        entries = grouped[category]
        if entries:
            lines.extend(entries)
        else:
            lines.append("- No entries.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=".",
        help="Repository path to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Output file path. Defaults to CHANGELOG.md in the repository.",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Do not fetch remote tags before generating the changelog.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"{repo} is not a git repository")

    if not args.no_fetch:
        fetch_tags(repo)

    tag = last_tag(repo)
    commits = commits_since_tag(repo, tag)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(render_changelog(commits, tag), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
