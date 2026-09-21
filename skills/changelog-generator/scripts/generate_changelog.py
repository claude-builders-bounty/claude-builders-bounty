#!/usr/bin/env python3
"""Generate a Keep-a-Changelog document from commits after the latest tag."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

CATEGORY_BY_TYPE = {
    "feat": "Added",
    "fix": "Fixed",
    "remove": "Removed",
    "removed": "Removed",
    "revert": "Removed",
}
CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")
CONVENTIONAL = re.compile(r"^(?P<type>[A-Za-z][\w-]*)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<description>.+)$")


class GitError(RuntimeError):
    pass


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if check and result.returncode:
        raise GitError(result.stderr.strip() or "git command failed")
    return result.stdout.rstrip("\n")


def latest_tag(repo: Path) -> str | None:
    value = git(repo, "describe", "--tags", "--abbrev=0", check=False).strip()
    return value or None


def get_commits(repo: Path, since_tag: str | None = None) -> tuple[str | None, list[tuple[str, str]]]:
    """Return (range tag, commits) using NUL delimiters so subjects stay intact."""
    boundary = since_tag if since_tag is not None else latest_tag(repo)
    revision = f"{boundary}..HEAD" if boundary else "HEAD"
    # `-z` removes the record-separating newline that otherwise becomes part
    # of the next hash when subjects and hashes are parsed as NUL fields.
    raw = git(repo, "log", "-z", "--no-merges", "--format=%h%x00%s", revision)
    fields = raw.split("\x00") if raw else []
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) % 2:
        raise GitError("unexpected git log output")
    return boundary, list(zip(fields[0::2], fields[1::2]))


def parse_commit(short_hash: str, subject: str) -> dict[str, str | None]:
    match = CONVENTIONAL.match(subject.strip())
    if not match:
        return {"hash": short_hash, "category": "Changed", "scope": None, "description": subject.strip()}
    commit_type = match.group("type").lower()
    category = CATEGORY_BY_TYPE.get(commit_type, "Changed")
    description = match.group("description").strip()
    if match.group("breaking"):
        description += " **(breaking)**"
    return {"hash": short_hash, "category": category, "scope": match.group("scope"), "description": description}


def render(commits: list[dict[str, str | None]], version: str = "Unreleased", release_date: str | None = None) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    for commit in commits:
        scope = f"**{commit['scope']}**: " if commit["scope"] else ""
        grouped[str(commit["category"])].append(f"- {scope}{commit['description']} ({commit['hash']})")

    heading = f"## [{version}]"
    if version != "Unreleased":
        heading += f" - {release_date or date.today().isoformat()}"
    lines = ["# Changelog", "", heading, ""]
    for category in CATEGORY_ORDER:
        lines.extend([f"### {category}", ""])
        lines.extend(grouped.get(category, ["- No changes."]))
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits after the latest git tag")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--since-tag", help="override the automatically detected latest tag")
    parser.add_argument("--version", default="Unreleased")
    parser.add_argument("--date", dest="release_date")
    parser.add_argument("-o", "--output", type=Path, help="write to this path; otherwise print to stdout")
    args = parser.parse_args(argv)

    try:
        _boundary, raw_commits = get_commits(args.repo.resolve(), args.since_tag)
    except GitError as exc:
        print(f"generate-changelog: {exc}", file=sys.stderr)
        return 2
    content = render([parse_commit(*item) for item in raw_commits], args.version, args.release_date)
    if args.output:
        output = args.output if args.output.is_absolute() else args.repo / args.output
        output.write_text(content, encoding="utf-8")
        print(f"Wrote {output}")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
