#!/usr/bin/env python3
"""Generate a Keep a Changelog-style Unreleased section from Git history."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


CATEGORY_ORDER = ("Added", "Fixed", "Changed", "Removed")
TICK = chr(96)
CONVENTIONAL_SUBJECT = re.compile(
    r"^(?P<kind>[a-z][a-z0-9_-]*)(?:\([^)]*\))?(?P<breaking>!)?:\s*(?P<summary>.+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str


def _git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Git was not found on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or "Git could not read this repository.") from exc


def _repository_root(path: Path) -> Path:
    result = _git(path, "rev-parse", "--show-toplevel")
    return Path(result.stdout.decode("utf-8", errors="strict").strip())


def _last_reachable_tag(repo: Path) -> str | None:
    result = _git(repo, "describe", "--tags", "--abbrev=0", "HEAD", check=False)
    if result.returncode:
        return None
    tag = result.stdout.decode("utf-8", errors="replace").strip()
    return tag or None


def _commits_since_tag(repo: Path, tag: str | None) -> list[Commit]:
    revision = f"{tag}..HEAD" if tag else "HEAD"
    result = _git(
        repo,
        "log",
        "--no-merges",
        "--reverse",
        "--format=%H%x09%s",
        "-z",
        revision,
    )
    commits: list[Commit] = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        sha, separator, subject = record.partition(b"\t")
        if not separator:
            raise RuntimeError("Git returned a commit without a subject separator.")
        commits.append(
            Commit(
                sha.decode("ascii", errors="replace"),
                subject.decode("utf-8", errors="replace").strip(),
            )
        )
    return commits


def _classify(subject: str) -> tuple[str, str]:
    """Return the changelog section and concise human-readable subject."""
    conventional = CONVENTIONAL_SUBJECT.match(subject.strip())
    kind = conventional.group("kind").lower() if conventional else ""
    description = (
        conventional.group("summary").strip() if conventional else subject.strip()
    )
    first_word = (
        description.split(maxsplit=1)[0].rstrip(":,").lower() if description else ""
    )

    if kind in {
        "remove",
        "removed",
        "delete",
        "deleted",
        "drop",
        "deprecate",
    } or first_word in {
        "remove",
        "removed",
        "delete",
        "deleted",
        "drop",
        "deprecate",
        "deprecated",
    }:
        return "Removed", description
    if conventional and conventional.group("breaking"):
        return "Changed", description
    if kind in {"feat", "feature", "add", "added"} or first_word in {
        "add",
        "added",
        "introduce",
        "introduced",
        "new",
    }:
        return "Added", description
    if kind in {"fix", "bug", "bugfix", "patch", "resolve"} or first_word in {
        "fix",
        "fixed",
        "resolve",
        "resolved",
        "repair",
        "repaired",
    }:
        return "Fixed", description
    return "Changed", description


def _escape_markdown(value: str) -> str:
    special = set("\\*_{}[]()#+.!|>~" + TICK)
    escaped: list[str] = []
    for char in value.replace("\r", " ").replace("\n", " ").strip():
        safe = html.escape(char, quote=False)
        escaped.append("\\" + safe if char in special else safe)
    return "".join(escaped)


def generate_changelog(repo_path: Path) -> str:
    repo = _repository_root(repo_path.expanduser().resolve())
    tag = _last_reachable_tag(repo)
    commits = _commits_since_tag(repo, tag)
    sections: dict[str, list[str]] = {category: [] for category in CATEGORY_ORDER}
    for commit in commits:
        category, description = _classify(commit.subject)
        label = _escape_markdown(description)
        sections[category].append(f"- {label} ({TICK}{commit.sha[:12]}{TICK})")

    lines = [
        "# Changelog",
        "",
        "Notable changes are grouped by commit subject since the latest reachable Git tag.",
        "",
        "## [Unreleased]",
        "",
    ]
    if not commits:
        lines.extend(
            ["_No non-merge commits found since the latest reachable tag._", ""]
        )
    else:
        for category in CATEGORY_ORDER:
            entries = sections[category]
            if entries:
                lines.extend([f"### {category}", "", *entries, ""])
    return "\n".join(lines)


def _write_output(path: Path, content: str, *, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise RuntimeError(f"{path} already exists; pass --force to replace it.")
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a categorized CHANGELOG.md section from local Git history."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Git repository (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Output path relative to the repository",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the generated Markdown instead of writing a file",
    )
    parser.add_argument(
        "--force", action="store_true", help="Replace an existing output file"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repo = _repository_root(args.repo.expanduser().resolve())
        content = generate_changelog(repo)
        if args.stdout:
            sys.stdout.write(content)
            return 0
        output = args.output.expanduser()
        if not output.is_absolute():
            output = repo / output
        _write_output(output, content, force=args.force)
        print(f"Generated {output}")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"generate-changelog: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
