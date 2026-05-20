#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

KEYWORDS = {
    "Added": ("feat", "add", "new", "introduce"),
    "Fixed": ("fix", "bug", "patch", "repair", "resolve"),
    "Changed": ("change", "refactor", "docs", "chore", "perf", "style", "test", "build", "ci"),
    "Removed": ("remove", "delete", "drop", "deprecate"),
}


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str

    @property
    def short_sha(self) -> str:
        return self.sha[:7]


def run_git(repo: Path, *args: str, allow_failure: bool = False) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        if allow_failure:
            return ""
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def find_latest_tag(repo: Path) -> str | None:
    tag = run_git(repo, "describe", "--tags", "--abbrev=0", allow_failure=True)
    return tag or None


def build_range(repo: Path, since: str | None) -> tuple[str, str]:
    if since:
        return f"{since}..HEAD", since

    latest_tag = find_latest_tag(repo)
    if latest_tag:
        return f"{latest_tag}..HEAD", latest_tag

    return "HEAD", "repository start"


def get_commits(repo: Path, revision_range: str) -> list[Commit]:
    raw = run_git(
        repo,
        "log",
        "--no-merges",
        "--format=%H%x1f%s%x1f%b%x1e",
        revision_range,
    )
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 2:
            continue
        sha = parts[0].strip()
        subject = parts[1].strip()
        body = parts[2].strip() if len(parts) > 2 else ""
        if sha and subject:
            commits.append(Commit(sha=sha, subject=subject, body=body))
    return commits


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return subject[:1].upper() + subject[1:] if subject else subject


def categorize(subject: str) -> str:
    normalized = subject.lower().strip()
    conventional_type = normalized.split(":", 1)[0]
    conventional_type = conventional_type.split("(", 1)[0].rstrip("!")

    for category, words in KEYWORDS.items():
        if conventional_type in words:
            return category

    for category, words in KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(word)}\b", normalized) for word in words):
            return category

    return "Changed"


def remote_compare_url(repo: Path, base_ref: str, head_ref: str = "HEAD") -> str | None:
    remote = run_git(repo, "config", "--get", "remote.origin.url", allow_failure=True)
    if not remote:
        return None

    match = re.match(r"(?:git@github\.com:|https://github\.com/)([^/]+/[^/.]+)(?:\.git)?", remote)
    if not match:
        return None

    slug = match.group(1)
    if base_ref == "repository start":
        return f"https://github.com/{slug}/commits/{head_ref}"
    return f"https://github.com/{slug}/compare/{base_ref}...{head_ref}"


def render_changelog(repo: Path, commits: list[Commit], since_ref: str, version: str) -> str:
    today = dt.date.today().isoformat()
    grouped: dict[str, list[Commit]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[categorize(commit.subject)].append(commit)

    lines = [
        "# Changelog",
        "",
        f"## {version} - {today}",
        "",
        f"_Generated from commits since {since_ref}._",
    ]

    compare_url = remote_compare_url(repo, since_ref)
    if compare_url:
        lines.extend(["", f"[Compare changes]({compare_url})"])

    for category in CATEGORIES:
        lines.extend(["", f"### {category}", ""])
        if grouped[category]:
            for commit in grouped[category]:
                lines.append(f"- {clean_subject(commit.subject)} ({commit.short_sha})")
        else:
            lines.append("- No changes.")

    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Repository path. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path.")
    parser.add_argument("--since", help="Git tag or ref to use as the changelog base.")
    parser.add_argument("--version", default="Unreleased", help="Version heading for the generated section.")
    parser.add_argument("--dry-run", action="store_true", help="Print the changelog instead of writing it.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output

    try:
        run_git(repo, "rev-parse", "--is-inside-work-tree")
        revision_range, since_ref = build_range(repo, args.since)
        commits = get_commits(repo, revision_range)
        changelog = render_changelog(repo, commits, since_ref, args.version)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    if args.dry_run:
        print(changelog)
        return 0

    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
