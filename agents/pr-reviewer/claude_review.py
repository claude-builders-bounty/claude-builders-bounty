#!/usr/bin/env python3
"""Fetch a GitHub PR diff and produce a structured Markdown review."""

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
from pathlib import Path


AGENT_PROMPT = Path(__file__).with_name("agent.md")


@dataclass
class DiffStats:
    files: list[str]
    added_lines: int
    removed_lines: int
    has_tests: bool
    has_lockfile: bool
    has_migration: bool
    has_security_sensitive_code: bool
    has_large_change: bool


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = re.match(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$", url)
    if not match:
        raise ValueError("Expected PR URL shaped like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)


def fetch_url(url: str, token: str | None = None) -> str:
    headers = {"User-Agent": "claude-pr-reviewer/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub returned HTTP {error.code} for {url}") from error


def fetch_diff(pr_url: str, token: str | None = None) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    return fetch_url(f"https://patch-diff.githubusercontent.com/raw/{owner}/{repo}/pull/{number}.diff", token)


def collect_stats(diff: str) -> DiffStats:
    files = re.findall(r"^\+\+\+ b/(.+)$", diff, flags=re.MULTILINE)
    added_lines = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed_lines = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    lowered_files = [file.lower() for file in files]
    lowered_diff = diff.lower()
    has_tests = any(re.search(r"(^|/)(test|tests|spec|__tests__)(/|$)", file) or file.endswith((".test.ts", ".test.js", ".spec.ts", ".spec.js", "_test.py")) for file in lowered_files)
    has_lockfile = any(file.endswith(("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock")) for file in lowered_files)
    has_migration = any("migration" in file or "schema" in file for file in lowered_files)
    security_terms = ("auth", "token", "password", "secret", "permission", "csrf", "xss", "sql", "jwt")
    has_security_sensitive_code = any(term in lowered_diff for term in security_terms)
    has_large_change = added_lines + removed_lines > 500 or len(files) > 12
    return DiffStats(
        files=files,
        added_lines=added_lines,
        removed_lines=removed_lines,
        has_tests=has_tests,
        has_lockfile=has_lockfile,
        has_migration=has_migration,
        has_security_sensitive_code=has_security_sensitive_code,
        has_large_change=has_large_change,
    )


def format_file_summary(files: list[str]) -> str:
    if not files:
        return "No changed files were found in the diff."
    visible = files[:8]
    suffix = "" if len(files) <= 8 else f", and {len(files) - 8} more"
    return ", ".join(f"`{file}`" for file in visible) + suffix


def offline_review(pr_url: str, diff: str) -> str:
    stats = collect_stats(diff)
    risks: list[str] = []
    suggestions: list[str] = []

    if not stats.has_tests:
        risks.append("Behavior appears to change without dedicated test files in the diff.")
        suggestions.append("Add focused regression tests that fail before this change and pass after it.")
    if stats.has_security_sensitive_code:
        risks.append("The diff touches security-sensitive terms such as auth, tokens, permissions, SQL, or secrets.")
        suggestions.append("Double-check access control, secret handling, and failure paths before merging.")
    if stats.has_migration:
        risks.append("Schema or migration-related files are present, so rollout and rollback behavior may matter.")
        suggestions.append("Document migration order and verify backward compatibility with existing data.")
    if stats.has_lockfile:
        risks.append("A dependency lockfile changed; supply-chain and version drift should be reviewed.")
        suggestions.append("Confirm the dependency update is intentional and scan the resolved versions.")
    if stats.has_large_change:
        risks.append("The change is large enough that review coverage may be uneven.")
        suggestions.append("Consider splitting mechanical changes from behavior changes where possible.")

    if not risks:
        risks.append("No major risks identified from the diff alone.")
    if not suggestions:
        suggestions.append("Add a short validation note to the PR description explaining how the change was tested.")

    confidence = "Medium"
    confidence_reason = "Diff-level review was possible, but repository-specific runtime context was not available."
    if stats.has_tests and not stats.has_large_change:
        confidence = "High"
        confidence_reason = "The diff is scoped and includes test coverage."
    if stats.has_large_change and not stats.has_tests:
        confidence = "Low"
        confidence_reason = "The diff is large and no dedicated tests were detected."

    return "\n".join(
        [
            "## Summary",
            (
                f"This pull request changes {len(stats.files)} file(s), with {stats.added_lines} added "
                f"line(s) and {stats.removed_lines} removed line(s). The main files visible in the diff are "
                f"{format_file_summary(stats.files)}."
            ),
            "The review below is based on the PR diff and highlights merge risks that are visible without running the full project.",
            "",
            "## Identified Risks",
            *[f"- {risk}" for risk in risks],
            "",
            "## Improvement Suggestions",
            *[f"- {suggestion}" for suggestion in suggestions],
            "",
            "## Confidence",
            f"{confidence} - {confidence_reason}",
            "",
        ]
    )


def claude_review(pr_url: str, diff: str) -> str:
    if not shutil.which("claude"):
        raise RuntimeError("Claude Code CLI not found")
    prompt = textwrap.dedent(
        f"""
        Use the bundled PR reviewer agent instructions below to review this pull request.

        Pull request: {pr_url}

        Agent instructions:
        {AGENT_PROMPT.read_text(encoding='utf-8')}

        Diff:
        ```diff
        {diff[:120000]}
        ```
        """
    ).strip()
    completed = subprocess.run(
        ["claude", "-p", prompt],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Claude Code CLI failed")
    return completed.stdout.strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--offline", action="store_true", help="Use deterministic local review instead of Claude")
    parser.add_argument("--output", help="Write review Markdown to this path")
    parser.add_argument("--token-env", default="GITHUB_TOKEN", help="Environment variable that contains a GitHub token")
    args = parser.parse_args(argv)

    token = os.environ.get(args.token_env)
    diff = fetch_diff(args.pr, token)
    if args.offline:
        review = offline_review(args.pr, diff)
    else:
        try:
            review = claude_review(args.pr, diff)
        except RuntimeError as error:
            review = offline_review(args.pr, diff)
            review += f"\n<!-- Claude Code CLI fallback reason: {error} -->\n"

    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
    else:
        sys.stdout.write(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

