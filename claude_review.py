#!/usr/bin/env python3
"""Generate a structured Markdown review from a GitHub pull request diff."""

from __future__ import annotations

import argparse
import dataclasses
import re
import sys
import urllib.error
import urllib.request


RISK_PATTERNS = (
    ("destructive operation", re.compile(r"\b(rm\s+-rf|DROP\s+TABLE|TRUNCATE|DELETE\s+FROM)\b", re.IGNORECASE)),
    ("secret or credential handling", re.compile(r"\b(api[_-]?key|secret|token|password|private[_-]?key)\b", re.IGNORECASE)),
    ("network or external I/O", re.compile(r"\b(fetch|axios|requests\.|urllib|http\.|https://)\b", re.IGNORECASE)),
    ("database/schema change", re.compile(r"\b(migration|schema|CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE)\b", re.IGNORECASE)),
    ("authentication/authorization", re.compile(r"\b(auth|permission|role|session|jwt|oauth)\b", re.IGNORECASE)),
)


@dataclasses.dataclass(frozen=True)
class DiffStats:
    files_changed: int
    additions: int
    deletions: int
    hunks: int


@dataclasses.dataclass(frozen=True)
class Review:
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str


def parse_pr_url(pr_url: str) -> tuple[str, str, str]:
    match = re.match(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$", pr_url)
    if not match:
        raise ValueError("Expected PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return owner, repo, number


def diff_url(pr_url: str) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "claude-review-cli"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not fetch {url}: {error}") from error


def changed_files(diff_text: str) -> list[str]:
    files: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                files.append(parts[1])
    return files


def diff_stats(diff_text: str) -> DiffStats:
    files = changed_files(diff_text)
    additions = 0
    deletions = 0
    hunks = 0
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return DiffStats(files_changed=len(files), additions=additions, deletions=deletions, hunks=hunks)


def detect_risks(diff_text: str) -> list[str]:
    risks: list[str] = []
    for label, pattern in RISK_PATTERNS:
        if pattern.search(diff_text):
            risks.append(f"- Review {label}: matching changes appear in the diff.")

    stats = diff_stats(diff_text)
    if stats.files_changed > 20:
        risks.append(f"- Large review surface: {stats.files_changed} files changed.")
    if stats.additions + stats.deletions > 800:
        risks.append(f"- Large diff size: {stats.additions} additions and {stats.deletions} deletions.")
    if not risks:
        risks.append("- No high-risk patterns detected from the diff text.")
    return risks


def build_suggestions(files: list[str], stats: DiffStats, risks: list[str]) -> list[str]:
    suggestions = [
        "- Confirm the PR has tests or documented manual validation for the changed behavior.",
        "- Check that edge cases around empty, invalid, or missing inputs are covered.",
    ]

    if any(file.endswith((".md", ".mdx")) for file in files):
        suggestions.append("- For documentation changes, verify examples are copy-paste runnable where applicable.")
    if any("test" in file.lower() for file in files):
        suggestions.append("- Make sure new tests fail without the implementation change.")
    if any("No high-risk patterns" not in risk for risk in risks):
        suggestions.append("- Ask for focused maintainer review on the detected risk areas before merge.")
    if stats.files_changed <= 3 and stats.additions + stats.deletions <= 150:
        suggestions.append("- This is a small diff; prefer a direct maintainer review over expanding process.")
    return suggestions


def confidence(stats: DiffStats, diff_text: str) -> str:
    if not diff_text.strip():
        return "Low"
    if stats.files_changed <= 5 and stats.additions + stats.deletions <= 300:
        return "High"
    if stats.files_changed <= 20 and stats.additions + stats.deletions <= 800:
        return "Medium"
    return "Low"


def summarize(pr_url: str, files: list[str], stats: DiffStats) -> str:
    file_preview = ", ".join(files[:5]) if files else "no files detected"
    if len(files) > 5:
        file_preview += f", and {len(files) - 5} more"
    return (
        f"This PR changes {stats.files_changed} file(s), with {stats.additions} additions "
        f"and {stats.deletions} deletions across {stats.hunks} diff hunk(s). "
        f"The main changed paths are: {file_preview}. Source PR: {pr_url}."
    )


def render_review(review: Review) -> str:
    lines = [
        "## PR Review",
        "",
        "### Summary",
        "",
        review.summary,
        "",
        "### Identified Risks",
        "",
        *review.risks,
        "",
        "### Improvement Suggestions",
        "",
        *review.suggestions,
        "",
        f"### Confidence: {review.confidence}",
        "",
    ]
    return "\n".join(lines)


def review_pr(pr_url: str) -> Review:
    diff_text = fetch_text(diff_url(pr_url))
    files = changed_files(diff_text)
    stats = diff_stats(diff_text)
    risks = detect_risks(diff_text)
    suggestions = build_suggestions(files, stats, risks)
    return Review(
        summary=summarize(pr_url, files, stats),
        risks=risks,
        suggestions=suggestions,
        confidence=confidence(stats, diff_text),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        review = review_pr(args.pr)
    except (RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(render_review(review))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
