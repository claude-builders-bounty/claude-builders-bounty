#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    subject: str
    sha: str


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def get_latest_tag() -> str | None:
    try:
        return run_git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None


def get_commits(since_ref: str | None) -> list[Commit]:
    range_arg = f"{since_ref}..HEAD" if since_ref else "HEAD"
    output = run_git(["log", range_arg, "--pretty=format:%h%x09%s"])
    commits: list[Commit] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        sha, subject = line.split("\t", 1)
        commits.append(Commit(subject=subject.strip(), sha=sha.strip()))
    return commits


def classify(subject: str) -> str:
    normalized = subject.lower()
    prefix = normalized.split(":", 1)[0].split("(", 1)[0].strip()

    if prefix in {"feat", "feature", "add"} or normalized.startswith("add "):
        return "Added"
    if prefix in {"fix", "bugfix", "hotfix"} or "fix" in normalized or "bug" in normalized:
        return "Fixed"
    if prefix in {"remove", "removed", "delete", "deleted"} or normalized.startswith(("remove ", "delete ")):
        return "Removed"
    return "Changed"


def clean_subject(subject: str) -> str:
    def sentence_case(text: str) -> str:
        return text[:1].upper() + text[1:] if text else text

    if ":" in subject:
        prefix = subject.split(":", 1)[0].lower()
        bare_prefix = prefix.split("(", 1)[0].strip()
        if bare_prefix in {
            "feat",
            "feature",
            "add",
            "fix",
            "bugfix",
            "hotfix",
            "chore",
            "docs",
            "refactor",
            "style",
            "test",
            "remove",
            "delete",
        }:
            return sentence_case(subject.split(":", 1)[1].strip())
    return subject.strip()


def render_changelog(commits: list[Commit], since_ref: str | None) -> str:
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[classify(commit.subject)].append(commit)

    today = dt.date.today().isoformat()
    title = f"## Unreleased - {today}"
    scope = f"Commits since `{since_ref}`." if since_ref else "All commits; no git tag was found."

    lines = [
        "# Changelog",
        "",
        "All notable changes generated from git history.",
        "",
        title,
        "",
        scope,
        "",
    ]

    if not commits:
        lines.extend(["No commits found.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        if grouped[category]:
            for commit in grouped[category]:
                lines.append(f"- {clean_subject(commit.subject)} (`{commit.sha}`)")
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output changelog path.")
    args = parser.parse_args()

    since_ref = get_latest_tag()
    commits = get_commits(since_ref)
    changelog = render_changelog(commits, since_ref)
    Path(args.output).write_text(changelog, encoding="utf-8")
    print(f"Wrote {args.output} with {len(commits)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
