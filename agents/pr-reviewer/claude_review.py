#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub pull request diff."""

from __future__ import annotations

import argparse
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass


PR_URL_RE = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)/?$")


@dataclass
class DiffStats:
    files: list[str]
    added: int
    removed: int
    test_files: list[str]
    docs_only: bool
    raw: str


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("PR URL must look like https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), match.group("number")


def fetch_pr_diff(url: str) -> str:
    owner, repo, number = parse_pr_url(url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    request = urllib.request.Request(api_url)
    request.add_header("Accept", "application/vnd.github.v3.diff")
    request.add_header("User-Agent", "claude-review-bounty-agent")

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while fetching the PR diff") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch PR diff: {exc.reason}") from exc


def parse_diff(diff: str) -> DiffStats:
    files: list[str] = []
    added = 0
    removed = 0

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[3].removeprefix("b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1

    test_files = [
        path
        for path in files
        if re.search(r"(^|/)(test|tests|spec|__tests__)(/|$)|(\.test|\.spec)\.", path, re.IGNORECASE)
    ]
    docs_only = bool(files) and all(
        path.lower().endswith((".md", ".mdx", ".txt", ".rst")) or path.lower().startswith("docs/")
        for path in files
    )
    return DiffStats(files=files, added=added, removed=removed, test_files=test_files, docs_only=docs_only, raw=diff)


def detect_risks(stats: DiffStats) -> list[str]:
    risks: list[str] = []
    lowered = stats.raw.lower()
    changed = stats.added + stats.removed

    if changed > 500:
        risks.append(f"Large diff size ({changed} changed lines) raises review and regression risk.")
    if not stats.docs_only and not stats.test_files:
        risks.append("No test files were changed; behavior changes may lack regression coverage.")
    if re.search(r"\b(eval|exec)\s*\(", lowered):
        risks.append("Dynamic code execution appears in the diff; validate input handling carefully.")
    if "dangerouslysetinnerhtml" in lowered or ".innerhtml" in lowered:
        risks.append("HTML injection surfaces changed; check escaping and trusted-content boundaries.")
    if re.search(r"(password|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]+", lowered):
        risks.append("Potential hardcoded credential-like value detected in added code.")
    if re.search(r"(drop table|truncate|delete from)", lowered):
        risks.append("Destructive SQL appears in the diff; verify transaction and migration safety.")
    if re.search(r"\bconsole\.log\(|\bdebugger\b|todo|fixme", lowered):
        risks.append("Debug or placeholder markers appear in the diff and may need cleanup.")

    return risks or ["No obvious high-risk patterns were detected from the diff alone."]


def suggestions(stats: DiffStats, risks: list[str]) -> list[str]:
    items: list[str] = []
    if not stats.docs_only and not stats.test_files:
        items.append("Add or update focused tests for the changed behavior before merging.")
    if stats.added + stats.removed > 500:
        items.append("Consider splitting the PR or adding a reviewer guide for the largest files.")
    if stats.files:
        items.append("Ask reviewers to focus first on the changed public interfaces and data-flow boundaries.")
    if risks == ["No obvious high-risk patterns were detected from the diff alone."]:
        items.append("Keep the PR description aligned with the diff so reviewers can confirm intent quickly.")
    items.append("Run the project's normal lint, typecheck, and test commands before approval.")
    return items


def confidence(stats: DiffStats, risks: list[str]) -> str:
    if not stats.raw.strip() or stats.added + stats.removed > 800:
        return "Low"
    if stats.test_files and len(risks) <= 2:
        return "High"
    if stats.docs_only or len(risks) <= 2:
        return "Medium"
    return "Low"


def render_review(pr_url: str, stats: DiffStats) -> str:
    risks = detect_risks(stats)
    improvement_suggestions = suggestions(stats, risks)
    file_summary = ", ".join(stats.files[:5]) if stats.files else "no files detected"
    if len(stats.files) > 5:
        file_summary += f", and {len(stats.files) - 5} more"

    summary = (
        f"This PR changes {len(stats.files)} file(s), with {stats.added} added and {stats.removed} removed lines. "
        f"The main touched paths are: {file_summary}. "
        "The review below is generated from the public diff and should be combined with project-specific CI results."
    )

    return "\n".join(
        [
            "## Claude Review",
            "",
            f"**PR:** {pr_url}",
            "",
            "### Summary of Changes",
            "",
            textwrap.fill(summary, width=100),
            "",
            "### Identified Risks",
            "",
            *[f"- {risk}" for risk in risks],
            "",
            "### Improvement Suggestions",
            "",
            *[f"- {item}" for item in improvement_suggestions],
            "",
            f"### Confidence Score: {confidence(stats, risks)}",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and emit structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    args = parser.parse_args(argv)

    try:
        diff = fetch_pr_diff(args.pr)
        print(render_review(args.pr, parse_diff(diff)))
    except (RuntimeError, ValueError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
