#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from commits since the latest git tag."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
DEFAULT_OUTPUT = "CHANGELOG.md"


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run_git(args: list[str], repo: pathlib.Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def optional_git(args: list[str], repo: pathlib.Path) -> str | None:
    try:
        value = run_git(args, repo)
    except RuntimeError:
        return None
    return value or None


def repo_root(path: pathlib.Path) -> pathlib.Path:
    root = optional_git(["rev-parse", "--show-toplevel"], path)
    if root is None:
        raise RuntimeError(f"{path} is not inside a git repository")
    return pathlib.Path(root)


def latest_tag(repo: pathlib.Path) -> str | None:
    return optional_git(["describe", "--tags", "--abbrev=0"], repo)


def commit_range(repo: pathlib.Path, since: str | None) -> tuple[str | None, list[str]]:
    tag = since if since is not None else latest_tag(repo)
    if tag:
        return tag, [f"{tag}..HEAD"]
    return None, ["HEAD"]


def load_commits(repo: pathlib.Path, since: str | None) -> tuple[str | None, list[Commit]]:
    base_ref, revision_args = commit_range(repo, since)
    raw_log = run_git(
        [
            "log",
            "--no-merges",
            "--format=%H%x1f%s%x1f%b%x1e",
            *revision_args,
        ],
        repo,
    )
    commits: list[Commit] = []
    for record in raw_log.split("\x1e"):
        cleaned_record = record.strip()
        if not cleaned_record:
            continue
        parts = cleaned_record.split("\x1f", 2)
        if len(parts) < 2:
            continue
        sha = parts[0].strip()
        subject = parts[1].strip()
        body = parts[2].strip() if len(parts) == 3 else ""
        if subject:
            commits.append(Commit(sha=sha, subject=subject, body=body))
    return base_ref, commits


def conventional_type(subject: str) -> str | None:
    match = re.match(r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?!?:\s+", subject)
    if not match:
        return None
    return match.group("type").lower()


def categorize(commit: Commit) -> str:
    subject = commit.subject.lower()
    commit_type = conventional_type(commit.subject)

    if commit_type in {"fix", "bugfix", "hotfix"}:
        return "Fixed"
    if commit_type in {"feat", "feature"}:
        return "Added"
    if commit_type in {"remove", "removed"}:
        return "Removed"
    if commit_type in {"change", "changed", "refactor", "perf", "docs", "test", "build", "ci", "chore", "style"}:
        return "Changed"

    if re.search(r"\b(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)\b", subject):
        return "Removed"
    if re.search(r"\b(fix|fixed|bug|repair|resolve|resolved|correct|corrected|patch)\b", subject):
        return "Fixed"
    if re.search(r"\b(add|added|create|created|introduce|introduced|implement|implemented|new)\b", subject):
        return "Added"
    return "Changed"


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s+", "", subject).strip()
    if not subject:
        return "Update project"
    return subject[0].upper() + subject[1:]


def grouped_commits(commits: list[Commit]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    seen: set[tuple[str, str]] = set()
    for commit in commits:
        category = categorize(commit)
        item = f"- {clean_subject(commit.subject)} ({commit.sha[:7]})"
        dedupe_key = (category, item)
        if dedupe_key in seen:
            continue
        grouped[category].append(item)
        seen.add(dedupe_key)
    return grouped


def render_changelog(base_ref: str | None, commits: list[Commit], version: str) -> str:
    today = dt.date.today().isoformat()
    base_line = f"Changes since `{base_ref}`." if base_ref else "Changes from the full git history; no tags were found."
    lines = [
        "# Changelog",
        "",
        f"## {version} - {today}",
        "",
        base_line,
        "",
    ]

    grouped = grouped_commits(commits)
    if not commits:
        lines.extend(["No commits found since the last git tag.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        items = grouped[category]
        if items:
            lines.extend(items)
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_changelog(output_path: pathlib.Path, content: str) -> None:
    output_path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits since the latest tag.")
    parser.add_argument("--repo", default=".", help="Path inside the git repository. Default: current directory.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path. Default: CHANGELOG.md at repo root.")
    parser.add_argument("--since", default=None, help="Override the base tag/ref. Default: latest git tag.")
    parser.add_argument("--version", default="Unreleased", help="Changelog section version label. Default: Unreleased.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = repo_root(pathlib.Path(args.repo).resolve())
        base_ref, commits = load_commits(root, args.since)
        content = render_changelog(base_ref, commits, args.version)
        output_path = pathlib.Path(args.output)
        if not output_path.is_absolute():
            output_path = root / output_path
        write_changelog(output_path, content)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
