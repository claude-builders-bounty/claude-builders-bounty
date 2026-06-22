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

PREFIX_TO_CATEGORY = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "create": "Added",
    "implement": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "patch": "Fixed",
    "change": "Changed",
    "changed": "Changed",
    "update": "Changed",
    "improve": "Changed",
    "refactor": "Changed",
    "perf": "Changed",
    "style": "Changed",
    "docs": "Changed",
    "test": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "remove": "Removed",
    "delete": "Removed",
    "drop": "Removed",
    "deprecate": "Removed",
}

VERB_HINTS = (
    ("Removed", re.compile(r"\b(remove|removed|delete|deleted|drop|dropped|deprecat)", re.I)),
    ("Fixed", re.compile(r"\b(fix|fixed|bug|patch|repair|resolve|resolved)", re.I)),
    ("Added", re.compile(r"\b(add|added|create|created|implement|implemented|introduce|initial)", re.I)),
)

CONVENTIONAL_RE = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?(?P<breaking>!)?:\s*(?P<text>.+)$")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    date: str


def run_git(args: list[str], repo: Path, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def repo_root(path: Path) -> Path:
    root = run_git(["rev-parse", "--show-toplevel"], path)
    return Path(root)


def latest_tag(repo: Path) -> str | None:
    tag = run_git(["describe", "--tags", "--abbrev=0"], repo, check=False)
    return tag or None


def collect_commits(repo: Path, tag: str | None) -> list[Commit]:
    revision_range = f"{tag}..HEAD" if tag else "HEAD"
    raw = run_git(
        ["log", "--no-merges", "--pretty=format:%H%x1f%s%x1f%ad", "--date=short", revision_range],
        repo,
        check=False,
    )
    commits: list[Commit] = []
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3:
            commits.append(Commit(sha=parts[0], subject=parts[1], date=parts[2]))
    commits.reverse()
    return commits


def clean_subject(subject: str) -> tuple[str, str]:
    match = CONVENTIONAL_RE.match(subject)
    if match:
        commit_type = match.group("type").lower()
        text = match.group("text").strip()
        if match.group("breaking"):
            return "Changed", text
        return PREFIX_TO_CATEGORY.get(commit_type, "Changed"), sentence_case(text)

    lowered = subject.strip().lower()
    first_word = re.split(r"[\s:/_-]+", lowered, maxsplit=1)[0]
    if first_word in PREFIX_TO_CATEGORY:
        cleaned = re.sub(r"^[A-Za-z]+[\s:/_-]+", "", subject.strip(), count=1)
        return PREFIX_TO_CATEGORY[first_word], sentence_case(cleaned)

    for category, pattern in VERB_HINTS:
        if pattern.search(subject):
            return category, sentence_case(subject)
    return "Changed", sentence_case(subject)


def sentence_case(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    return text[:1].upper() + text[1:]


def build_changelog(commits: list[Commit], tag: str | None, include_hashes: bool) -> str:
    today = dt.date.today().isoformat()
    scope = f"commits since `{tag}`" if tag else "the full git history"
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}

    for commit in commits:
        category, text = clean_subject(commit.subject)
        suffix = f" (`{commit.sha[:7]}`)" if include_hashes else ""
        grouped[category].append(f"- {text}{suffix}")

    lines = [
        "# Changelog",
        "",
        f"## [Unreleased] - {today}",
        "",
        f"_Generated from {scope}._",
        "",
    ]

    if not commits:
        lines.extend(["No changes recorded.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        lines.append(f"### {category}")
        lines.extend(grouped[category] or ["- No changes."])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Git repository path. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md.")
    parser.add_argument("--since-tag", default=None, help="Override the tag used as the lower bound.")
    parser.add_argument("--no-hashes", action="store_true", help="Do not include short commit hashes in entries.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing the output file.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        repo = repo_root(Path(args.repo).resolve())
        tag = args.since_tag if args.since_tag is not None else latest_tag(repo)
        commits = collect_commits(repo, tag)
        changelog = build_changelog(commits, tag, include_hashes=not args.no_hashes)

        if args.stdout:
            print(changelog, end="")
            return 0

        output = Path(args.output)
        if not output.is_absolute():
            output = repo / output
        output.write_text(changelog, encoding="utf-8")
        print(f"Wrote {output}")
        return 0
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"generate-changelog: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
