#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from Git history."""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")
START_MARKER = "<!-- generate-changelog:start -->"
END_MARKER = "<!-- generate-changelog:end -->"

CONVENTIONAL_TYPES = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "new": "Added",
    "fix": "Fixed",
    "bug": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
    "deprecate": "Removed",
}

KEYWORDS = {
    "Added": ("add", "added", "introduce", "introduced", "create", "created", "new "),
    "Fixed": ("fix", "fixed", "repair", "repaired", "bug", "resolve", "resolved"),
    "Removed": ("remove", "removed", "delete", "deleted", "deprecate", "deprecated"),
}

CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]+")
CONVENTIONAL_RE = re.compile(
    r"^(?P<kind>[A-Za-z][A-Za-z0-9_-]*)(?:\([^)]+\))?(?P<breaking>!)?\s*:\s*(?P<subject>.+)$"
)


@dataclass(frozen=True)
class Commit:
    full_hash: str
    short_hash: str
    date: str
    subject: str


class ChangelogError(RuntimeError):
    """Raised for user-facing changelog generation failures."""


def git(repo: pathlib.Path, *args: str, check: bool = True) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip() or "unknown git error"
        raise ChangelogError(f"git {' '.join(args)} failed: {detail}")
    return process.stdout.strip()


def clean_subject(subject: str) -> str:
    cleaned = CONTROL_RE.sub(" ", subject).strip()
    return re.sub(r"\s+", " ", cleaned)


def latest_tag(repo: pathlib.Path) -> str | None:
    tag = git(repo, "describe", "--tags", "--abbrev=0", check=False)
    return tag or None


def commit_range(repo: pathlib.Path, since: str | None) -> tuple[str, str]:
    if since:
        git(repo, "rev-parse", "--verify", f"{since}^{{commit}}")
        return f"{since}..HEAD", since

    tag = latest_tag(repo)
    if tag:
        return f"{tag}..HEAD", tag
    return "HEAD", "the beginning of history"


def read_commits(repo: pathlib.Path, revision_range: str, include_merges: bool) -> list[Commit]:
    separator = "%x1f"
    terminator = "%x1e"
    args = ["log", revision_range, f"--format=%H{separator}%h{separator}%cs{separator}%s{terminator}"]
    if not include_merges:
        args.insert(1, "--no-merges")

    raw = git(repo, *args)
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        fields = record.split("\x1f", 3)
        if len(fields) != 4:
            continue
        full_hash, short_hash, date, subject = fields
        subject = clean_subject(subject)
        if subject:
            commits.append(
                Commit(
                    full_hash=full_hash.strip(),
                    short_hash=short_hash.strip(),
                    date=date.strip(),
                    subject=subject,
                )
            )
    return commits


def categorize(subject: str) -> tuple[str, str]:
    match = CONVENTIONAL_RE.match(subject)
    if match:
        kind = match.group("kind").lower()
        display_subject = match.group("subject").strip()
        if match.group("breaking"):
            return "Changed", f"{display_subject} **(breaking)**"
        return CONVENTIONAL_TYPES.get(kind, "Changed"), display_subject

    lowered = subject.lower()
    for category in ("Removed", "Fixed", "Added"):
        if any(lowered.startswith(word) or f" {word} " in lowered for word in KEYWORDS[category]):
            return category, subject
    return "Changed", subject


def group_commits(commits: Iterable[Commit]) -> dict[str, list[str]]:
    grouped = {category: [] for category in CATEGORY_ORDER}
    for commit in commits:
        category, subject = categorize(commit.subject)
        grouped[category].append(f"- {subject} (`{commit.short_hash}`)")
    return grouped


def render_section(
    grouped: dict[str, list[str]],
    version: str,
    generated_date: str,
    source_label: str,
) -> str:
    lines = [
        START_MARKER,
        f"## [{version}] - {generated_date}",
        "",
        f"_Generated from commits after {source_label}._",
        "",
    ]
    for category in CATEGORY_ORDER:
        lines.append(f"### {category}")
        lines.append("")
        entries = grouped[category]
        lines.extend(entries if entries else ["_No changes._"])
        lines.append("")
    lines.append(END_MARKER)
    return "\n".join(lines).rstrip() + "\n"


def merge_document(existing: str, generated_section: str) -> str:
    if START_MARKER in existing and END_MARKER in existing:
        before, remainder = existing.split(START_MARKER, 1)
        _, after = remainder.split(END_MARKER, 1)
        return f"{before.rstrip()}\n\n{generated_section.rstrip()}\n{after.lstrip()}".rstrip() + "\n"

    header = (
        "# Changelog\n\n"
        "All notable changes to this project are documented in this file.\n\n"
        "The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n"
    )
    if not existing.strip():
        return header + generated_section

    old = existing.strip()
    if old.startswith("# Changelog"):
        old = old[len("# Changelog") :].lstrip()
    return (
        header
        + generated_section.rstrip()
        + "\n\n---\n\n"
        + "## Previous changelog content\n\n"
        + old
        + "\n"
    )


def output_path(repo: pathlib.Path, value: str) -> pathlib.Path:
    candidate = pathlib.Path(value)
    return candidate if candidate.is_absolute() else repo / candidate


def write_atomic(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Generate a Keep a Changelog-style file from Git commits since the latest tag."
    )
    command.add_argument("--repo", default=".", help="Git repository path (default: current directory).")
    command.add_argument("--output", default="CHANGELOG.md", help="Output path, relative to --repo by default.")
    command.add_argument("--since", help="Git revision to use instead of the latest tag.")
    command.add_argument("--version", default="Unreleased", help="Version heading (default: Unreleased).")
    command.add_argument(
        "--date",
        default=dt.datetime.now(dt.timezone.utc).date().isoformat(),
        help="Date for the generated section in YYYY-MM-DD form.",
    )
    command.add_argument("--include-merges", action="store_true", help="Include merge commits.")
    command.add_argument("--dry-run", action="store_true", help="Print the result without writing a file.")
    return command


def main() -> int:
    args = parser().parse_args()
    repo = pathlib.Path(args.repo).expanduser().resolve()

    try:
        if not repo.is_dir():
            raise ChangelogError(f"repository path does not exist: {repo}")
        git(repo, "rev-parse", "--is-inside-work-tree")
        revision_range, source_label = commit_range(repo, args.since)
        commits = read_commits(repo, revision_range, args.include_merges)
        section = render_section(group_commits(commits), args.version, args.date, source_label)
        destination = output_path(repo, args.output)
        existing = destination.read_text(encoding="utf-8") if destination.exists() else ""
        document = merge_document(existing, section)

        if args.dry_run:
            sys.stdout.write(document)
        else:
            write_atomic(destination, document)
            print(f"Wrote {destination} from {len(commits)} commit(s) after {source_label}.")
        return 0
    except (ChangelogError, OSError) as error:
        print(f"generate-changelog: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
