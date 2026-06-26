#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    author: str
    date: str


def run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def optional_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=False,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return completed.stdout.strip()


def repo_root() -> Path:
    return Path(run_git(["rev-parse", "--show-toplevel"]))


def last_tag() -> str | None:
    tag = optional_git(["describe", "--tags", "--abbrev=0"])
    return tag or None


def commit_range(start_tag: str | None, end_ref: str) -> str:
    return f"{start_tag}..{end_ref}" if start_tag else end_ref


def collect_commits(range_spec: str) -> list[Commit]:
    raw = optional_git(
        [
            "log",
            "--no-merges",
            "--date=short",
            "--pretty=format:%H%x1f%s%x1f%an%x1f%ad",
            range_spec,
        ]
    )
    commits: list[Commit] = []
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        commits.append(Commit(*parts))
    return commits


def classify(subject: str) -> str:
    lowered = subject.lower().strip()
    conventional = re.match(r"^(?P<kind>[a-z]+)(?:\([^)]+\))?!?:", lowered)
    if conventional:
        kind = conventional.group("kind")
        if kind == "feat":
            return "Added"
        if kind == "fix":
            return "Fixed"
        if kind in {"remove", "removed"}:
            return "Removed"
        if kind in {"refactor", "perf", "docs", "style", "test", "build", "ci", "chore"}:
            return "Changed"

    if re.search(r"\b(add|added|adds|create|created|introduce|new)\b", lowered):
        return "Added"
    if re.search(r"\b(fix|fixed|fixes|bug|repair|resolve|resolved|patch)\b", lowered):
        return "Fixed"
    if re.search(r"\b(remove|removed|removes|delete|deleted|drop|dropped)\b", lowered):
        return "Removed"
    return "Changed"


def clean_subject(subject: str) -> str:
    cleaned = re.sub(r"^[a-z]+(?:\([^)]+\))?!?:\s*", "", subject, flags=re.IGNORECASE).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else subject


def render_markdown(commits: list[Commit], start_tag: str | None, end_ref: str) -> str:
    now = dt.date.today().isoformat()
    grouped: dict[str, list[Commit]] = {name: [] for name in CATEGORIES}
    for commit in commits:
        grouped[classify(commit.subject)].append(commit)

    range_label = f"{start_tag}..{end_ref}" if start_tag else f"initial history..{end_ref}"
    lines: list[str] = [
        "# Changelog",
        "",
        f"Generated on {now} from `{range_label}`.",
        "",
        "## Unreleased",
        "",
    ]

    if not commits:
        lines.extend(["No commits found since the last tag.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.append("")
        entries = grouped[category]
        if entries:
            for commit in entries:
                short_sha = commit.sha[:7]
                subject = clean_subject(commit.subject)
                lines.append(f"- {subject} ([`{short_sha}`])")
        else:
            lines.append("- No entries.")
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a categorized CHANGELOG.md from git history.")
    parser.add_argument("--since", help="Start tag/ref. Defaults to the latest git tag.")
    parser.add_argument("--to", default="HEAD", help="End ref. Defaults to HEAD.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output Markdown path.")
    parser.add_argument("--stdout", action="store_true", help="Print Markdown instead of writing the output file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    start = args.since or last_tag()
    range_spec = commit_range(start, args.to)
    commits = collect_commits(range_spec)
    markdown = render_markdown(commits, start, args.to)

    if args.stdout:
        print(markdown)
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.write_text(markdown, encoding="utf-8")
    print(f"Wrote {output} with {len(commits)} commit(s).")
    if start:
        print(f"Range: {start}..{args.to}")
    else:
        print(f"Range: all history through {args.to} (no git tags found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
