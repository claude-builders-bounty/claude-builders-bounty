#!/usr/bin/env python3
"""Fetch a GitHub PR diff and produce a structured Markdown review comment."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")


@dataclass(frozen=True)
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    risky_files: list[str]
    has_tests: bool
    has_docs: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a GitHub pull request diff.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--max-diff-chars", type=int, default=60000, help="Maximum diff size sent to Claude")
    return parser.parse_args()


def diff_url(pr_url: str) -> str:
    match = PR_RE.match(pr_url)
    if not match:
        raise SystemExit("--pr must be a GitHub pull request URL")
    owner, repo, number = match.groups()
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_diff(pr_url: str) -> str:
    request = urllib.request.Request(diff_url(pr_url), headers={"User-Agent": "claude-review"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        raise SystemExit(f"failed to fetch PR diff: HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"failed to fetch PR diff: {error.reason}") from error


def analyze_diff(diff: str) -> DiffStats:
    files: list[str] = []
    additions = 0
    deletions = 0

    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            files.append(line.removeprefix("+++ b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    risky_patterns = (
        ".github/workflows/",
        "package.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "package-lock.json",
        "schema",
        "migration",
        "auth",
        "billing",
        "payment",
    )
    risky_files = [path for path in files if any(pattern in path.lower() for pattern in risky_patterns)]
    has_tests = any(("test" in path.lower() or "spec" in path.lower()) for path in files)
    has_docs = any(path.lower().endswith((".md", ".mdx", ".rst")) for path in files)
    return DiffStats(files, additions, deletions, risky_files, has_tests, has_docs)


def bullet_list(items: Iterable[str], fallback: str) -> str:
    values = list(items)
    if not values:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in values)


def local_review(pr_url: str, diff: str) -> str:
    stats = analyze_diff(diff)
    file_count = len(stats.files)
    changed = f"{file_count} file{'s' if file_count != 1 else ''}, +{stats.additions}/-{stats.deletions}"

    risks: list[str] = []
    if stats.risky_files:
        risks.append("Touches higher-risk files: " + ", ".join(stats.risky_files[:5]))
    if not stats.has_tests:
        risks.append("No test files were changed, so behavior may rely on manual validation.")
    if stats.additions + stats.deletions > 500:
        risks.append("Large diff size makes regression review harder.")
    if not risks:
        risks.append("No obvious high-risk files or unusually large changes detected from the diff alone.")

    suggestions: list[str] = []
    if not stats.has_tests:
        suggestions.append("Add or mention targeted test coverage for the changed behavior.")
    if stats.has_docs:
        suggestions.append("Confirm examples and commands in documentation were run or manually verified.")
    suggestions.append("Keep the PR body aligned with the actual validation performed.")

    confidence = "High" if file_count <= 3 and not stats.risky_files else "Medium"
    if stats.additions + stats.deletions > 1000:
        confidence = "Low"

    focus = ", ".join(stats.files[:3]) if stats.files else "repository content"
    return "\n\n".join(
        [
            "## Summary",
            f"This PR changes {changed}. The diff appears focused on {focus}.",
            "## Identified Risks",
            bullet_list(risks, "No major risks detected."),
            "## Improvement Suggestions",
            bullet_list(suggestions, "No specific suggestions."),
            "## Confidence",
            confidence,
        ]
    )


def claude_review(pr_url: str, diff: str, max_chars: int) -> str | None:
    if os.environ.get("CLAUDE_REVIEW_USE_CLAUDE") != "1":
        return None
    if shutil.which("claude") is None:
        return None

    prompt = textwrap.dedent(
        f"""\
        Review this pull request diff and return only Markdown with these sections:
        ## Summary
        2-3 sentences.
        ## Identified Risks
        Bullet list.
        ## Improvement Suggestions
        Bullet list.
        ## Confidence
        Low, Medium, or High.

        PR: {pr_url}

        Diff:
        {diff[:max_chars]}
        """
    )
    result = subprocess.run(
        ["claude", "-p", prompt],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.strip()


def main() -> int:
    args = parse_args()
    diff = fetch_diff(args.pr)
    review = claude_review(args.pr, diff, args.max_diff_chars) or local_review(args.pr, diff)
    print(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
