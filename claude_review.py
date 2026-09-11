#!/usr/bin/env python3
"""Produce a deterministic, structured first-pass review for a GitHub PR."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PR_PATTERN = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?$")


@dataclass(frozen=True)
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    state: str
    draft: bool
    additions: int
    deletions: int
    changed_files: int
    mergeable: bool | None
    files: tuple[dict, ...]


def parse_pr_url(value: str) -> tuple[str, str, int]:
    match = PR_PATTERN.match(value.rstrip("/"))
    if not match:
        raise ValueError("expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))


def github_get(path: str) -> dict | list:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review-bounty",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError) as error:
        if isinstance(error, HTTPError) and error.code == 404:
            raise RuntimeError("GitHub PR not found or not publicly readable") from error
        if isinstance(error, HTTPError) and error.code == 403:
            raise RuntimeError("GitHub API rate limit reached; set GITHUB_TOKEN and retry") from error
        raise RuntimeError(f"GitHub API request failed: {error}") from error


def load_pr(owner: str, repo: str, number: int) -> PullRequest:
    base = f"/repos/{owner}/{repo}/pulls/{number}"
    data = github_get(base)
    files = github_get(f"{base}/files?per_page=100")
    if not isinstance(data, dict) or not isinstance(files, list):
        raise RuntimeError("GitHub returned an unexpected response")
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=data.get("title", "Untitled PR").strip(),
        body=(data.get("body") or "").strip(),
        state=data.get("state", "unknown"),
        draft=bool(data.get("draft")),
        additions=int(data.get("additions", 0)),
        deletions=int(data.get("deletions", 0)),
        changed_files=int(data.get("changed_files", len(files))),
        mergeable=data.get("mergeable"),
        files=tuple(file for file in files if isinstance(file, dict)),
    )


def file_names(pr: PullRequest) -> list[str]:
    return [str(file.get("filename", "")) for file in pr.files]


def summary(pr: PullRequest) -> str:
    scope = f"{pr.changed_files} file(s), +{pr.additions}/-{pr.deletions} lines"
    state = "draft" if pr.draft else pr.state
    first = f"{pr.title} changes {scope} and is currently {state}."
    if pr.files:
        names = file_names(pr)
        preview = ", ".join(names[:3])
        if len(names) > 3:
            preview += ", and more"
        second = f"The touched paths include {preview}."
    else:
        second = "No changed-file metadata was returned by GitHub."
    return f"{first} {second}"


def risks(pr: PullRequest) -> list[str]:
    names = file_names(pr)
    lowered = [name.lower() for name in names]
    findings: list[str] = []

    if pr.changed_files == 0:
        findings.append("The pull request has no changed files to review.")
    if pr.additions + pr.deletions > 800:
        findings.append("The diff is large enough to make review and regression isolation difficult.")
    if any("migration" in name or name.endswith((".sql", ".prisma")) for name in lowered):
        findings.append("Database or migration files changed; backwards compatibility and rollback behavior need explicit verification.")
    if any(name.endswith((".yml", ".yaml")) or "/workflows/" in name for name in lowered):
        findings.append("Automation configuration changed; review permissions, untrusted input handling, and secret exposure.")
    if any(part in name for name in lowered for part in ("auth", "permission", "security", "token", "credential")):
        findings.append("Security-sensitive paths changed; verify authorization boundaries and negative cases.")
    if any(name.endswith(("package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "requirements.txt", "pyproject.toml")) for name in lowered):
        findings.append("Dependency metadata changed; check lockfile integrity and transitive-version impact.")

    has_tests = any(any(marker in name for marker in ("test", "spec", "__tests__")) for name in lowered)
    if not has_tests and pr.changed_files:
        findings.append("No test path is present in the changed-file list; behavior changes may lack regression coverage.")
    if pr.mergeable is False:
        findings.append("GitHub currently reports the pull request as not mergeable; resolve conflicts before approval.")
    if not findings:
        findings.append("No high-signal risk was detected by the static first-pass checks; maintainers should still review behavior and tests.")
    return findings


def suggestions(pr: PullRequest) -> list[str]:
    names = [name.lower() for name in file_names(pr)]
    result: list[str] = []
    if pr.changed_files and not any(any(marker in name for marker in ("test", "spec", "__tests__")) for name in names):
        result.append("Add focused regression tests for the changed behavior, including at least one failure or boundary case.")
    if pr.additions + pr.deletions > 800:
        result.append("Consider splitting the diff into smaller reviewable changes.")
    if not pr.body:
        result.append("Add a short problem statement, validation steps, and any rollout or compatibility notes to the PR description.")
    else:
        result.append("Keep the PR description synchronized with the tested commands and observable behavior.")
    result.append("Run the repository's formatter, linter, and test suite before merge.")
    return result


def confidence(pr: PullRequest) -> str:
    size = pr.additions + pr.deletions
    has_tests = any(any(marker in name.lower() for marker in ("test", "spec", "__tests__")) for name in file_names(pr))
    if pr.mergeable is False or size > 1500:
        return "Low"
    if has_tests and size <= 500:
        return "High"
    return "Medium"


def render(pr: PullRequest) -> str:
    risk_lines = "\n".join(f"- {item}" for item in risks(pr))
    suggestion_lines = "\n".join(f"- {item}" for item in suggestions(pr))
    url = f"https://github.com/{pr.owner}/{pr.repo}/pull/{pr.number}"
    return (
        f"# PR Review: {pr.title}\n\n"
        f"**Pull request:** {url}\n\n"
        "## Summary\n\n"
        f"{summary(pr)}\n\n"
        "## Identified risks\n\n"
        f"{risk_lines}\n\n"
        "## Improvement suggestions\n\n"
        f"{suggestion_lines}\n\n"
        "## Confidence\n\n"
        f"**{confidence(pr)}**\n"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub pull request and print structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    args = parser.parse_args(argv)
    try:
        owner, repo, number = parse_pr_url(args.pr)
        print(render(load_pr(owner, repo, number)))
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
