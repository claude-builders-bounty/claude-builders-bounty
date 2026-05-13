#!/usr/bin/env python3
"""Claude Code PR review agent CLI.

Fetches a public GitHub pull request diff and returns a structured Markdown
review comment with summary, risks, suggestions, and confidence.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PullRequestURL:
    owner: str
    repo: str
    number: int


@dataclass
class DiffAnalysis:
    files_changed: list[str]
    added_lines: int
    removed_lines: int
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")


def parse_pr_url(url: str) -> PullRequestURL:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("Expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestURL(owner=owner, repo=repo, number=int(number))


def fetch_pr_diff(pr: PullRequestURL) -> str:
    url = f"https://patch-diff.githubusercontent.com/raw/{pr.owner}/{pr.repo}/pull/{pr.number}.diff"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/plain",
            "User-Agent": "claude-review-agent/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _changed_files(diff: str) -> list[str]:
    files: list[str] = []
    seen = set()
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[len("+++ b/") :]
            if path != "/dev/null" and path not in seen:
                seen.add(path)
                files.append(path)
    return files


def _added_content_lines(diff: str) -> list[str]:
    lines = []
    for line in diff.splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            lines.append(line[1:])
    return lines


def _removed_content_lines(diff: str) -> list[str]:
    lines = []
    for line in diff.splitlines():
        if line.startswith("---"):
            continue
        if line.startswith("-"):
            lines.append(line[1:])
    return lines


def analyze_diff(diff: str) -> DiffAnalysis:
    files = _changed_files(diff)
    added_lines_list = [line for line in _added_content_lines(diff) if line.strip()]
    removed_lines_list = [line for line in _removed_content_lines(diff) if line.strip()]
    added = len(added_lines_list)
    removed = len(removed_lines_list)
    lower_added = "\n".join(added_lines_list).lower()

    if files:
        file_phrase = ", ".join(files[:4])
        if len(files) > 4:
            file_phrase += f", and {len(files) - 4} more file(s)"
        summary = f"This PR changes {len(files)} file(s): {file_phrase}. It adds {added} line(s) and removes {removed} line(s)."
    else:
        summary = "This PR diff does not show changed files. Verify that the PR is not empty or that the diff could be fetched correctly."

    risks: list[str] = []
    suggestions: list[str] = []

    if "shell=true" in lower_added or "shell = true" in lower_added:
        risks.append("Use of `shell=True` can execute unexpected shell input if any command content becomes user-controlled.")
        suggestions.append("Avoid `shell=True`; pass arguments as a list and validate any dynamic command parts.")

    if re.search(r"(?i)(secret|api[_-]?key|password|token)\w*\s*=\s*['\"][^'\"]+['\"]", "\n".join(added_lines_list)):
        risks.append("The diff appears to add a hard-coded secret, token, password, or API key.")
        suggestions.append("Move secrets into environment variables or a secret manager, and rotate any value that was committed.")

    if any(re.search(r"\b(eval|exec)\s*\(", line) for line in added_lines_list):
        risks.append("Dynamic code execution (`eval`/`exec`) can create code injection risk.")
        suggestions.append("Replace dynamic execution with explicit parsing or a safe dispatch table.")

    if any(re.search(r"rm\s+-rf|drop\s+table|truncate\s+table|delete\s+from", line, re.I) for line in added_lines_list):
        risks.append("The diff introduces destructive command or SQL patterns that deserve explicit safeguards.")
        suggestions.append("Add confirmation, scoping, dry-run behavior, and tests for destructive-operation paths.")

    test_files = [f for f in files if "test" in f.lower() or f.lower().endswith((".spec.ts", ".test.ts", ".spec.js", ".test.js"))]
    if not test_files:
        suggestions.append("Add or update automated tests that cover the new behavior and at least one failure/edge case.")

    if added + removed > 400:
        risks.append("The PR is relatively large, which increases review risk and may hide unrelated changes.")
        suggestions.append("Consider splitting unrelated changes into smaller PRs or documenting why the broad change is necessary.")

    if not risks:
        risks.append("No obvious high-risk patterns were detected from the diff alone; still review runtime behavior and tests manually.")

    confidence = "High" if risks or files else "Low"
    if added + removed > 800:
        confidence = "Medium"
    if not diff.strip():
        confidence = "Low"

    return DiffAnalysis(
        files_changed=files,
        added_lines=added,
        removed_lines=removed,
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
    )


def _bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def format_review(analysis: DiffAnalysis, pr_url: str) -> str:
    return f"""## Summary of changes
{analysis.summary}

## Identified risks
{_bullets(analysis.risks)}

## Improvement suggestions
{_bullets(analysis.suggestions)}

## Confidence score
**{analysis.confidence}** — based on static diff heuristics for {pr_url}. This is intended as a first-pass Claude Code review comment, not a replacement for maintainer judgment.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and print a structured Markdown comment.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Optional local diff file for offline testing instead of fetching from GitHub")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        pr = parse_pr_url(args.pr)
        if args.diff_file:
            with open(args.diff_file, "r", encoding="utf-8") as fh:
                diff = fh.read()
        else:
            diff = fetch_pr_diff(pr)
        print(format_review(analyze_diff(diff), args.pr))
    except Exception as exc:  # CLI should print concise human-facing errors.
        print(f"claude-review: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
