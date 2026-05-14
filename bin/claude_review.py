#!/usr/bin/env python3
"""Structured PR review CLI for Claude Code workflows.

The tool fetches a GitHub PR diff, performs deterministic review triage, and
returns a Markdown comment with the sections required by the bounty. It is
stdlib-only so it works in CI and fresh Claude Code sandboxes.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Sequence

PR_RE = re.compile(r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)/?$")
FILE_RE = re.compile(r"^diff --git a/(?P<old>.+?) b/(?P<new>.+)$")
HUNK_RE = re.compile(r"^@@")

RISK_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("database", re.compile(r"\b(migration|schema|ALTER TABLE|DROP TABLE|DELETE FROM|TRUNCATE)\b", re.I), "Touches database/schema behavior; verify migration safety and rollback path."),
    ("auth", re.compile(r"\b(auth|session|jwt|token|oauth|permission|role|acl)\b", re.I), "Touches auth/session/permission logic; verify access-control tests."),
    ("secrets", re.compile(r"\b(api[_-]?key|secret|password|private[_-]?key|bearer)\b", re.I), "Contains secret-like terms; confirm no credentials or tokens are committed."),
    ("network", re.compile(r"\b(fetch\(|requests\.|axios\.|urllib|http[s]?://|webhook)\b", re.I), "Touches network/API calls; verify timeout, retry, and error handling."),
    ("ci", re.compile(r"\.github/workflows|Dockerfile|docker-compose|package-lock|pnpm-lock|requirements\.txt", re.I), "Touches CI/build/dependency files; verify reproducible installs and pipeline impact."),
    ("tests", re.compile(r"\b(test|spec|pytest|unittest|vitest|jest)\b", re.I), "Includes tests or test config; check whether coverage matches changed behavior."),
)

@dataclasses.dataclass(frozen=True)
class ChangedFile:
    path: str
    added: int = 0
    removed: int = 0
    hunks: int = 0
    risk_tags: tuple[str, ...] = ()

@dataclasses.dataclass(frozen=True)
class Review:
    pr_url: str
    files: Sequence[ChangedFile]
    total_added: int
    total_removed: int
    risk_notes: Sequence[str]
    suggestions: Sequence[str]
    confidence: str


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_RE.match(url)
    if not match:
        raise ValueError("Expected GitHub PR URL like https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), match.group("number")


def fetch_pr_diff(pr_url: str) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    diff_url = f"https://patch-diff.githubusercontent.com/raw/{owner}/{repo}/pull/{number}.diff"
    request = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review-cli"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_diff(diff_text: str) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    current_path: str | None = None
    added = removed = hunks = 0
    collected_lines: list[str] = []

    def flush() -> None:
        nonlocal current_path, added, removed, hunks, collected_lines
        if current_path is None:
            return
        body = "\n".join(collected_lines)
        tags = tuple(name for name, pattern, _ in RISK_PATTERNS if pattern.search(current_path) or pattern.search(body))
        files.append(ChangedFile(current_path, added, removed, hunks, tags))
        current_path = None
        added = removed = hunks = 0
        collected_lines = []

    for line in diff_text.splitlines():
        file_match = FILE_RE.match(line)
        if file_match:
            flush()
            current_path = file_match.group("new")
            continue
        if current_path is None:
            continue
        collected_lines.append(line)
        if HUNK_RE.match(line):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    flush()
    return files


def analyze(pr_url: str, diff_text: str) -> Review:
    files = parse_diff(diff_text)
    total_added = sum(file.added for file in files)
    total_removed = sum(file.removed for file in files)
    risk_notes = build_risk_notes(files, total_added, total_removed)
    suggestions = build_suggestions(files, total_added, total_removed)
    confidence = confidence_score(files, total_added, total_removed, risk_notes)
    return Review(pr_url, files, total_added, total_removed, risk_notes, suggestions, confidence)


def build_risk_notes(files: Sequence[ChangedFile], total_added: int, total_removed: int) -> list[str]:
    notes: list[str] = []
    tag_counts = Counter(tag for file in files for tag in file.risk_tags)
    reason_by_tag = {name: reason for name, _, reason in RISK_PATTERNS}
    for tag, count in tag_counts.most_common():
        notes.append(f"{reason_by_tag[tag]} ({count} file{'s' if count != 1 else ''})")
    if total_added + total_removed > 800:
        notes.append("Large diff size; review may miss behavior hidden in broad refactors.")
    if not any("tests" in file.risk_tags or file.path.startswith("test") or "/test" in file.path for file in files):
        notes.append("No obvious test files changed; verify behavior manually or add coverage.")
    if not notes:
        notes.append("No high-risk patterns detected in the diff; review standard correctness and maintainability.")
    return notes


def build_suggestions(files: Sequence[ChangedFile], total_added: int, total_removed: int) -> list[str]:
    suggestions: list[str] = []
    paths = [file.path for file in files]
    if any(path.endswith((".py", ".ts", ".tsx", ".js")) for path in paths):
        suggestions.append("Run the language-specific test/lint/typecheck commands before merge and include results in the PR.")
    if any("database" in file.risk_tags for file in files):
        suggestions.append("Add migration notes: forward path, rollback/backup plan, and data-shape assumptions.")
    if any("auth" in file.risk_tags for file in files):
        suggestions.append("Add or confirm negative authorization tests, not only happy-path tests.")
    if any("network" in file.risk_tags for file in files):
        suggestions.append("Confirm external calls have timeouts and useful failure messages.")
    if total_added + total_removed > 500:
        suggestions.append("Consider splitting mechanical refactors from behavior changes to make review safer.")
    if not suggestions:
        suggestions.append("Keep the PR description focused on user-visible behavior and verification steps.")
    return suggestions


def confidence_score(files: Sequence[ChangedFile], total_added: int, total_removed: int, risk_notes: Sequence[str]) -> str:
    size = total_added + total_removed
    risk_tags = {tag for file in files for tag in file.risk_tags}
    has_tests = any("tests" in file.risk_tags or file.path.startswith("test") or "/test" in file.path for file in files)
    if size > 1000 or len(risk_tags & {"auth", "database", "secrets"}) >= 2:
        return "Low"
    if size > 400 or (risk_tags & {"auth", "database", "secrets"}) or not has_tests:
        return "Medium"
    return "High"


def summarize_changes(files: Sequence[ChangedFile], total_added: int, total_removed: int) -> str:
    if not files:
        return "This PR has an empty diff or the diff could not be parsed. No file-level changes were available for review."
    extensions = Counter(Path(file.path).suffix or "[no extension]" for file in files)
    top_ext = ", ".join(f"{ext} ({count})" for ext, count in extensions.most_common(3))
    biggest = sorted(files, key=lambda file: file.added + file.removed, reverse=True)[:3]
    biggest_text = ", ".join(f"`{file.path}`" for file in biggest)
    return (
        f"This PR changes {len(files)} file{'s' if len(files) != 1 else ''} "
        f"with +{total_added}/-{total_removed} lines. "
        f"The main file types are {top_ext}, with the largest changes in {biggest_text}."
    )


def render_markdown(review: Review) -> str:
    lines = ["## Claude PR Review", "", "### Summary of changes", ""]
    lines.append(summarize_changes(review.files, review.total_added, review.total_removed))
    lines.extend(["", "### Identified risks", ""])
    lines.extend(f"- {note}" for note in review.risk_notes)
    lines.extend(["", "### Improvement suggestions", ""])
    lines.extend(f"- {suggestion}" for suggestion in review.suggestions)
    lines.extend(["", f"### Confidence score: {review.confidence}", ""])
    lines.append(f"Reviewed diff: {review.pr_url}")
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and print a structured Markdown comment.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Optional local diff file for offline tests.")
    parser.add_argument("--output", help="Optional output markdown file. Defaults to stdout.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.diff_file:
            diff_text = Path(args.diff_file).read_text(encoding="utf-8")
        else:
            diff_text = fetch_pr_diff(args.pr)
        markdown = render_markdown(analyze(args.pr, diff_text))
    except Exception as exc:
        print(f"claude-review failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
