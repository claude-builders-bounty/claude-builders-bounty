#!/usr/bin/env python3
"""Fetch a GitHub PR diff and emit a structured Markdown review."""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")


@dataclass
class DiffStats:
    files: set[str]
    additions: int
    deletions: int
    added_lines: list[str]
    deleted_lines: list[str]


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("expected PR URL like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)


def fetch_diff(owner: str, repo: str, number: str) -> str:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
        headers={
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "claude-pr-review-agent",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not fetch PR diff: {exc.reason}") from exc


def diff_stats(diff: str) -> DiffStats:
    files: set[str] = set()
    added_lines: list[str] = []
    deleted_lines: list[str] = []

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.add(parts[3].removeprefix("b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            deleted_lines.append(line[1:])

    return DiffStats(
        files=files,
        additions=len(added_lines),
        deletions=len(deleted_lines),
        added_lines=added_lines,
        deleted_lines=deleted_lines,
    )


def detect_risks(stats: DiffStats) -> list[str]:
    risks: list[str] = []
    changed = "\n".join(stats.added_lines).lower()
    paths = " ".join(stats.files).lower()

    if stats.additions + stats.deletions > 500:
        risks.append("Large diff size may make behavioral regressions harder to spot.")
    if any(path.endswith((".yml", ".yaml")) and ".github/workflows/" in path for path in stats.files):
        risks.append("Workflow changes can affect CI permissions, secrets, or release behavior.")
    if re.search(r"\b(secret|token|password|api[_-]?key)\b", changed):
        risks.append("Added code references sensitive credential terms; verify no secrets are logged or committed.")
    if re.search(r"\brm\s+-rf\b|\bgit\s+push\s+--force\b|\bdrop\s+table\b", changed):
        risks.append("Added command text includes destructive operations; verify guardrails and tests.")
    if "test" not in paths and stats.additions > 25:
        risks.append("No obvious test files changed, so runtime behavior may be under-verified.")

    if not risks:
        risks.append("No major risk signals detected from the diff structure.")

    return risks


def suggestions(stats: DiffStats) -> list[str]:
    ideas: list[str] = []
    paths = " ".join(stats.files).lower()

    if "readme" not in paths and stats.additions > 25:
        ideas.append("Add or update README usage notes if this introduces user-facing behavior.")
    if "test" not in paths:
        ideas.append("Add focused tests or paste a reproducible manual verification transcript.")
    if stats.additions + stats.deletions > 300:
        ideas.append("Consider splitting follow-up cleanup from the functional change.")

    if not ideas:
        ideas.append("Keep the PR focused and include the verification commands in the final review thread.")

    return ideas


def confidence(stats: DiffStats) -> str:
    total = stats.additions + stats.deletions
    paths = " ".join(stats.files).lower()
    has_tests = "test" in paths

    if has_tests and total <= 250:
        return "High"
    if total <= 500:
        return "Medium"
    return "Low"


def bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def render_review(pr_url: str, stats: DiffStats) -> str:
    file_count = len(stats.files)
    summary = (
        f"This PR changes {file_count} file{'s' if file_count != 1 else ''} "
        f"with {stats.additions} additions and {stats.deletions} deletions. "
        "The diff appears focused on "
        + (", ".join(sorted(stats.files)[:3]) if stats.files else "repository metadata")
        + "."
    )

    return "\n".join(
        [
            "## Claude PR Review",
            "",
            "### Summary of Changes",
            summary,
            "",
            "### Identified Risks",
            bullets(detect_risks(stats)),
            "",
            "### Improvement Suggestions",
            bullets(suggestions(stats)),
            "",
            f"### Confidence Score: {confidence(stats)}",
            "",
            f"_Source PR: {pr_url}_",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    args = parser.parse_args()

    try:
        owner, repo, number = parse_pr_url(args.pr)
        diff = fetch_diff(owner, repo, number)
    except (RuntimeError, ValueError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 2

    print(render_review(args.pr, diff_stats(diff)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
