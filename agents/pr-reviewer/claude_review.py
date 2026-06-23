#!/usr/bin/env python3
"""Generate a structured Markdown review from a GitHub pull request diff."""

from __future__ import annotations

import argparse
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    has_tests: bool
    has_docs: bool
    has_db_change: bool
    has_security_change: bool
    has_dependency_change: bool


def github_diff_url(pr_url: str) -> str:
    clean = pr_url.strip().rstrip("/")
    if not re.match(r"^https://github\.com/[^/]+/[^/]+/pull/\d+$", clean):
        raise SystemExit("Expected a public GitHub PR URL like https://github.com/owner/repo/pull/123")
    return f"{clean}.diff"


def fetch_diff(pr_url: str) -> str:
    request = urllib.request.Request(github_diff_url(pr_url), headers={"User-Agent": "claude-review-cli"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def analyze_diff(diff_text: str) -> DiffStats:
    files: list[str] = []
    additions = 0
    deletions = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            match = re.search(r" b/(.+)$", line)
            if match:
                files.append(match.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    lowered = [file.lower() for file in files]
    has_tests = any("test" in file or "spec" in file or file.startswith("tests/") for file in lowered)
    has_docs = any(file.endswith((".md", ".mdx", ".rst")) or file.startswith("docs/") for file in lowered)
    has_db_change = any("migration" in file or "schema" in file or "/db/" in f"/{file}" for file in lowered)
    has_security_change = any("auth" in file or "token" in file or "secret" in file or "permission" in file for file in lowered)
    has_dependency_change = any(file.endswith(("package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "requirements.txt", "pyproject.toml", "cargo.toml", "go.mod")) for file in lowered)

    return DiffStats(
        files=files,
        additions=additions,
        deletions=deletions,
        has_tests=has_tests,
        has_docs=has_docs,
        has_db_change=has_db_change,
        has_security_change=has_security_change,
        has_dependency_change=has_dependency_change,
    )


def summary_for(stats: DiffStats, pr_url: str | None) -> str:
    file_count = len(stats.files)
    change_size = stats.additions + stats.deletions
    target = f" for {pr_url}" if pr_url else ""
    return (
        f"This PR{target} changes {file_count} file{'s' if file_count != 1 else ''} "
        f"with {stats.additions} additions and {stats.deletions} deletions. "
        f"The main review focus should be {'tests and behavior coverage' if stats.has_tests else 'behavior coverage and missing test evidence'}, "
        f"with extra attention to {'database/security boundaries' if stats.has_db_change or stats.has_security_change else 'scope control and validation evidence'}. "
        f"Overall size is {'small' if change_size < 120 else 'medium' if change_size < 500 else 'large'}, so review depth should match the risk rather than only the line count."
    )


def risks_for(stats: DiffStats) -> list[str]:
    risks: list[str] = []
    if not stats.files:
        return ["No changed files were detected in the provided diff."]
    if not stats.has_tests:
        risks.append("No test file was changed, so behavioral regressions may not be covered yet.")
    if stats.has_db_change:
        risks.append("Database/schema changes need migration and rollback review.")
    if stats.has_security_change:
        risks.append("Auth, token, secret, or permission-related files changed and need security-focused review.")
    if stats.has_dependency_change:
        risks.append("Dependency metadata changed, so lockfile consistency and supply-chain impact should be checked.")
    if stats.additions + stats.deletions > 500:
        risks.append("The diff is large enough that smaller reviewable slices may reduce review risk.")
    if not risks:
        risks.append("No obvious high-risk file patterns were detected; still verify the changed behavior manually.")
    return risks


def suggestions_for(stats: DiffStats) -> list[str]:
    suggestions = []
    if not stats.has_tests:
        suggestions.append("Add or link a focused regression test for the behavior changed by this PR.")
    else:
        suggestions.append("Confirm the touched tests fail before the fix or clearly prove the intended behavior.")
    if stats.has_docs:
        suggestions.append("Check that documentation changes match the implemented behavior and do not overpromise.")
    if stats.has_dependency_change:
        suggestions.append("Run install/lockfile validation and explain why the dependency change is needed.")
    suggestions.append("List the exact validation commands run in the PR description or follow-up comment.")
    suggestions.append("Keep follow-up cleanup separate unless it directly supports the reviewed change.")
    return suggestions


def confidence_for(stats: DiffStats) -> str:
    total = stats.additions + stats.deletions
    if stats.has_tests and total < 250 and not stats.has_security_change:
        return "High"
    if total < 600:
        return "Medium"
    return "Low"


def render_review(diff_text: str, pr_url: str | None = None) -> str:
    stats = analyze_diff(diff_text)
    lines = ["## PR review", "", "### Summary", "", summary_for(stats, pr_url), "", "### Identified risks", ""]
    for risk in risks_for(stats):
        lines.append(f"- {risk}")
    lines.extend(["", "### Improvement suggestions", ""])
    for suggestion in suggestions_for(stats):
        lines.append(f"- {suggestion}")
    lines.extend(["", "### Confidence score", "", confidence_for(stats), ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and print a structured Markdown comment.")
    parser.add_argument("--pr", help="Public GitHub PR URL to review.")
    parser.add_argument("--diff-file", help="Local diff file to review instead of fetching a PR.")
    parser.add_argument("--output", help="Optional Markdown file to write.")
    args = parser.parse_args()

    if not args.pr and not args.diff_file:
        raise SystemExit("Provide --pr or --diff-file")

    diff_text = fetch_diff(args.pr) if args.pr else Path(args.diff_file).read_text(encoding="utf-8")
    review = render_review(diff_text, args.pr)

    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(review, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
