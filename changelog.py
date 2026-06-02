#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import subprocess
from datetime import date
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()


def last_tag() -> str | None:
    try:
        tag = git(["describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None
    return tag or None


def commit_subjects(tag: str | None) -> list[str]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        output = git(["log", revision_range, "--pretty=format:%s"])
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def clean_subject(subject: str) -> str:
    lowered = subject.lower()
    prefixes = (
        "feat:",
        "feature:",
        "fix:",
        "bugfix:",
        "docs:",
        "doc:",
        "chore:",
        "refactor:",
        "perf:",
        "test:",
        "remove:",
        "removed:",
        "delete:",
        "deleted:",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            cleaned = subject[len(prefix) :].strip()
            return cleaned[:1].upper() + cleaned[1:] if cleaned else subject
    return subject[:1].upper() + subject[1:] if subject else subject


def categorize(subject: str) -> str:
    lowered = f" {subject.lower()} "
    if subject.lower().startswith(("feat:", "feature:")) or any(
        word in lowered for word in (" add ", " added ", " new ")
    ):
        return "Added"
    if subject.lower().startswith(("fix:", "bugfix:")) or any(
        word in lowered for word in (" fix ", " fixed ", " bug ", " broken ")
    ):
        return "Fixed"
    if subject.lower().startswith(("remove:", "removed:", "delete:", "deleted:")) or any(
        word in lowered for word in (" remove ", " removed ", " delete ", " deleted ")
    ):
        return "Removed"
    return "Changed"


def build_changelog(subjects: list[str], tag: str | None) -> str:
    grouped = {category: [] for category in CATEGORIES}
    for subject in subjects:
        grouped[categorize(subject)].append(clean_subject(subject))

    base = tag or "repository start"
    lines = [
        "# Changelog",
        "",
        f"## Unreleased - {date.today().isoformat()}",
        "",
        f"_Generated from commits since {base}._",
        "",
    ]
    if not subjects:
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        if grouped[category]:
            lines.extend(f"- {item}" for item in grouped[category])
        else:
            lines.append("- No changes.")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the last git tag.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file.")
    args = parser.parse_args()

    tag = last_tag()
    subjects = commit_subjects(tag)
    changelog = build_changelog(subjects, tag)

    if args.stdout:
        print(changelog)
    else:
        Path(args.output).write_text(changelog, encoding="utf-8")
        print(f"Wrote {args.output} from {len(subjects)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
