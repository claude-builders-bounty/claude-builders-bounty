#!/usr/bin/env python3
"""Generate a structured changelog from local git or GitHub commits."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str = ""
    author: str = ""
    url: str = ""


def run_git(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("git was not found. Use --repo owner/name for GitHub API mode.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "git command failed"
        raise SystemExit(detail) from exc
    return completed.stdout.rstrip("\r\n")


def latest_local_tag() -> str | None:
    try:
        return run_git(["describe", "--tags", "--abbrev=0", "HEAD"])
    except SystemExit:
        return None


def local_commits(since_tag: str | None, max_commits: int) -> list[Commit]:
    revision_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
    fmt = "%H%x1f%an%x1f%s%x1f%b%x1e"
    output = run_git(["log", "--no-merges", revision_range, f"--pretty=format:{fmt}"])
    commits: list[Commit] = []
    for raw in output.split("\x1e"):
        raw = raw.strip("\r\n")
        if not raw:
            continue
        parts = raw.split("\x1f", 3)
        if len(parts) != 4:
            continue
        sha, author, subject, body = parts
        commits.append(Commit(sha=sha, author=author, subject=subject, body=body))
    return commits[:max_commits]


def parse_github_repo(value: str) -> tuple[str, str]:
    if re.fullmatch(r"[\w.-]+/[\w.-]+", value):
        owner, repo = value.split("/", 1)
        return owner, repo.removesuffix(".git")

    match = re.search(r"github\.com[:/]([^/\s]+)/([^/\s#?]+)", value)
    if not match:
        raise SystemExit("--repo must be owner/name or a GitHub repository URL")
    owner, repo = match.groups()
    return owner, repo.removesuffix(".git")


def github_json(path: str, token: str | None = None) -> object:
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-builders-generate-changelog",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if os.name == "nt":
        return powershell_json(url, headers)

    return urllib_json(url, headers)


def powershell_json(url: str, headers: dict[str, str]) -> object:
    script = r"""
$ErrorActionPreference = 'Stop'
$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
$requestHeaders = @{}
$payload.headers.PSObject.Properties | ForEach-Object {
  $requestHeaders[$_.Name] = [string]$_.Value
}
Invoke-RestMethod -Uri $payload.url -Headers $requestHeaders -TimeoutSec 30 | ConvertTo-Json -Depth 100
"""
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        input=json.dumps({"url": url, "headers": headers}),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SystemExit(f"GitHub API request failed: {detail}")
    return json.loads(completed.stdout)


def urllib_json(url: str, headers: dict[str, str]) -> object:
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub API request failed ({exc.code}): {message}") from exc


def github_default_branch(owner: str, repo: str, token: str | None) -> str:
    payload = github_json(f"/repos/{owner}/{repo}", token)
    if not isinstance(payload, dict) or not payload.get("default_branch"):
        raise SystemExit("GitHub API response did not include a default branch")
    return str(payload["default_branch"])


def latest_github_tag(owner: str, repo: str, token: str | None) -> str | None:
    payload = github_json(f"/repos/{owner}/{repo}/tags?per_page=1", token)
    if isinstance(payload, list) and payload:
        name = payload[0].get("name")
        return str(name) if name else None
    return None


def github_commits(
    owner: str,
    repo: str,
    since_tag: str | None,
    max_commits: int,
    token: str | None,
    head_ref: str | None = None,
) -> list[Commit]:
    if since_tag:
        encoded_tag = quote(since_tag, safe="")
        branch = head_ref or github_default_branch(owner, repo, token)
        encoded_branch = quote(branch, safe="")
        payload = github_json(
            f"/repos/{owner}/{repo}/compare/{encoded_tag}...{encoded_branch}",
            token,
        )
        raw_commits = payload.get("commits", []) if isinstance(payload, dict) else []
    else:
        query = f"?per_page={min(max_commits, 100)}"
        if head_ref:
            query += f"&sha={quote(head_ref, safe='')}"
        payload = github_json(f"/repos/{owner}/{repo}/commits{query}", token)
        raw_commits = payload if isinstance(payload, list) else []

    commits: list[Commit] = []
    for item in reversed(raw_commits):
        if not isinstance(item, dict):
            continue
        commit = item.get("commit", {})
        if not isinstance(commit, dict):
            continue
        message = str(commit.get("message", "")).strip()
        subject, _, body = message.partition("\n")
        if subject.lower().startswith("merge "):
            continue
        commit_author = commit.get("author", {})
        author = commit_author.get("name", "") if isinstance(commit_author, dict) else ""
        commits.append(
            Commit(
                sha=str(item.get("sha", "")),
                author=str(author),
                subject=subject.strip(),
                body=body.strip(),
                url=str(item.get("html_url", "")),
            )
        )
    return commits[:max_commits]


def classify_commit(commit: Commit) -> str:
    text = f"{commit.subject}\n{commit.body}".lower()
    subject = commit.subject.lower().strip()

    if re.match(r"^(feat|feature)(\(.+\))?!?:", subject):
        return "Added"
    if re.match(r"^(fix|bugfix|security)(\(.+\))?!?:", subject):
        return "Fixed"
    if re.match(r"^(remove|removed|delete|drop|deprecate)(\(.+\))?!?:", subject):
        return "Removed"

    if re.search(r"\b(add|adds|added|create|creates|created|introduce|introduces)\b", text):
        return "Added"
    if re.search(r"\b(fix|fixes|fixed|repair|repairs|prevent|prevents|correct|corrects)\b", text):
        return "Fixed"
    if re.search(r"\b(remove|removes|removed|delete|deletes|deleted|drop|drops|dropped|deprecate|deprecated)\b", text):
        return "Removed"
    return "Changed"


def format_commit(commit: Commit) -> str:
    subject = commit.subject.rstrip(".")
    short_sha = commit.sha[:7]
    suffix = f" ({short_sha})" if short_sha else ""
    if commit.url and short_sha:
        suffix = f" ([{short_sha}]({commit.url}))"
    if commit.author:
        suffix += f" by {commit.author}"
    return f"- {subject}{suffix}"


def render_changelog(commits: Iterable[Commit], since_tag: str | None, source: str) -> str:
    grouped: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped[classify_commit(commit)].append(format_commit(commit))

    today = date.today().isoformat()
    base = f" since `{since_tag}`" if since_tag else ""
    lines = [
        "# Changelog",
        "",
        f"## Unreleased - {today}",
        "",
        f"Generated from `{source}`{base}.",
        "",
    ]

    if not any(grouped.values()):
        lines.extend(["No commits found for this range.", ""])
        return "\n".join(lines)

    for category in CATEGORIES:
        if not grouped[category]:
            continue
        lines.extend([f"### {category}", "", *grouped[category], ""])
    return "\n".join(lines).rstrip() + "\n"


def build_changelog(args: argparse.Namespace) -> str:
    if args.repo:
        owner, repo = parse_github_repo(args.repo)
        since_tag = args.since_tag or latest_github_tag(owner, repo, args.token)
        head_ref = github_default_branch(owner, repo, args.token)
        commits = github_commits(
            owner,
            repo,
            since_tag,
            args.max_commits,
            args.token,
            head_ref=head_ref,
        )
        return render_changelog(commits, since_tag, f"github.com/{owner}/{repo}")

    since_tag = args.since_tag or latest_local_tag()
    commits = local_commits(since_tag, args.max_commits)
    root = run_git(["rev-parse", "--show-toplevel"])
    return render_changelog(commits, since_tag, root)


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from commits since the latest tag.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Path to write. Defaults to CHANGELOG.md.")
    parser.add_argument("--repo", help="GitHub owner/name or URL. Uses the GitHub API instead of local git.")
    parser.add_argument("--since-tag", help="Tag to compare from. Auto-detects the latest tag when omitted.")
    parser.add_argument("--max-commits", type=positive_int, default=100, help="Maximum commits to include.")
    parser.add_argument("--dry-run", action="store_true", help="Print the changelog instead of writing a file.")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token for API mode.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    changelog = build_changelog(args)
    if args.dry_run:
        print(changelog, end="")
        return 0

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(changelog, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
