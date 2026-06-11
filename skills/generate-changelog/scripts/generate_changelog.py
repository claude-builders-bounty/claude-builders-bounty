#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SECTIONS = ("Added", "Fixed", "Changed", "Removed")
TYPE_TO_SECTION = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "create": "Added",
    "implement": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "repair": "Fixed",
    "resolve": "Fixed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "drop": "Removed",
    "deprecate": "Removed",
    "docs": "Changed",
    "doc": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "test": "Changed",
    "tests": "Changed",
    "chore": "Changed",
    "ci": "Changed",
    "build": "Changed",
    "style": "Changed",
}
CONVENTIONAL = re.compile(r"^(?P<type>[a-z]+)(?:\([^)]+\))?(?P<breaking>!)?:\s*(?P<desc>.+)$", re.I)
REMOVED_WORDS = re.compile(r"\b(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)\b", re.I)
ADDED_WORDS = re.compile(r"\b(add|added|create|created|implement|implemented|introduce|introduced)\b", re.I)
FIXED_WORDS = re.compile(r"\b(fix|fixed|bugfix|repair|resolve|resolved)\b", re.I)


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require_git_repo(repo: Path) -> None:
    result = run_git(repo, ["rev-parse", "--is-inside-work-tree"], check=False)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise SystemExit(f"{repo} is not a git repository")


def latest_tag(repo: Path, to_ref: str) -> str | None:
    result = run_git(repo, ["describe", "--tags", "--abbrev=0", to_ref], check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def commits_since(repo: Path, from_ref: str | None, to_ref: str, include_merges: bool) -> list[Commit]:
    rev_range = f"{from_ref}..{to_ref}" if from_ref else to_ref
    args = ["log", "--pretty=format:%H%x1f%s%x1f%b%x1e", rev_range]
    if not include_merges:
        args.insert(1, "--no-merges")
    result = run_git(repo, args, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "git log failed")

    commits: list[Commit] = []
    for record in result.stdout.strip("\x1e\n").split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip("\n").split("\x1f", 2)
        if len(parts) != 3:
            continue
        commits.append(Commit(parts[0], parts[1].strip(), parts[2].strip()))
    return commits


def github_commit_base(repo: Path) -> str | None:
    result = run_git(repo, ["remote", "get-url", "origin"], check=False)
    if result.returncode != 0:
        return None
    remote = result.stdout.strip()
    if remote.startswith("git@github.com:"):
        slug = remote.removeprefix("git@github.com:").removesuffix(".git")
        return f"https://github.com/{slug}/commit"
    if remote.startswith("https://github.com/"):
        return remote.removesuffix(".git") + "/commit"
    return None


def clean_subject(subject: str) -> tuple[str, str | None, bool]:
    match = CONVENTIONAL.match(subject)
    if match:
        commit_type = match.group("type").lower()
        return match.group("desc").strip(), commit_type, bool(match.group("breaking"))
    return subject.strip(), None, False


def categorize(commit: Commit) -> tuple[str, str]:
    cleaned, commit_type, breaking = clean_subject(commit.subject)
    section = TYPE_TO_SECTION.get(commit_type or "")
    searchable = f"{commit.subject}\n{commit.body}"
    if not section:
        if REMOVED_WORDS.search(searchable):
            section = "Removed"
        elif FIXED_WORDS.search(searchable):
            section = "Fixed"
        elif ADDED_WORDS.search(searchable):
            section = "Added"
        else:
            section = "Changed"
    if breaking or "BREAKING CHANGE" in commit.body:
        cleaned = f"BREAKING: {cleaned}"
        section = "Changed"
    return section, normalize_entry(cleaned)


def normalize_entry(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "Update project"
    return text[0].upper() + text[1:]


def format_commit_ref(commit: Commit, commit_base: str | None) -> str:
    short = commit.sha[:7]
    if commit_base:
        return f" ([{short}]({commit_base}/{commit.sha}))"
    return f" ({short})"


def build_section(repo: Path, commits: list[Commit], from_ref: str | None, to_ref: str, heading: str) -> str:
    today = dt.date.today().isoformat()
    range_note = f"since `{from_ref}`" if from_ref else "from the full git history"
    commit_base = github_commit_base(repo)
    grouped: dict[str, list[str]] = {section: [] for section in SECTIONS}

    for commit in commits:
        section, message = categorize(commit)
        grouped[section].append(f"- {message}{format_commit_ref(commit, commit_base)}")

    lines = [
        f"## {heading} - {today}",
        "",
        f"Generated from commits {range_note} through `{to_ref}`.",
        "",
    ]
    for section in SECTIONS:
        lines.append(f"### {section}")
        lines.append("")
        if grouped[section]:
            lines.extend(grouped[section])
        else:
            lines.append("- No changes.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def merge_with_existing(output_path: Path, new_section: str) -> str:
    if not output_path.exists():
        return f"# Changelog\n\n{new_section}"

    existing = output_path.read_text(encoding="utf-8").strip()
    if not existing:
        return f"# Changelog\n\n{new_section}"
    lines = existing.splitlines()
    if lines and lines[0].strip().lower() == "# changelog":
        rest = "\n".join(lines[1:]).strip()
        return f"# Changelog\n\n{new_section}\n\n{rest}\n"
    return f"# Changelog\n\n{new_section}\n\n{existing}\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Path to the git repository")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output changelog path")
    parser.add_argument("--from-ref", help="Start after this tag/ref. Defaults to the latest tag")
    parser.add_argument("--to-ref", default="HEAD", help="End ref. Defaults to HEAD")
    parser.add_argument("--version-heading", default="Unreleased", help="Heading for the generated section")
    parser.add_argument("--include-merges", action="store_true", help="Include merge commits")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo = Path(args.repo).resolve()
    require_git_repo(repo)
    from_ref = args.from_ref if args.from_ref is not None else latest_tag(repo, args.to_ref)
    commits = commits_since(repo, from_ref, args.to_ref, args.include_merges)
    new_section = build_section(repo, commits, from_ref, args.to_ref, args.version_heading)

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo / output_path
    changelog = merge_with_existing(output_path, new_section)

    if args.stdout:
        print(changelog, end="")
    else:
        output_path.write_text(changelog, encoding="utf-8")
        print(f"Wrote {os.path.relpath(output_path, repo)} with {len(commits)} commits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
