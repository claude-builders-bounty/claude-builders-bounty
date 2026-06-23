#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class CommitEntry:
    sha: str
    subject: str
    category: str


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or "git command failed")
    return result.stdout.strip()


def latest_tag(repo: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "describe", "--tags", "--abbrev=0"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def classify(subject: str) -> str:
    lowered = subject.lower().strip()
    prefix = lowered.split(":", 1)[0].split("(", 1)[0].strip()

    if prefix in {"feat", "feature", "add"} or lowered.startswith(("add ", "added ", "create ", "introduce ")):
        return "Added"
    if prefix in {"fix", "bugfix", "hotfix"} or lowered.startswith(("fix ", "fixed ", "repair ")):
        return "Fixed"
    if prefix in {"remove", "removed", "delete", "deleted"} or lowered.startswith(("remove ", "removed ", "delete ", "drop ")):
        return "Removed"
    return "Changed"


def collect_commits(repo: Path) -> tuple[str | None, list[CommitEntry]]:
    tag = latest_tag(repo)
    revision = f"{tag}..HEAD" if tag else "HEAD"
    output = run_git(repo, ["log", revision, "--pretty=format:%H%x09%s", "--no-merges"])
    if not output:
        return tag, []
    entries = []
    for line in output.splitlines():
        sha, subject = line.split("\t", 1)
        entries.append(CommitEntry(sha=sha[:7], subject=subject.strip(), category=classify(subject)))
    return tag, entries


def render_changelog(repo: Path, entries: list[CommitEntry], tag: str | None) -> str:
    heading = f"## Unreleased - {date.today().isoformat()}"
    source = f"Commits since `{tag}`." if tag else "Commits since repository start."
    lines = ["# Changelog", "", heading, "", source, ""]

    for category in CATEGORIES:
        items = [entry for entry in entries if entry.category == category]
        if not items:
            continue
        lines.extend([f"### {category}", ""])
        for item in items:
            lines.append(f"- {item.subject} (`{item.sha}`)")
        lines.append("")

    if not entries:
        lines.extend(["No new commits found.", ""])

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest git tag.")
    parser.add_argument("--repo", default=".", help="Repository path to inspect. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md in the current directory.")
    parser.add_argument("--stdout", action="store_true", help="Print the changelog instead of writing it.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    tag, entries = collect_commits(repo)
    changelog = render_changelog(repo, entries, tag)

    if args.stdout:
        print(changelog, end="")
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
