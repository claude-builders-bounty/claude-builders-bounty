#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git commits since the last tag."""

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
DEFAULT_MAX_COMMITS_WITHOUT_TAG = 200
CONVENTIONAL_PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(?:\([^)]+\))?!?:\s*")
ADDED_RE = re.compile(r"\b(add|adds|added|new|introduce|implement)\b")
FIXED_RE = re.compile(r"\b(fix|fixed|bug|patch|resolve|repair)\b")
REMOVED_RE = re.compile(r"\b(remove|removed|delete|deleted|drop|dropped|deprecate)\b")


class GitCommandError(Exception):
    def __init__(self, args: List[str], stdout: str, stderr: str) -> None:
        self.args_list = args
        self.stdout = stdout
        self.stderr = stderr
        message = stderr.strip() or stdout.strip() or "unknown git error"
        super().__init__(f"git {' '.join(args)} failed: {message}")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: List[str], repo: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise GitCommandError(args, exc.stdout or "", exc.stderr or "") from exc
    return completed.stdout.strip()


def find_repo_root(start: Path) -> Path:
    root = run_git(["rev-parse", "--show-toplevel"], start)
    return Path(root)


def last_tag(repo: Path) -> Optional[str]:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"], repo)
    except GitCommandError as exc:
        output = f"{exc.stderr}\n{exc.stdout}".lower()
        if "no names found" in output or "no tags can describe" in output:
            return None
        raise
    return tag or None


def commits_since(repo: Path, tag: Optional[str], max_count_without_tag: int) -> List[Commit]:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    args = ["log"]
    if tag is None and max_count_without_tag > 0:
        args.append(f"--max-count={max_count_without_tag}")
    args.extend([revision, "--pretty=format:%h%x09%s"])
    raw = run_git(args, repo)
    commits: List[Commit] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\t")
        commits.append(Commit(sha=sha, subject=subject.strip()))
    return commits


def clean_subject(subject: str) -> str:
    subject = CONVENTIONAL_PREFIX_RE.sub("", subject).strip()
    return subject[:1].upper() + subject[1:] if subject else subject


def categorize(subject: str) -> str:
    lowered = subject.lower()
    prefix = lowered.split(":", 1)[0]

    if prefix.startswith(("feat", "add")) or ADDED_RE.search(lowered):
        return "Added"
    if prefix.startswith(("fix", "bug", "hotfix")) or FIXED_RE.search(lowered):
        return "Fixed"
    if prefix.startswith(("remove", "delete", "drop")) or REMOVED_RE.search(lowered):
        return "Removed"
    return "Changed"


def render_changelog(commits: List[Commit], tag: Optional[str], history_limit: Optional[int] = None) -> str:
    today = dt.date.today().isoformat()
    if tag:
        source_label = f"from commits since {tag}"
    elif history_limit:
        source_label = f"from the last {history_limit} commits in repository history"
    else:
        source_label = "from repository history"

    grouped: Dict[str, List[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        f"## Unreleased - {today}",
        "",
        f"_Generated {source_label}._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines).rstrip() + "\n"

    for category in CATEGORIES:
        lines.append(f"### {category}")
        if grouped[category]:
            for commit in grouped[category]:
                lines.append(f"- {clean_subject(commit.subject)} ({commit.sha})")
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument(
        "-o",
        "--output",
        default="CHANGELOG.md",
        help="Output file path, relative to the repo root unless absolute.",
    )
    parser.add_argument(
        "--print",
        dest="print_changelog",
        action="store_true",
        help="Print changelog to stdout instead of writing a file.",
    )
    parser.add_argument(
        "--max-count",
        type=int,
        default=DEFAULT_MAX_COMMITS_WITHOUT_TAG,
        help="Maximum commits to read when the repo has no tags; use 0 for full history.",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        if args.max_count < 0:
            raise SystemExit("--max-count must be 0 or greater.")
        repo = find_repo_root(Path.cwd())
        tag = last_tag(repo)
        commits = commits_since(repo, tag, args.max_count)
        history_limit = args.max_count if tag is None and args.max_count > 0 else None
        changelog = render_changelog(commits, tag, history_limit)
    except GitCommandError as exc:
        raise SystemExit(str(exc)) from exc

    if args.print_changelog:
        print(changelog, end="")
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
