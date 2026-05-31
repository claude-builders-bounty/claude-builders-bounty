#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path


CATEGORIES = {
    "Added": ("feat", "feature", "add", "added", "initial"),
    "Fixed": ("fix", "fixed", "bug", "bugfix", "patch", "resolve", "resolved"),
    "Changed": (
        "change",
        "changed",
        "update",
        "updated",
        "refactor",
        "perf",
        "docs",
        "doc",
        "chore",
        "style",
        "test",
        "build",
        "ci",
    ),
    "Removed": ("remove", "removes", "removed", "delete", "deletes", "deleted", "deprecate", "deprecated"),
}


def run_git(repo: Path, args: list[str], check: bool = True, strip: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout.strip() if strip else completed.stdout


def ensure_git_repo(repo: Path) -> None:
    run_git(repo, ["rev-parse", "--is-inside-work-tree"])


def latest_tag(repo: Path) -> str | None:
    tag = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    return tag or None


def commit_range(repo: Path, since: str | None) -> tuple[str, str | None]:
    if since:
        return since, f"{since}..HEAD"
    tag = latest_tag(repo)
    if tag:
        return tag, f"{tag}..HEAD"
    return "repository start", None


def git_log(repo: Path, rev_range: str | None) -> list[tuple[str, str, str]]:
    fmt = "%H%x1f%s%x1f%b%x1e"
    args = ["log", "--reverse", f"--pretty=format:{fmt}"]
    if rev_range:
        args.append(rev_range)
    output = run_git(repo, args, strip=False)
    commits: list[tuple[str, str, str]] = []
    for record in output.split("\x1e"):
        record = record.strip("\r\n")
        if not record.strip():
            continue
        parts = record.split("\x1f")
        if len(parts) < 3:
            continue
        commits.append((parts[0], parts[1].strip(), parts[2].strip()))
    return commits


def normalize_subject(subject: str) -> str:
    subject = subject.strip()
    if ":" in subject:
        prefix, rest = subject.split(":", 1)
        if prefix.replace("!", "").lower() in {
            "feat",
            "fix",
            "docs",
            "chore",
            "refactor",
            "perf",
            "test",
            "build",
            "ci",
            "style",
        }:
            subject = rest.strip()
    return subject[:1].upper() + subject[1:] if subject else "Update"


def category_for(subject: str, body: str) -> str:
    text = f"{subject} {body}".lower()
    conventional_type = subject.split(":", 1)[0].replace("!", "").lower() if ":" in subject else ""
    if any(keyword in text for keyword in CATEGORIES["Removed"]):
        return "Removed"
    for category, keywords in CATEGORIES.items():
        if conventional_type in keywords:
            return category
    for category, keywords in CATEGORIES.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Changed"


def render_changelog(since_label: str, commits: list[tuple[str, str, str]]) -> str:
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    for commit_hash, subject, body in commits:
        category = category_for(subject, body)
        short_hash = commit_hash[:7]
        grouped[category].append(f"- {normalize_subject(subject)} ({short_hash})")

    today = dt.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        "All notable changes are generated from git history.",
        "",
        f"## Unreleased - {today}",
        "",
        f"Commits since: `{since_label}`",
        "",
    ]
    if not commits:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in ("Added", "Fixed", "Changed", "Removed"):
        lines.append(f"### {category}")
        lines.append("")
        entries = grouped[category]
        if entries:
            lines.extend(entries)
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git commits.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git repository path.")
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"), help="Output markdown file.")
    parser.add_argument("--since", help="Git ref/tag to use as the start of the range.")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    ensure_git_repo(repo)
    since_label, rev_range = commit_range(repo, args.since)
    commits = git_log(repo, rev_range)
    changelog = render_changelog(since_label, commits)

    output = args.output if args.output.is_absolute() else repo / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
