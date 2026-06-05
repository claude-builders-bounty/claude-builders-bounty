#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import subprocess
import sys


CATEGORIES = {
    "Added": [r"^add\b", r"^feat\b", r"feature", r"new ", r"introduce"],
    "Changed": [r"^change\b", r"^update\b", r"^refactor\b", r"improve", r"enhance"],
    "Fixed": [r"^fix\b", r"bug", r"resolve", r"repair", r"correct"],
    "Removed": [r"^remove\b", r"delete", r"drop "],
    "Security": [r"security", r"vulnerab", r"cve", r"auth"],
    "Deprecated": [r"deprecat"],
}


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def latest_tag() -> str | None:
    try:
        tag = run_git(["describe", "--tags", "--abbrev=0"])
        return tag or None
    except RuntimeError:
        return None


def collect_commits(start_ref: str | None, end_ref: str) -> list[tuple[str, str]]:
    revision_range = f"{start_ref}..{end_ref}" if start_ref else end_ref
    raw = run_git(["log", revision_range, "--pretty=format:%h%x09%s"])
    commits: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        short_hash, _, subject = line.partition("\t")
        commits.append((short_hash.strip(), subject.strip()))
    return commits


def categorize(subject: str) -> str:
    normalized = subject.lower()
    conventional_match = re.match(r"^(feat|fix|docs|chore|refactor|test|perf|ci)(?:\(.+?\))?:", normalized)
    if conventional_match:
        commit_type = conventional_match.group(1)
        if commit_type == "feat":
            return "Added"
        if commit_type == "fix":
            return "Fixed"
        if commit_type in {"refactor", "perf"}:
            return "Changed"

    for category, patterns in CATEGORIES.items():
        if any(re.search(pattern, normalized) for pattern in patterns):
            return category
    return "Other"


def render_section(commits: list[tuple[str, str]], start_ref: str | None, end_ref: str) -> str:
    today = dt.date.today().isoformat()
    heading = f"## Unreleased - {today}"
    heading += f" ({start_ref}...{end_ref})" if start_ref else f" ({end_ref})"

    grouped: dict[str, list[tuple[str, str]]] = {category: [] for category in [*CATEGORIES.keys(), "Other"]}
    for commit in commits:
        grouped[categorize(commit[1])].append(commit)

    lines = ["# Changelog", "", heading, ""]
    if not commits:
        lines.append("_No commits found for this range._")
        lines.append("")
        return "\n".join(lines)

    for category, items in grouped.items():
        if not items:
            continue
        lines.append(f"### {category}")
        lines.append("")
        for short_hash, subject in items:
            lines.append(f"- {subject} (`{short_hash}`)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def merge_with_existing(output_path: pathlib.Path, new_section: str) -> str:
    if not output_path.exists():
        return new_section

    existing = output_path.read_text(encoding="utf-8")
    if existing.startswith("# Changelog"):
        body = existing.split("\n", 2)
        if len(body) == 3:
            return f"# Changelog\n\n{new_section.split(chr(10), 2)[2].rstrip()}\n\n{body[2].lstrip()}"
    return f"{new_section.rstrip()}\n\n{existing.lstrip()}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    parser.add_argument("--from", dest="from_ref", help="Start ref or tag. Defaults to latest reachable tag.")
    parser.add_argument("--to", dest="to_ref", default="HEAD", help="End ref. Defaults to HEAD.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output changelog path.")
    parser.add_argument("--dry-run", action="store_true", help="Print generated changelog instead of writing it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        start_ref = args.from_ref if args.from_ref is not None else latest_tag()
        commits = collect_commits(start_ref, args.to_ref)
        section = render_section(commits, start_ref, args.to_ref)
        output_path = pathlib.Path(args.output)
        final_content = section if args.dry_run else merge_with_existing(output_path, section)
        if args.dry_run:
            print(final_content)
        else:
            output_path.write_text(final_content, encoding="utf-8")
            print(f"Wrote {output_path} with {len(commits)} commits.")
        return 0
    except Exception as exc:
        print(f"generate-changelog failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
