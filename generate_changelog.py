#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

CATEGORY_PATTERNS = {
    "Removed": re.compile(r"(^|\s)(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)(\s|:|$)"),
    "Fixed": re.compile(r"(^|\s)(fix|fixed|bugfix|repair|repaired|resolve|resolved|patch|patched)(\s|:|$)"),
    "Added": re.compile(
        r"(^|\s)(add|added|create|created|implement|implemented|introduce|introduced|support|feat|feature|initial|init)(\s|:|$)"
    ),
}

CONVENTIONAL_PREFIX = re.compile(r"^[a-zA-Z]+(\([^)]+\))?!?:\s*")


def run_git(args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message)

    return result.stdout.strip()


def ensure_git_repo() -> None:
    try:
        inside_work_tree = run_git(["rev-parse", "--is-inside-work-tree"])
    except RuntimeError as exc:
        raise RuntimeError("generate_changelog.py must be run inside a git repository.") from exc

    if inside_work_tree != "true":
        raise RuntimeError("generate_changelog.py must be run inside a git repository.")


def latest_tag() -> str | None:
    tag = run_git(["describe", "--tags", "--abbrev=0"], check=False)
    return tag or None


def commit_range() -> tuple[str, str]:
    tag = latest_tag()
    if tag:
        return f"{tag}..HEAD", f"since {tag}"

    return "HEAD", "from all commits"


def clean_subject(subject: str) -> str:
    return CONVENTIONAL_PREFIX.sub("", subject).strip()


def categorize(subject: str) -> str:
    normalized = subject.lower()
    for category, pattern in CATEGORY_PATTERNS.items():
        if pattern.search(normalized):
            return category

    return "Changed"


def collect_entries(range_spec: str) -> dict[str, list[str]]:
    entries: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    log_output = run_git(["log", range_spec, "--no-merges", "--reverse", "--format=%h%x09%s"], check=False)

    if not log_output:
        return entries

    for line in log_output.splitlines():
        if "\t" not in line:
            continue

        short_hash, subject = line.split("\t", 1)
        category = categorize(subject)
        entries[category].append(f"{clean_subject(subject)} ({short_hash})")

    return entries


def render_changelog(entries: dict[str, list[str]], range_label: str) -> str:
    commit_count = sum(len(category_entries) for category_entries in entries.values())
    today = dt.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        f"Generated on {today} for commits {range_label}.",
        "",
        f"Total commits analyzed: {commit_count}",
        "",
        "## Unreleased",
        "",
    ]

    if commit_count == 0:
        lines.append("No changes detected.")
        lines.append("")
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.append("")

        category_entries = entries[category]
        if category_entries:
            lines.extend(f"- {entry}" for entry in category_entries)
        else:
            lines.append("- No changes.")

        lines.append("")

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest git tag.")
    parser.add_argument(
        "-o",
        "--output",
        default="CHANGELOG.md",
        help="Output file path. Defaults to CHANGELOG.md.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    try:
        ensure_git_repo()
        range_spec, range_label = commit_range()
        entries = collect_entries(range_spec)
        output = Path(args.output)
        output.write_text(render_changelog(entries, range_label), encoding="utf-8")
        commit_count = sum(len(category_entries) for category_entries in entries.values())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {output} from {commit_count} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
