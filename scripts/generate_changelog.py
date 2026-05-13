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
from typing import Dict, List, Optional


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    hash: str
    subject: str


def git(args: List[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def git_or_none(args: List[str], cwd: Path) -> Optional[str]:
    try:
        value = git(args, cwd)
    except RuntimeError:
        return None
    return value or None


def repo_root(path: Path) -> Path:
    root = git_or_none(["rev-parse", "--show-toplevel"], path)
    if root is None:
        raise RuntimeError(f"{path} is not inside a git repository")
    return Path(root)


def latest_tag(cwd: Path) -> Optional[str]:
    return git_or_none(["describe", "--tags", "--abbrev=0"], cwd)


def release_title(tag: Optional[str], explicit_version: Optional[str]) -> str:
    if explicit_version:
        return explicit_version
    if tag:
        return "Unreleased"
    return "Initial release"


def commit_range(cwd: Path, start_tag: Optional[str], explicit_range: Optional[str]) -> str:
    if explicit_range:
        return explicit_range
    if start_tag:
        return f"{start_tag}..HEAD"
    return "HEAD"


def read_commits(cwd: Path, revision_range: str) -> List[Commit]:
    raw = git(["log", "--no-merges", "--format=%H%x1f%s", revision_range], cwd)
    commits: List[Commit] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        full_hash, _, subject = line.partition("\x1f")
        commits.append(Commit(hash=full_hash[:7], subject=subject.strip()))
    return commits


def category_for(subject: str) -> str:
    normalized = subject.strip().lower()
    type_match = re.match(r"^(?P<type>[a-z]+)(?:\([^)]+\))?!?:", normalized)
    commit_type = type_match.group("type") if type_match else ""

    if commit_type in {"feat", "feature"} or re.search(
        r"\b(add|adds|added|create|creates|introduce|implement|support)\b", normalized
    ):
        return "Added"
    if commit_type in {"fix", "bugfix"} or re.search(
        r"\b(fix|fixes|fixed|bug|prevent|resolve|repair|correct)\b", normalized
    ):
        return "Fixed"
    if commit_type in {"remove", "removed"} or re.search(
        r"\b(remove|removes|removed|delete|deletes|drop|drops|dropped|deprecate)\b",
        normalized,
    ):
        return "Removed"
    return "Changed"


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-z]+(?:\([^)]+\))?!?:\s*", "", subject.strip(), flags=re.I)
    return subject[:1].upper() + subject[1:]


def origin_url(cwd: Path) -> Optional[str]:
    url = git_or_none(["config", "--get", "remote.origin.url"], cwd)
    if not url:
        return None
    ssh_match = re.match(r"git@github\.com:(?P<repo>.+?)(?:\.git)?$", url)
    if ssh_match:
        return f"https://github.com/{ssh_match.group('repo')}"
    https_match = re.match(r"https://github\.com/(?P<repo>.+?)(?:\.git)?$", url)
    if https_match:
        return f"https://github.com/{https_match.group('repo')}"
    return None


def format_commit(commit: Commit, repo_url: Optional[str]) -> str:
    subject = clean_subject(commit.subject)
    if repo_url:
        return f"- {subject} ([{commit.hash}]({repo_url}/commit/{commit.hash}))"
    return f"- {subject} ({commit.hash})"


def build_changelog(
    commits: List[Commit],
    tag: Optional[str],
    version: Optional[str],
    repo_url: Optional[str],
) -> str:
    today = dt.date.today().isoformat()
    grouped: Dict[str, List[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[category_for(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git commit history.",
        "",
        f"## {release_title(tag, version)} - {today}",
        "",
    ]
    if tag:
        lines.extend([f"Changes since `{tag}`.", ""])
    else:
        lines.extend(["No git tags were found; using the full commit history.", ""])

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        entries = grouped[category]
        if entries:
            lines.extend(format_commit(commit, repo_url) for commit in entries)
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from commits since the latest git tag.",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Git repository path to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output",
        default="CHANGELOG.md",
        help="Output file path. Defaults to CHANGELOG.md in the repository root.",
    )
    parser.add_argument(
        "--range",
        dest="revision_range",
        help="Optional git revision range, for example v1.0.0..HEAD.",
    )
    parser.add_argument(
        "--version",
        help="Optional release heading. Defaults to Unreleased when a tag exists.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        cwd = repo_root(Path(args.repo).resolve())
        tag = latest_tag(cwd) if args.revision_range is None else None
        commits = read_commits(cwd, commit_range(cwd, tag, args.revision_range))
        changelog = build_changelog(commits, tag, args.version, origin_url(cwd))
        output = Path(args.output)
        if not output.is_absolute():
            output = cwd / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(changelog, encoding="utf-8")
        print(f"Wrote {output}")
        return 0
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
