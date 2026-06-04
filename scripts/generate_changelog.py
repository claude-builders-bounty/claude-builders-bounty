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

PREFIX_CATEGORY = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "drop": "Removed",
    "docs": "Changed",
    "doc": "Changed",
    "chore": "Changed",
    "ci": "Changed",
    "build": "Changed",
    "perf": "Changed",
    "refactor": "Changed",
    "style": "Changed",
    "test": "Changed",
}

KEYWORD_CATEGORY = (
    ("Fixed", ("fix", "fixed", "bug", "patch", "repair", "resolve", "correct")),
    ("Removed", ("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecate")),
    ("Added", ("add", "added", "create", "created", "implement", "support", "introduce")),
    ("Changed", ("change", "changed", "update", "updated", "improve", "refactor", "rename")),
)


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def ensure_git_repo(repo: Path) -> None:
    result = run_git(repo, ["rev-parse", "--is-inside-work-tree"], check=False)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise SystemExit(f"{repo} is not a git repository")


def last_tag(repo: Path) -> str | None:
    result = run_git(repo, ["describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def git_log_range(since: str | None) -> list[str]:
    if since:
        return [f"{since}..HEAD"]
    return ["HEAD"]


def parse_commits(raw_log: str) -> list[dict[str, str]]:
    commits: list[dict[str, str]] = []
    for record in raw_log.strip("\x1e\n").split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f", 2)
        if len(parts) < 2:
            continue
        sha, subject = parts[0].strip(), parts[1].strip()
        body = parts[2].strip() if len(parts) == 3 else ""
        commits.append({"sha": sha, "subject": subject, "body": body})
    return commits


def load_commits(repo: Path, since: str | None, include_merges: bool) -> list[dict[str, str]]:
    args = ["log", "--pretty=format:%H%x1f%s%x1f%b%x1e"]
    if not include_merges:
        args.append("--no-merges")
    args.extend(git_log_range(since))
    result = run_git(repo, args, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "Unable to read git history")
    return parse_commits(result.stdout)


def category_for(subject: str) -> str:
    normalized = subject.strip().lower()
    conventional = re.match(r"^(?P<prefix>[a-z]+)(?:\([^)]+\))?!?:", normalized)
    if conventional:
        prefix = conventional.group("prefix")
        return PREFIX_CATEGORY.get(prefix, "Changed")

    words = re.findall(r"[a-z0-9]+", normalized)
    for category, keywords in KEYWORD_CATEGORY:
        if any(keyword in words for keyword in keywords):
            return category
    return "Changed"


def strip_conventional_prefix(subject: str) -> str:
    cleaned = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else subject


def group_commits(commits: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[category_for(commit["subject"])].append(commit)
    return grouped


def render_changelog(
    grouped: dict[str, list[dict[str, str]]],
    version: str,
    since: str | None,
    include_empty: bool,
) -> str:
    date = dt.date.today().isoformat()
    scope = f"Changes since `{since}`." if since else "No git tags found; includes all commits."
    lines = [
        "# Changelog",
        "",
        f"## {version} - {date}",
        "",
        f"_{scope}_",
        "",
    ]

    for category in CATEGORIES:
        entries = grouped[category]
        if not entries and not include_empty:
            continue
        lines.append(f"### {category}")
        if entries:
            for commit in entries:
                subject = strip_conventional_prefix(commit["subject"])
                short_sha = commit["sha"][:7]
                lines.append(f"- {subject} (`{short_sha}`)")
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from commits since the last git tag."
    )
    parser.add_argument("--repo", default=".", help="Git repository path. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output changelog path.")
    parser.add_argument("--version", default="Unreleased", help="Version heading to write.")
    parser.add_argument("--since", help="Git ref/tag to start from. Defaults to the latest tag.")
    parser.add_argument("--include-merges", action="store_true", help="Include merge commits.")
    parser.add_argument(
        "--skip-empty-sections",
        action="store_true",
        help="Omit categories with no matching commits.",
    )
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing it.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    ensure_git_repo(repo)

    since = args.since or last_tag(repo)
    commits = load_commits(repo, since, args.include_merges)
    grouped = group_commits(commits)
    changelog = render_changelog(
        grouped=grouped,
        version=args.version,
        since=since,
        include_empty=not args.skip_empty_sections,
    )

    if args.stdout:
        sys.stdout.write(changelog)
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    with output.open("w", encoding="utf-8", newline="\n") as changelog_file:
        changelog_file.write(changelog)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
