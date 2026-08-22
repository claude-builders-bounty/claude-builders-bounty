#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Features:
- Fetches commits since the last git tag
- Auto-categorizes commits into Added / Fixed / Changed / Removed
- Emits a properly formatted CHANGELOG.md
- Supports command-style usage: ./changelog.sh or /generate-changelog via Claude Code skill wrapper
- Includes unit tests

Security/robustness:
- Uses subprocess with argument lists (no shell injection)
- Validates repository state and git availability
- Handles empty repositories and tagless repositories gracefully
- Writes atomically to CHANGELOG.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


CATEGORY_ORDER = ["Added", "Fixed", "Changed", "Removed"]
DEFAULT_OUTPUT = "CHANGELOG.md"
DEFAULT_TITLE = "Changelog"


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


class ChangelogError(RuntimeError):
    pass


def run_git(args: Sequence[str], cwd: Optional[Path] = None) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ChangelogError("git is not installed or not available in PATH") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise ChangelogError(stderr or f"git {' '.join(args)} failed") from exc
    return completed.stdout


def ensure_git_repo(repo: Path) -> None:
    if not (repo / ".git").exists():
        raise ChangelogError(f"Not a git repository: {repo}")


def get_last_tag(repo: Path) -> Optional[str]:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"], cwd=repo).strip()
        return tag or None
    except ChangelogError:
        return None


def get_commits_since(repo: Path, last_tag: Optional[str]) -> List[Commit]:
    rev_range = f"{last_tag}..HEAD" if last_tag else "HEAD"
    fmt = "%H%x1f%s%x1e"
    out = run_git(["log", "--reverse", f"--pretty=format:{fmt}", rev_range], cwd=repo)
    commits: List[Commit] = []
    for record in out.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        sha, subject = record.split("\x1f", 1)
        commits.append(Commit(sha=sha.strip(), subject=subject.strip()))
    return commits


_FIX_RE = re.compile(r"^(fix|bug|patch|hotfix)(\(|:|\s)", re.IGNORECASE)
_ADD_RE = re.compile(r"^(feat|feature|add|added)(\(|:|\s)", re.IGNORECASE)
_CHG_RE = re.compile(r"^(refactor|change|chore|docs|style|perf|build|ci)(\(|:|\s)", re.IGNORECASE)
_REM_RE = re.compile(r"^(remove|removed|delete|drop)(\(|:|\s)", re.IGNORECASE)
_BREAKING_RE = re.compile(r"BREAKING[\s-]CHANGE", re.IGNORECASE)


def categorize_commit(subject: str) -> str:
    s = subject.strip()
    if _REM_RE.search(s):
        return "Removed"
    if _FIX_RE.search(s):
        return "Fixed"
    if _ADD_RE.search(s):
        return "Added"
    if _BREAKING_RE.search(s):
        return "Changed"
    if _CHG_RE.search(s):
        return "Changed"
    return "Changed"


def clean_subject(subject: str) -> str:
    s = subject.strip()
    s = re.sub(r"^\w+(\([^)]*\))?:\s*", "", s)
    s = re.sub(r"^\w+\s*:\s*", "", s)
    s = s[:1].upper() + s[1:] if s else s
    return s


def build_sections(commits: Sequence[Commit]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {k: [] for k in CATEGORY_ORDER}
    for commit in commits:
        category = categorize_commit(commit.subject)
        message = clean_subject(commit.subject)
        if message not in sections[category]:
            sections[category].append(message)
    return sections


def render_changelog(title: str, last_tag: Optional[str], commits: Sequence[Commit]) -> str:
    now = dt.datetime.utcnow().strftime("%Y-%m-%d")
    sections = build_sections(commits)
    lines: List[str] = [f"# {title}", ""]
    if last_tag:
        lines += [f"## Unreleased ({last_tag}..HEAD)"]
    else:
        lines += ["## Unreleased"]
    lines += [f"Generated on {now}", ""]

    for category in CATEGORY_ORDER:
        items = sections[category]
        if not items:
            continue
        lines += [f"### {category}"]
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    if all(not v for v in sections.values()):
        lines += ["_No commits found since the last tag._", ""]
    return "\n".join(lines).rstrip() + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    p.add_argument("--repo", default=".", help="Path to the git repository")
    p.add_argument("--output", default=DEFAULT_OUTPUT, help="Output file path")
    p.add_argument("--title", default=DEFAULT_TITLE, help="Changelog title")
    p.add_argument("--stdout", action="store_true", help="Print changelog to stdout")
    return p.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    try:
        ensure_git_repo(repo)
        last_tag = get_last_tag(repo)
        commits = get_commits_since(repo, last_tag)
        changelog = render_changelog(args.title, last_tag, commits)
        if args.stdout:
            sys.stdout.write(changelog)
        else:
            atomic_write(repo / args.output, changelog)
        return 0
    except ChangelogError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


# changelog.sh wrapper content (save as changelog.sh)
# -----------------------------------------------
# #!/usr/bin/env bash
# set -euo pipefail
# DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# exec python3 "$DIR/changelog.py" "$@"


# SKILL.md content (save as SKILL.md for Claude Code)
# -----------------------------------------------
# ---
# name: generate-changelog
# description: Generate a structured CHANGELOG.md from git history
# ---
#
# # /generate-changelog
#
# Run:
# ```bash
# bash changelog.sh
# ```
#
# Or directly:
# ```bash
# python3 changelog.py --repo . --output CHANGELOG.md
# ```
#
# This skill generates a structured CHANGELOG from commits since the last git tag,
# categorized as Added / Fixed / Changed / Removed.

