#!/usr/bin/env python3
"""CLI PR review agent that emits a structured Markdown review comment."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")
FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    test_files: int
    docs_files: int
    risky_patterns: list[str]


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("Expected PR URL like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)


def fetch_diff(pr_url: str) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    diff_url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    request = Request(diff_url, headers={"User-Agent": "claude-pr-review-agent"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} for {diff_url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not fetch PR diff: {exc.reason}") from exc


def analyze_diff(diff: str) -> DiffStats:
    files = FILE_RE.findall(diff)
    additions = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    lowered_files = [file.lower() for file in files]
    test_files = sum(1 for file in lowered_files if "test" in file or "spec" in file)
    docs_files = sum(1 for file in lowered_files if file.endswith(".md") or "readme" in file)

    risky_patterns: list[str] = []
    lowered_diff = diff.lower()
    checks = [
        ("destructive shell operation", r"rm\s+-[a-z]*r[a-z]*f|--force"),
        ("database destructive statement", r"drop\s+table|truncate|delete\s+from"),
        ("secret or credential handling", r"api[_-]?key|secret|token|password"),
        ("network call or external dependency", r"https?://|urlopen|fetch\(|requests\."),
        ("filesystem write/delete behavior", r"write_text|open\(.+['\"]w|remove\(|unlink\("),
    ]
    for label, pattern in checks:
        if re.search(pattern, lowered_diff):
            risky_patterns.append(label)

    return DiffStats(
        files=files,
        additions=additions,
        deletions=deletions,
        test_files=test_files,
        docs_files=docs_files,
        risky_patterns=risky_patterns,
    )


def confidence(stats: DiffStats) -> str:
    if not stats.files:
        return "Low"
    if stats.additions + stats.deletions > 800 or not stats.test_files:
        return "Medium"
    if len(stats.risky_patterns) >= 3:
        return "Medium"
    return "High"


def summarize(stats: DiffStats) -> str:
    if not stats.files:
        return "This PR diff did not expose changed files, so the review is limited. I could not infer the implementation surface from the patch."

    file_count = len(stats.files)
    changed = f"{file_count} file{'s' if file_count != 1 else ''}"
    code_surface = ", ".join(stats.files[:4])
    if file_count > 4:
        code_surface += ", ..."

    return (
        f"This PR changes {changed} with {stats.additions} additions and {stats.deletions} deletions. "
        f"The main surface appears to be `{code_surface}`. "
        "The review below focuses on test coverage, operational risk, and maintainability signals visible in the diff."
    )


def risks(stats: DiffStats) -> list[str]:
    items: list[str] = []
    if not stats.test_files:
        items.append("No dedicated test file was detected in the diff, so regressions may not be caught automatically.")
    if stats.risky_patterns:
        items.append("Risk-sensitive patterns detected: " + ", ".join(sorted(set(stats.risky_patterns))) + ".")
    if stats.additions + stats.deletions > 500:
        items.append("The patch is moderately large; reviewers should check whether it can be split or whether all changed files are necessary.")
    if stats.docs_files == 0:
        items.append("No documentation update was detected, which may make adoption harder if behavior or setup changed.")
    if not items:
        items.append("No major structural risks were detected from the diff metadata.")
    return items


def suggestions(stats: DiffStats) -> list[str]:
    items: list[str] = []
    if not stats.test_files:
        items.append("Add focused tests that cover the core behavior and at least one failure path.")
    if stats.docs_files == 0:
        items.append("Add or update README usage notes for any new command, configuration, or workflow.")
    if stats.risky_patterns:
        items.append("Document the guardrails around detected risk-sensitive behavior and include a negative test where practical.")
    items.append("Keep the PR description aligned with the changed files and include exact local validation commands.")
    return items


def render_review(pr_url: str, stats: DiffStats) -> str:
    risk_lines = "\n".join(f"- {item}" for item in risks(stats))
    suggestion_lines = "\n".join(f"- {item}" for item in suggestions(stats))
    return f"""## Summary

{summarize(stats)}

## Identified risks

{risk_lines}

## Improvement suggestions

{suggestion_lines}

## Confidence score

{confidence(stats)}

Reviewed PR: {pr_url}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--output", help="Optional output Markdown file")
    args = parser.parse_args(argv)

    try:
        diff = fetch_diff(args.pr)
        review = render_review(args.pr, analyze_diff(diff))
    except (RuntimeError, ValueError) as exc:
        print(f"claude-review failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
    else:
        print(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
