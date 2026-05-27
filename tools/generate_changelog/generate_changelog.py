#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run_git(repo: Path, args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def ensure_git_repo(repo: Path) -> None:
    run_git(repo, ["rev-parse", "--is-inside-work-tree"])


def fetch_tags(repo: Path) -> None:
    run_git(repo, ["fetch", "--tags", "--quiet"], check=False)


def latest_tag(repo: Path) -> str | None:
    tag = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    return tag or None


def parse_commits(raw: str) -> list[Commit]:
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip("\r\n")
        if not record:
            continue
        fields = record.split("\x1f")
        if len(fields) < 2:
            continue
        body = fields[2].strip() if len(fields) > 2 else ""
        commits.append(Commit(sha=fields[0], subject=fields[1].strip(), body=body))
    return commits


def commits_since(repo: Path, tag: str | None) -> list[Commit]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    raw = run_git(repo, ["log", revision_range, "--no-merges", "--pretty=format:%H%x1f%s%x1f%b%x1e"])
    return parse_commits(raw)


def category_for(subject: str) -> str:
    text = subject.strip().lower()
    prefix = text.split(":", 1)[0]

    if prefix in {"feat", "feature"} or any(word in text for word in ("add ", "adds ", "new ", "introduce")):
        return "Added"
    if prefix in {"fix", "bugfix", "hotfix"} or any(word in text for word in ("fix ", "fixes ", "resolve", "bug")):
        return "Fixed"
    if prefix in {"remove", "removed", "delete", "deleted"} or any(word in text for word in ("remove ", "delete ", "drop ", "deprecate")):
        return "Removed"
    return "Changed"


def format_entry(commit: Commit) -> str:
    short_sha = commit.sha[:7]
    return f"- {commit.subject} ({short_sha})"


def build_changelog(commits: list[Commit], tag: str | None, version: str) -> str:
    today = dt.date.today().isoformat()
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[category_for(commit.subject)].append(format_entry(commit))

    baseline = tag or "repository start"
    lines = [
        "# Changelog",
        "",
        f"## [{version}] - {today}",
        "",
        f"Generated from commits since {baseline}.",
        "",
    ]
    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.extend(grouped[category] or ["- No changes."])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_changelog(repo: Path, output: Path, version: str, no_fetch: bool) -> tuple[Path, int, str | None]:
    ensure_git_repo(repo)
    if not no_fetch:
        fetch_tags(repo)
    tag = latest_tag(repo)
    commits = commits_since(repo, tag)
    changelog = build_changelog(commits, tag, version)
    output_path = output if output.is_absolute() else repo / output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(changelog, encoding="utf-8")
    return output_path, len(commits), tag


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Git repository to inspect. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path. Defaults to CHANGELOG.md in the repo.")
    parser.add_argument("--version", default="Unreleased", help="Version heading to use in the changelog.")
    parser.add_argument("--no-fetch", action="store_true", help="Skip git fetch --tags before reading history.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    output = Path(args.output)
    try:
        output_path, count, tag = write_changelog(repo, output, args.version, args.no_fetch)
    except Exception as exc:
        print(f"changelog generation failed: {exc}", file=sys.stderr)
        return 1

    baseline = tag or "repository start"
    print(f"Generated {output_path} from {count} commits since {baseline}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
