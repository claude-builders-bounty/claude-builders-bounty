#!/usr/bin/env python3
"""Generate a small, conventional CHANGELOG from git commit subjects."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


CATEGORIES = (
    ("Added", ("feat", "add", "new")),
    ("Fixed", ("fix", "bug", "patch", "resolve")),
    ("Removed", ("remove", "delete", "drop")),
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def last_tag(repo: Path) -> str | None:
    try:
        return git(repo, "describe", "--tags", "--abbrev=0") or None
    except subprocess.CalledProcessError:
        return None


def classify(subject: str) -> str:
    lowered = subject.lower()
    for category, prefixes in CATEGORIES:
        if any(
            lowered == prefix
            or lowered.startswith(f"{prefix}:")
            or lowered.startswith(f"{prefix}(")
            or f"{prefix} " in lowered
            for prefix in prefixes
        ):
            return category
    return "Changed"


def commits(repo: Path, revision: str) -> list[tuple[str, str]]:
    output = git(repo, "log", "--format=%H%x09%s", "--no-merges", revision)
    entries: list[tuple[str, str]] = []
    for line in output.splitlines():
        if not line:
            continue
        commit_hash, _, subject = line.partition("\t")
        if subject:
            entries.append((commit_hash[:7], subject))
    return entries


def render(repo: Path, revision: str, label: str) -> str:
    grouped = {category: [] for category, _ in CATEGORIES}
    grouped["Changed"] = []
    for short_hash, subject in commits(repo, revision):
        grouped[classify(subject)].append(f"- {subject} ({short_hash})")

    lines = ["# Changelog", "", f"## [{label}]", ""]
    for category in ("Added", "Fixed", "Changed", "Removed"):
        lines.extend([f"### {category}", ""])
        lines.extend(grouped[category] or ["- None"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument("--output", default="CHANGELOG.md", type=Path)
    parser.add_argument("--from-tag", help="Use TAG..HEAD instead of the latest tag")
    parser.add_argument("--label", default="Unreleased")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    tag = args.from_tag or last_tag(repo)
    revision = f"{tag}..HEAD" if tag else "HEAD"
    result = render(repo, revision, args.label)
    if args.stdout:
        print(result, end="")
    else:
        output = args.output if args.output.is_absolute() else repo / args.output
        output.write_text(result, encoding="utf-8")
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
