#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

This is intentionally dependency-free so it works in fresh Claude Code sessions,
CI jobs, and small open-source repositories without setup friction.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence


CATEGORY_ORDER = ["Breaking Changes", "Added", "Fixed", "Changed", "Removed"]
TYPE_TO_CATEGORY = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "perf": "Fixed",
    "refactor": "Changed",
    "docs": "Changed",
    "doc": "Changed",
    "style": "Changed",
    "test": "Changed",
    "tests": "Changed",
    "build": "Changed",
    "ci": "Changed",
    "chore": "Changed",
    "revert": "Changed",
    "remove": "Removed",
    "removed": "Removed",
    "delete": "Removed",
}
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<summary>.+)$"
)
PR_RE = re.compile(r"\(#(?P<number>\d+)\)\s*$")
BREAKING_RE = re.compile(r"(^|\n)BREAKING[ -]CHANGE:\s*(?P<text>.+)", re.IGNORECASE | re.DOTALL)


@dataclasses.dataclass(frozen=True)
class CommitEntry:
    category: str
    scope: str
    summary: str
    breaking: bool = False
    breaking_note: str = ""
    pr_number: str | None = None
    sha: str = ""
    author: str = ""
    date: str = ""
    subject: str = ""
    body: str = ""

    def with_metadata(self, *, sha: str, author: str, date: str, body: str = "") -> "CommitEntry":
        return dataclasses.replace(self, sha=sha, author=author, date=date, body=body)


@dataclasses.dataclass(frozen=True)
class Changelog:
    version: str
    date: str
    compare_url: str | None
    commits: Sequence[CommitEntry]
    repo_name: str


def run_git(repo_path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.rstrip("\n")


def latest_tag(repo_path: Path) -> str | None:
    try:
        return run_git(repo_path, "describe", "--tags", "--abbrev=0")
    except subprocess.CalledProcessError:
        return None


def repo_remote_url(repo_path: Path) -> str | None:
    try:
        return run_git(repo_path, "config", "--get", "remote.origin.url") or None
    except subprocess.CalledProcessError:
        return None


def github_web_url(remote_url: str | None) -> str | None:
    if not remote_url:
        return None
    remote_url = remote_url.strip()
    if remote_url.startswith("git@github.com:"):
        slug = remote_url.removeprefix("git@github.com:").removesuffix(".git")
        return f"https://github.com/{slug}"
    match = re.match(r"https://github\.com/(?P<slug>[^/]+/[^/.]+)(?:\.git)?$", remote_url)
    if match:
        return f"https://github.com/{match.group('slug')}"
    return None


def build_compare_url(repo_path: Path, tag: str | None) -> str | None:
    web_url = github_web_url(repo_remote_url(repo_path))
    if not web_url or not tag:
        return None
    return f"{web_url}/compare/{tag}...HEAD"


def categorize_commit(subject: str, body: str = "") -> CommitEntry:
    original_subject = subject.strip()
    cleaned_subject = original_subject
    pr_number = None
    pr_match = PR_RE.search(cleaned_subject)
    if pr_match:
        pr_number = pr_match.group("number")
        cleaned_subject = PR_RE.sub("", cleaned_subject).strip()

    match = CONVENTIONAL_RE.match(cleaned_subject)
    breaking_note = ""
    body_breaking = BREAKING_RE.search(body or "")
    if body_breaking:
        breaking_note = " ".join(body_breaking.group("text").split())

    if match:
        commit_type = match.group("type").lower()
        scope = (match.group("scope") or "general").strip()
        summary = match.group("summary").strip()
        breaking = bool(match.group("bang")) or bool(body_breaking)
        category = TYPE_TO_CATEGORY.get(commit_type, "Changed")
        lowered_summary = summary.lower()
        if any(word in lowered_summary for word in ["remove", "delete", "drop"]):
            category = "Removed"
    else:
        lowered = cleaned_subject.lower()
        scope = "general"
        summary = cleaned_subject
        breaking = bool(body_breaking)
        if any(word in lowered for word in ["remove", "delete", "drop"]):
            category = "Removed"
        elif any(word in lowered for word in ["fix", "bug", "patch", "repair"]):
            category = "Fixed"
        elif any(word in lowered for word in ["add", "new", "introduce", "create"]):
            category = "Added"
        else:
            category = "Changed"

    if breaking:
        category = "Changed"

    return CommitEntry(
        category=category,
        scope=scope or "general",
        summary=summary,
        breaking=breaking,
        breaking_note=breaking_note,
        pr_number=pr_number,
        subject=original_subject,
        body=body or "",
    )


def collect_commits(repo_path: Path, since_ref: str | None = None) -> list[CommitEntry]:
    since_ref = since_ref if since_ref is not None else latest_tag(repo_path)
    revision_range = f"{since_ref}..HEAD" if since_ref else "HEAD"
    delimiter = "\x1f"
    record_separator = "\x1e"
    # Use git's %xNN escapes instead of literal control characters in argv.
    # This keeps the command portable across git builds and shells.
    pretty = "%H%x1f%h%x1f%an%x1f%ad%x1f%s%x1f%b%x1e"
    raw = run_git(repo_path, "log", revision_range, "--date=short", f"--pretty=format:{pretty}")
    commits: list[CommitEntry] = []
    for record in raw.split(record_separator):
        record = record.strip("\n\r ")
        if not record:
            continue
        parts = record.split(delimiter, 5)
        if len(parts) < 6:
            continue
        full_sha, short_sha, author, date, subject, body = parts
        entry = categorize_commit(subject, body).with_metadata(
            sha=short_sha,
            author=author,
            date=date,
            body=body,
        )
        commits.append(entry)
    return commits


def generate_changelog(
    repo_path: Path,
    commits: Sequence[CommitEntry] | None = None,
    *,
    version: str = "Unreleased",
    compare_url: str | None = None,
    since_ref: str | None = None,
) -> Changelog:
    repo_path = repo_path.resolve()
    discovered_tag = since_ref if since_ref is not None else latest_tag(repo_path)
    entries = list(commits) if commits is not None else collect_commits(repo_path, discovered_tag)
    return Changelog(
        version=version,
        date=_dt.date.today().isoformat(),
        compare_url=compare_url if compare_url is not None else build_compare_url(repo_path, discovered_tag),
        commits=entries,
        repo_name=repo_path.name,
    )


def pr_url(repo_url: str | None, pr_number: str | None) -> str | None:
    if not repo_url or not pr_number:
        return None
    return f"{repo_url}/pull/{pr_number}"


def commit_url(repo_url: str | None, sha: str) -> str | None:
    if not repo_url or not sha:
        return None
    return f"{repo_url}/commit/{sha}"


def render_changelog(changelog: Changelog, repo_url: str | None = None) -> str:
    if repo_url is None:
        repo_url = github_web_url(repo_remote_url(Path.cwd()))

    lines = ["# Changelog", "", "All notable changes are generated from git history.", ""]
    heading = f"## [{changelog.version}] - {changelog.date}"
    lines.extend([heading, ""])
    if changelog.compare_url:
        lines.extend([f"[Compare changes]({changelog.compare_url})", ""])

    if not changelog.commits:
        lines.extend(["No commits found for this range.", ""])
    else:
        breaking_entries = [entry for entry in changelog.commits if entry.breaking]
        if breaking_entries:
            lines.extend(["### Breaking Changes", ""])
            for entry in breaking_entries:
                lines.append(f"- {format_entry(entry, repo_url)}")
                if entry.breaking_note:
                    lines.append(f"  - Migration note: {entry.breaking_note}")
            lines.append("")

        grouped = group_commits(changelog.commits)
        for category in CATEGORY_ORDER[1:]:
            entries_by_scope = grouped.get(category)
            if not entries_by_scope:
                continue
            lines.extend([f"### {category}", ""])
            for scope in sorted(entries_by_scope):
                for entry in entries_by_scope[scope]:
                    lines.append(f"- {format_entry(entry, repo_url)}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Generated by `tools/changelog_generator.py` from git history._")
    return "\n".join(lines).rstrip() + "\n"


def group_commits(commits: Iterable[CommitEntry]) -> dict[str, dict[str, list[CommitEntry]]]:
    grouped: dict[str, dict[str, list[CommitEntry]]] = defaultdict(lambda: defaultdict(list))
    for entry in commits:
        grouped[entry.category][entry.scope].append(entry)
    return grouped


def format_entry(entry: CommitEntry, repo_url: str | None) -> str:
    scope_prefix = f"**{entry.scope}**: " if entry.scope and entry.scope != "general" else ""
    refs = []
    pull_url = pr_url(repo_url, entry.pr_number)
    if pull_url:
        refs.append(f"[#{entry.pr_number}]({pull_url})")
    elif entry.pr_number:
        refs.append(f"#{entry.pr_number}")

    sha_link = commit_url(repo_url, entry.sha)
    if sha_link:
        refs.append(f"[`{entry.sha}`]({sha_link})")
    elif entry.sha:
        refs.append(f"`{entry.sha}`")

    if entry.author:
        refs.append(f"by {entry.author}")

    suffix = f" ({', '.join(refs)})" if refs else ""
    marker = "**BREAKING**: " if entry.breaking else ""
    return f"{marker}{scope_prefix}{entry.summary}{suffix}"


def write_changelog(repo_path: Path, output: Path, version: str, since_ref: str | None) -> Path:
    changelog = generate_changelog(repo_path, version=version, since_ref=since_ref)
    repo_url = github_web_url(repo_remote_url(repo_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_changelog(changelog, repo_url=repo_url), encoding="utf-8")
    return output


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Path to the git repository. Default: current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output markdown path. Default: CHANGELOG.md.")
    parser.add_argument("--version", default="Unreleased", help="Version heading to write. Default: Unreleased.")
    parser.add_argument("--since", default=None, help="Git ref/tag to start from. Default: latest tag, or all history if no tag exists.")
    parser.add_argument("--stdout", action="store_true", help="Print changelog instead of writing a file.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_path = Path(args.repo).resolve()
    if args.stdout:
        changelog = generate_changelog(repo_path, version=args.version, since_ref=args.since)
        print(render_changelog(changelog, repo_url=github_web_url(repo_remote_url(repo_path))), end="")
        return 0
    output = Path(args.output)
    if not output.is_absolute():
        output = repo_path / output
    write_changelog(repo_path, output, args.version, args.since)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
