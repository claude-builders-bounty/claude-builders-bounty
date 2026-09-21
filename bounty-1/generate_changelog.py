#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from Git history."""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

SECTIONS = ("Added", "Fixed", "Changed", "Removed")
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<text>.+)$"
)


class ChangelogError(RuntimeError):
    pass


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str

def git(args: Sequence[str], *, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ChangelogError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def latest_tag(repo: Path) -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=repo, text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag or None


def read_commits(repo: Path, since: str | None, until: str) -> list[Commit]:
    revision = f"{since}..{until}" if since else until
    raw = git(
        ["log", revision, "--no-merges", "--format=%H%x1f%s%x1f%b%x1e"],
        cwd=repo,
    )
    commits: list[Commit] = []
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split("\x1f", 2)
        if len(parts) != 3:
            raise ChangelogError("unexpected git log record format")
        commits.append(Commit(parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return commits
def classify(commit: Commit) -> tuple[str, str, bool]:
    subject = commit.subject.strip()
    match = CONVENTIONAL_RE.match(subject)
    ctype = match.group("type").lower() if match else ""
    text = match.group("text").strip() if match else subject
    breaking = bool(match and match.group("breaking")) or "BREAKING CHANGE:" in commit.body

    if ctype in {"feat", "add", "new"}:
        section = "Added"
    elif ctype in {"fix", "bug", "patch"}:
        section = "Fixed"
    elif ctype in {"remove", "removed", "delete", "deprecate"}:
        section = "Removed"
    elif ctype:
        section = "Changed"
    elif re.match(r"^(remove|delete|deprecat)\b", subject, re.I):
        section = "Removed"
    elif re.match(r"^(fix|bug|patch)\b", subject, re.I):
        section = "Fixed"
    elif re.match(r"^(add|new|introduce)\b", subject, re.I):
        section = "Added"
    else:
        section = "Changed"

    return section, text, breaking


def render(commits: Sequence[Commit], *, date: str, heading: str) -> str:
    grouped: dict[str, list[str]] = {section: [] for section in SECTIONS}
    for commit in commits:
        section, text, breaking = classify(commit)
        marker = " **BREAKING**" if breaking else ""
        grouped[section].append(f"- {text}{marker} (`{commit.sha[:7]}`)")

    lines = [f"## {heading} - {date}", ""]
    for section in SECTIONS:
        items = grouped[section]
        if not items:
            continue
        lines.extend([f"### {section}", *items, ""]
        )
    return "\n".join(lines).rstrip() + "\n"
def update_file(path: Path, entry: str) -> None:
    if not path.exists():
        path.write_text("# Changelog\n\n" + entry, encoding="utf-8")
        return
    existing = path.read_text(encoding="utf-8")
    if existing.startswith("# Changelog"):
        first_line, _, rest = existing.partition("\n")
        content = first_line + "\n\n" + entry + "\n" + rest.lstrip("\n")
    else:
        content = "# Changelog\n\n" + entry + "\n" + existing
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--since", help="tag/commit/date; default: latest tag")
    parser.add_argument("--until", default="HEAD", help="end revision (default: HEAD)")
    parser.add_argument("--output", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--heading", default="Unreleased")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--stdout", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo.resolve()
    since = args.since if args.since is not None else latest_tag(repo)
    commits = read_commits(repo, since, args.until)
    if not commits:
        raise ChangelogError("no commits found in the requested range")
    entry = render(commits, date=args.date, heading=args.heading)
    if args.stdout:
        print(entry, end="")
    else:
        output = args.output if args.output.is_absolute() else repo / args.output
        update_file(output, entry)
        print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ChangelogError as exc:
        raise SystemExit(f"generate-changelog: {exc}")
