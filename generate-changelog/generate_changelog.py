#!/usr/bin/env python3
"""从 Git 历史生成结构化 CHANGELOG.md。"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SECTION_ORDER = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def latest_tag(cwd: Path) -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def commit_range(tag: str | None) -> str:
    return f"{tag}..HEAD" if tag else "HEAD"


def read_commits(cwd: Path, tag: str | None) -> list[Commit]:
    output = run_git(["log", commit_range(tag), "--pretty=format:%h%x1f%s"], cwd)
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\x1f")
        commits.append(Commit(sha=sha.strip(), subject=subject.strip()))
    return commits


def normalize_subject(subject: str) -> str:
    cleaned = re.sub(r"^\w+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else subject


def classify(subject: str) -> str:
    lowered = subject.lower()
    conventional_type = re.match(r"^(\w+)(?:\([^)]+\))?!?:", lowered)
    if conventional_type:
        commit_type = conventional_type.group(1)
        if commit_type in {"feat", "feature"}:
            return "Added"
        if commit_type in {"fix", "bugfix", "hotfix"}:
            return "Fixed"
        if commit_type in {"remove", "removed", "delete", "deleted"}:
            return "Removed"
        if commit_type in {"refactor", "perf", "style", "docs", "test", "chore", "build", "ci"}:
            return "Changed"

    if any(keyword in lowered for keyword in ("add ", "added ", "new ", "introduce", "create ")):
        return "Added"
    if any(keyword in lowered for keyword in ("fix ", "fixed ", "bug", "crash", "repair", "resolve")):
        return "Fixed"
    if any(keyword in lowered for keyword in ("remove ", "removed ", "delete ", "drop ", "deprecate")):
        return "Removed"
    return "Changed"


def grouped_commits(commits: list[Commit]) -> dict[str, list[Commit]]:
    groups = {section: [] for section in SECTION_ORDER}
    for commit in commits:
        groups[classify(commit.subject)].append(commit)
    return groups


def render_changelog(commits: list[Commit], tag: str | None, title: str = "Unreleased") -> str:
    today = dt.date.today().isoformat()
    source = f"since `{tag}`" if tag else "from full history because no git tags were found"
    groups = grouped_commits(commits)

    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        f"## {title} - {today}",
        "",
        f"_Source: commits {source}._",
        "",
    ]

    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for section in SECTION_ORDER:
        lines.append(f"### {section}")
        entries = groups[section]
        if entries:
            for commit in entries:
                lines.append(f"- {normalize_subject(commit.subject)} ({commit.sha})")
        else:
            lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_changelog(output_path: Path, content: str) -> None:
    output_path.write_text(content, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Git repository path. Defaults to the current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output path. Defaults to CHANGELOG.md.")
    parser.add_argument("--title", default="Unreleased", help="Changelog release title. Defaults to Unreleased.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo / output_path

    try:
        tag = latest_tag(repo)
        commits = read_commits(repo, tag)
        content = render_changelog(commits, tag, args.title)
        if args.stdout:
            print(content, end="")
        else:
            write_changelog(output_path, content)
            print(f"Generated {output_path}")
        return 0
    except Exception as exc:
        print(f"generate-changelog failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
