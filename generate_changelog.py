#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def latest_tag(repo: Path) -> str | None:
    try:
        return git(repo, "describe", "--tags", "--abbrev=0")
    except subprocess.CalledProcessError:
        return None


def default_range(repo: Path) -> str:
    tag = latest_tag(repo)
    return f"{tag}..HEAD" if tag else "HEAD"


def commit_subjects(repo: Path, rev_range: str) -> list[str]:
    output = git(repo, "log", rev_range, "--pretty=format:%s", "--no-merges")
    return [line for line in output.splitlines() if line.strip()]


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject)
    return subject.strip()


def categorize(subject: str) -> str:
    lowered = subject.lower()
    if re.search(r"^(feat|feature)(\(.+\))?!?:", lowered) or re.search(
        r"\b(add|adds|added|introduce|new)\b", lowered
    ):
        return "Added"
    if re.search(r"^(fix|bugfix|hotfix)(\(.+\))?!?:", lowered) or re.search(
        r"\b(fix|fixes|fixed|bug|repair|resolve|resolves|resolved)\b", lowered
    ):
        return "Fixed"
    if re.search(r"^(remove|removed|delete|deleted|drop|dropped)(\(.+\))?!?:", lowered) or re.search(
        r"\b(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)\b", lowered
    ):
        return "Removed"
    return "Changed"


def render_changelog(subjects: list[str], rev_range: str) -> str:
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    for subject in subjects:
        grouped[categorize(subject)].append(f"- {clean_subject(subject)}")

    lines = [
        "# Changelog",
        "",
        f"Generated on {dt.date.today().isoformat()} from `{rev_range}`.",
        "",
    ]
    for category in CATEGORIES:
        lines.extend([f"### {category}", ""])
        lines.extend(grouped[category] or ["- No changes."])
        lines.append("")
    return "\n".join(lines)


def safe_print(message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = "ascii"
        print(message.encode(encoding, errors="backslashreplace").decode(encoding))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG.md from git commits since the latest tag."
    )
    parser.add_argument("--repo", default=".", help="Path to the git repository. Defaults to current directory.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file path.")
    parser.add_argument("--range", dest="rev_range", help="Optional git revision range, e.g. v1.2.0..HEAD.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()
    rev_range = args.rev_range or default_range(repo)
    subjects = commit_subjects(repo, rev_range)
    changelog = render_changelog(subjects, rev_range)

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    safe_print(f"Wrote {output}")


if __name__ == "__main__":
    main()
