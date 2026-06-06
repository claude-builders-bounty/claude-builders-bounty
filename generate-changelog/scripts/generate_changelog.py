#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SECTIONS = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str = ""
    date: str = ""
    url: str | None = None


@dataclass(frozen=True)
class CommitSet:
    commits: list[Commit]
    since_ref: str | None
    source: str
    note: str | None = None


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest tag.")
    parser.add_argument("--repo", help="GitHub repository in owner/name form. Uses GitHub API instead of local git.")
    parser.add_argument("--cwd", default=".", help="Local git repository path. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path. Defaults to CHANGELOG.md.")
    parser.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing a file.")
    parser.add_argument("--version", default="Unreleased", help="Version heading to write. Defaults to Unreleased.")
    parser.add_argument("--title", default="Changelog", help="Top-level changelog title.")
    parser.add_argument("--max-pages", type=int, default=5, help="GitHub API commit pages to scan before stopping.")
    parser.add_argument("--no-sha", action="store_true", help="Do not include short commit hashes in bullets.")
    args = parser.parse_args()

    try:
        commit_set = load_github_commits(args.repo, args.max_pages) if args.repo else load_local_commits(Path(args.cwd))
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    changelog = render_changelog(
        commit_set=commit_set,
        title=args.title,
        version=args.version,
        include_sha=not args.no_sha,
    )

    if args.dry_run:
        print(changelog)
    else:
        output_path = Path(args.output)
        output_path.write_text(changelog, encoding="utf-8")
        print(f"Wrote {output_path}")

    return 0


def load_local_commits(cwd: Path) -> CommitSet:
    if not cwd.exists():
        raise RuntimeError(f"repository path does not exist: {cwd}")

    last_tag = run_git(["describe", "--tags", "--abbrev=0"], cwd, allow_failure=True)
    last_tag = last_tag.strip() or None
    revision = f"{last_tag}..HEAD" if last_tag else "HEAD"
    raw_log = run_git(
        [
            "log",
            revision,
            "--date=short",
            "--pretty=format:%H%x1f%ad%x1f%s%x1f%b%x1e",
        ],
        cwd,
    )

    commits: list[Commit] = []
    for entry in raw_log.strip("\x1e\n").split("\x1e"):
        if not entry.strip():
            continue
        parts = entry.strip().split("\x1f", 3)
        if len(parts) < 3:
            continue
        sha, date, subject = parts[:3]
        body = parts[3] if len(parts) == 4 else ""
        commits.append(Commit(sha=sha, subject=subject.strip(), body=body.strip(), date=date.strip()))

    return CommitSet(commits=commits, since_ref=last_tag, source=str(cwd.resolve()))


def run_git(args: list[str], cwd: Path, allow_failure: bool = False) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=not allow_failure,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git is not available; use --repo owner/name for GitHub API mode") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or "git command failed") from exc

    if result.returncode != 0 and allow_failure:
        return ""
    return result.stdout


def load_github_commits(repo: str, max_pages: int) -> CommitSet:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo or ""):
        raise RuntimeError("--repo must be in owner/name form")

    tags = github_json(f"/repos/{repo}/tags?per_page=1")
    latest_tag = tags[0] if tags else None
    stop_sha = latest_tag.get("commit", {}).get("sha") if latest_tag else None
    since_ref = latest_tag.get("name") if latest_tag else None

    commits: list[Commit] = []
    reached_tag = False
    for page in range(1, max_pages + 1):
        page_commits = github_json(f"/repos/{repo}/commits?per_page=100&page={page}")
        if not page_commits:
            break
        for item in page_commits:
            sha = item["sha"]
            if stop_sha and sha == stop_sha:
                reached_tag = True
                break
            message = item["commit"]["message"]
            subject, _, body = message.partition("\n")
            commits.append(
                Commit(
                    sha=sha,
                    subject=subject.strip(),
                    body=body.strip(),
                    date=item["commit"]["author"]["date"][:10],
                    url=item.get("html_url"),
                )
            )
        if reached_tag:
            break

    note = None
    if stop_sha and not reached_tag:
        note = f"Latest tag {since_ref} was not reached within {max_pages} GitHub API page(s); output uses scanned commits."
    if not latest_tag:
        note = "No tags found; output uses recent commits from the default branch."

    return CommitSet(commits=commits, since_ref=since_ref, source=f"https://github.com/{repo}", note=note)


def github_json(path: str):
    token = os.environ.get("GITHUB_TOKEN")
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "generate-changelog-skill",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API request failed: {exc.reason}") from exc


def render_changelog(commit_set: CommitSet, title: str, version: str, include_sha: bool) -> str:
    today = dt.date.today().isoformat()
    grouped = {section: [] for section in SECTIONS}
    for commit in commit_set.commits:
        grouped[categorize(commit.subject)].append(format_bullet(commit, include_sha))

    lines = [
        f"# {title}",
        "",
        "All notable changes are documented in this file.",
        "",
        f"## [{version}] - {today}",
        "",
    ]
    if commit_set.since_ref:
        lines.extend([f"_Generated from commits after `{commit_set.since_ref}` in {commit_set.source}._", ""])
    else:
        lines.extend([f"_Generated from commits in {commit_set.source}._", ""])
    if commit_set.note:
        lines.extend([f"_Note: {commit_set.note}_", ""])

    wrote_section = False
    for section in SECTIONS:
        bullets = unique(grouped[section])
        if not bullets:
            continue
        wrote_section = True
        lines.extend([f"### {section}", ""])
        lines.extend(bullets)
        lines.append("")

    if not wrote_section:
        lines.extend(["No changes found.", ""])

    return "\n".join(lines).rstrip() + "\n"


def categorize(subject: str) -> str:
    normalized = subject.strip().lower()
    commit_type = conventional_type(normalized)
    head = strip_conventional_prefix(normalized)

    if commit_type in {"feat", "feature", "add"} or starts_with_any(head, ("add ", "adds ", "create ", "implement ", "introduce ", "support ")):
        return "Added"
    if commit_type in {"fix", "bugfix", "hotfix"} or starts_with_any(head, ("fix ", "fixes ", "resolve ", "patch ")):
        return "Fixed"
    if commit_type in {"remove", "delete", "drop", "deprecate"} or starts_with_any(head, ("remove ", "delete ", "drop ", "deprecate ")):
        return "Removed"
    return "Changed"


def conventional_type(subject: str) -> str | None:
    match = re.match(r"^([a-zA-Z]+)(?:\([^)]+\))?!?:\s+", subject)
    return match.group(1).lower() if match else None


def strip_conventional_prefix(subject: str) -> str:
    return re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s+", "", subject).strip()


def starts_with_any(value: str, prefixes: Iterable[str]) -> bool:
    return any(value.startswith(prefix) for prefix in prefixes)


def format_bullet(commit: Commit, include_sha: bool) -> str:
    subject = strip_conventional_prefix(commit.subject).strip()
    subject = subject[:1].upper() + subject[1:] if subject else commit.subject
    subject = subject.rstrip(".")
    if not include_sha:
        return f"- {subject}"
    short_sha = commit.sha[:7]
    if commit.url:
        return f"- {subject} ([{short_sha}]({commit.url}))"
    return f"- {subject} ({short_sha})"


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
