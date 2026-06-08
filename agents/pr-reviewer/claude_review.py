#!/usr/bin/env python3
"""Structured pull request reviewer CLI for Claude Code workflows."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_URL_RE = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")
DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_RE = re.compile(r"^@@ -(?P<old_start>\d+)(?:,\d+)? \+(?P<new_start>\d+)(?:,\d+)? @@")
RISKY_PATTERNS = [
    (re.compile(r"\beval\s*\("), "Uses eval, which can execute untrusted code."),
    (re.compile(r"\bexec\s*\("), "Uses exec-style execution; validate inputs and sandboxing."),
    (re.compile(r"innerHTML\s*="), "Assigns innerHTML, which can introduce XSS if input is not trusted."),
    (re.compile(r"dangerouslySetInnerHTML"), "Uses dangerouslySetInnerHTML; confirm sanitization."),
    (re.compile(r"\bsubprocess\.(?:run|Popen|call)\("), "Runs subprocesses; confirm argument safety and error handling."),
    (re.compile(r"\bos\.system\s*\("), "Runs shell commands; confirm no user-controlled interpolation."),
    (re.compile(r"\bSELECT\s+\*\b", re.IGNORECASE), "Uses SELECT *; check data volume and schema stability."),
    (re.compile(r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", re.IGNORECASE), "DELETE FROM without WHERE may delete an entire table."),
]
TEST_FILE_HINTS = ("/test", "/tests", ".test.", ".spec.", "_test.", "test_")


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    risky_lines: list[str] | None = None

    def __post_init__(self) -> None:
        if self.risky_lines is None:
            self.risky_lines = []


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_URL_RE.search(url)
    if not match:
        raise ValueError("Expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), match.group("number")


def fetch_text(url: str, accept: str | None = None) -> str:
    headers = {"User-Agent": "claude-review-agent"}
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub request failed with HTTP {exc.code}: {url}") from exc


def fetch_pr(pr_url: str) -> tuple[dict, str]:
    owner, repo, number = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    metadata = json.loads(fetch_text(api_url, "application/vnd.github+json"))
    diff_text = fetch_text(f"{pr_url}.diff", "text/plain")
    return metadata, diff_text


def parse_diff(diff_text: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None
    current_line = 0

    for line in diff_text.splitlines():
        file_match = DIFF_FILE_RE.match(line)
        if file_match:
            current = FileChange(file_match.group(1))
            files.append(current)
            current_line = 0
            continue

        hunk_match = HUNK_RE.match(line)
        if hunk_match:
            current_line = int(hunk_match.group("new_start")) - 1
            continue

        if current is None:
            continue

        if line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current_line += 1
            added = line[1:]
            for pattern, message in RISKY_PATTERNS:
                if pattern.search(added):
                    current.risky_lines.append(f"{current.path}:{current_line} - {message}")
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
        elif line.startswith(" "):
            current_line += 1

    return files


def _is_test_file(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(hint in normalized for hint in TEST_FILE_HINTS)


def _format_file_summary(files: Iterable[FileChange]) -> str:
    rows = []
    for change in files:
        rows.append(f"- `{change.path}`: +{change.additions} / -{change.deletions}")
    return "\n".join(rows) if rows else "- No changed files detected."


def _risk_level(files: list[FileChange]) -> str:
    total_added = sum(change.additions for change in files)
    touched_paths = [change.path.lower() for change in files]
    risky_count = sum(len(change.risky_lines or []) for change in files)

    if risky_count or any("migration" in path or "auth" in path or "payment" in path for path in touched_paths):
        return "High"
    if total_added > 300 or len(files) > 8:
        return "Medium"
    return "Low"


def _confidence_score(files: list[FileChange], risky_lines: list[str]) -> int:
    if not files:
        return 40
    score = 85
    if risky_lines:
        score -= min(25, len(risky_lines) * 8)
    if not any(_is_test_file(change.path) for change in files):
        score -= 10
    if sum(change.additions for change in files) > 300:
        score -= 10
    return max(35, min(score, 95))


def _confidence_label(score: int) -> str:
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def _summary_sentences(title: str, files: list[FileChange], test_files: list[str], risk: str) -> str:
    changed_count = len(files)
    added = sum(change.additions for change in files)
    deleted = sum(change.deletions for change in files)
    test_note = "It includes test changes." if test_files else "I did not detect test-file changes."
    return (
        f"This PR updates {changed_count} file{'s' if changed_count != 1 else ''} for `{title}`, with +{added} / -{deleted} lines in the diff. "
        f"The static review classifies the change as **{risk.lower()}** risk based on file scope, diff size, and risky code patterns. "
        f"{test_note}"
    )


def render_review(pr_url: str, metadata: dict, files: list[FileChange]) -> str:
    title = metadata.get("title") or "Untitled PR"
    author = (metadata.get("user") or {}).get("login") or "unknown"
    test_files = [change.path for change in files if _is_test_file(change.path)]
    risky_lines = [line for change in files for line in (change.risky_lines or [])]
    risk = _risk_level(files)
    confidence = _confidence_score(files, risky_lines)
    confidence_label = _confidence_label(confidence)

    if risky_lines:
        bug_section = "\n".join(f"- {line}" for line in risky_lines)
    else:
        bug_section = "- No obvious high-risk code patterns were detected by the static review pass."

    if test_files:
        testing_section = "\n".join(f"- Test coverage touched: `{path}`" for path in test_files)
        improvement_section = "- Review whether the updated tests assert the most important behavior changed by the PR."
    else:
        testing_section = "- I did not detect changed test files. Consider adding or updating tests for the modified behavior."
        improvement_section = "- Add or update tests that cover the behavior changed by this PR before merging."

    suggested_comment = (
        f"Thanks for the PR. I reviewed the diff for `{title}` and the overall risk looks **{risk.lower()}**. "
        "Please double-check the testing notes below before merge."
    )

    return f"""# PR Review: {title}

- PR: {pr_url}
- Author: @{author}
- Risk level: **{risk}**
- Files changed: {len(files)}
- Added lines: {sum(change.additions for change in files)}
- Deleted lines: {sum(change.deletions for change in files)}

## Summary

{_summary_sentences(title, files, test_files, risk)}

## Changed Files

{_format_file_summary(files)}

## Identified Risks

{bug_section}

## Improvement Suggestions

{improvement_section}

## Testing Gaps

{testing_section}

## Confidence Score

{confidence_label} ({confidence}/100)

## Suggested GitHub Comment

{suggested_comment}
"""


def review_from_diff(pr_url: str, metadata: dict, diff_text: str) -> str:
    return render_review(pr_url, metadata, parse_diff(diff_text))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--diff-file", help="Optional local diff fixture instead of fetching from GitHub")
    parser.add_argument("--metadata-file", help="Optional local PR metadata JSON fixture")
    parser.add_argument("--output", help="Write Markdown review to this file instead of stdout")
    args = parser.parse_args(argv)

    if args.diff_file:
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")
        metadata = json.loads(Path(args.metadata_file).read_text(encoding="utf-8")) if args.metadata_file else {"title": args.pr, "user": {"login": "unknown"}}
    else:
        metadata, diff_text = fetch_pr(args.pr)

    review = review_from_diff(args.pr, metadata, diff_text)
    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
    else:
        sys.stdout.write(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
