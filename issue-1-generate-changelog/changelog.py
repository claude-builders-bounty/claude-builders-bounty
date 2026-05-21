#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Added", ("add", "added", "create", "created", "new", "introduce", "implement", "support")),
    ("Fixed", ("fix", "fixed", "repair", "resolve", "resolved", "bug", "patch", "correct")),
    ("Removed", ("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecate")),
]


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def latest_tag(cwd: Path) -> str | None:
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], cwd)
    except subprocess.CalledProcessError:
        return None


def collect_commits(cwd: Path, tag: str | None) -> list[Commit]:
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    output = run_git(["log", "--no-merges", "--pretty=format:%h%x09%s", rev_range], cwd)
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, subject = line.split("\t", 1)
        commits.append(Commit(sha=sha, subject=subject.strip()))
    return commits


def categorize(subject: str) -> str:
    lowered = subject.lower()
    prefix = lowered.split(":", 1)[0]
    scope_free = prefix.split("(", 1)[0]
    for category, words in CATEGORY_RULES:
        if scope_free in words or any(word in lowered for word in words):
            return category
    return "Changed"


def render_changelog(commits: list[Commit], tag: str | None) -> str:
    grouped: dict[str, list[Commit]] = {name: [] for name in ("Added", "Fixed", "Changed", "Removed")}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    title = "Unreleased"
    base = tag or "repository start"
    lines = [
        "# Changelog",
        "",
        f"## {title}",
        "",
        f"_Generated from commits since {base}._",
        "",
    ]
    for category in ("Added", "Fixed", "Changed", "Removed"):
        lines.append(f"### {category}")
        if grouped[category]:
            for commit in grouped[category]:
                lines.append(f"- {commit.subject} ({commit.sha})")
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Path to the git repository. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path. Defaults to CHANGELOG.md.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    tag = latest_tag(repo)
    commits = collect_commits(repo, tag)
    changelog = render_changelog(commits, tag)

    if args.stdout:
        print(changelog, end="")
    else:
        output = Path(args.output)
        if not output.is_absolute():
            output = repo / output
        output.write_text(changelog, encoding="utf-8")
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
