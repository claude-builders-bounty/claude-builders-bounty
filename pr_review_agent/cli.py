"""CLI for generating structured Markdown PR review comments."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


PR_URL_RE = re.compile(r"^https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?:[/?#].*)?$")
FILE_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
HUNK_RE = re.compile(r"^@@", re.MULTILINE)


@dataclass(frozen=True)
class Review:
    summary: list[str]
    risks: list[str]
    suggestions: list[str]
    confidence: str


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("PR URL must look like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)


def diff_url(pr_url: str) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    return f"https://github.com/{owner}/{repo}/pull/{number}.diff"


def fetch_diff(pr_url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        diff_url(pr_url),
        headers={
            "Accept": "text/x-diff",
            "User-Agent": "claude-review-agent",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub returned HTTP {exc.code} while fetching PR diff") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not fetch PR diff: {exc.reason}") from exc


def changed_files(diff: str) -> list[str]:
    return sorted(set(FILE_RE.findall(diff)))


def count_lines(diff: str) -> tuple[int, int]:
    added = 0
    removed = 0
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return added, removed


def classify_files(files: Iterable[str]) -> list[str]:
    labels: list[str] = []
    for path in files:
        lower = path.lower()
        if lower.endswith((".md", ".rst", ".txt")):
            labels.append("documentation")
        elif lower.endswith((".yml", ".yaml", ".json", ".toml")):
            labels.append("configuration")
        elif lower.endswith((".py", ".js", ".ts", ".tsx", ".go", ".rs", ".java")):
            labels.append("code")
        elif "test" in lower or "spec" in lower:
            labels.append("tests")
        else:
            labels.append("other files")
    return sorted(set(labels))


def analyze_diff(diff: str) -> Review:
    files = changed_files(diff)
    added, removed = count_lines(diff)
    hunks = len(HUNK_RE.findall(diff))
    categories = classify_files(files)

    file_phrase = ", ".join(files[:4]) if files else "no changed files detected"
    if len(files) > 4:
        file_phrase += f", and {len(files) - 4} more"

    summary = [
        f"This PR changes {len(files)} file(s): {file_phrase}.",
        f"The diff contains {added} added line(s), {removed} removed line(s), and {hunks} changed hunk(s), primarily affecting {', '.join(categories) if categories else 'uncategorized files'}.",
    ]

    lower = diff.lower()
    risks: list[str] = []
    if not files:
        risks.append("No changed files were detected in the diff, so the review may be incomplete.")
    if added + removed > 500:
        risks.append("The PR is large enough that behavior-level review should be split by area.")
    if any(token in lower for token in ("password", "secret", "api_key", "token")):
        risks.append("The diff contains credential-like terms; verify no secrets are committed.")
    if any(token in lower for token in ("subprocess", "shell=true", "exec(", "eval(")):
        risks.append("The diff includes command execution or dynamic evaluation patterns; validate inputs and failure handling.")
    if any(token in lower for token in ("delete from", "drop table", "truncate", "rm -rf")):
        risks.append("The diff includes destructive-operation terms; confirm safeguards and tests cover them.")
    if not any("test" in path.lower() or "spec" in path.lower() for path in files):
        risks.append("No test file changes were detected; regression coverage may be weak.")
    if not risks:
        risks.append("No obvious high-risk patterns were detected from the diff text alone.")

    suggestions: list[str] = []
    if "readme" not in " ".join(path.lower() for path in files):
        suggestions.append("Add or update README usage notes if this changes user-facing behavior.")
    if not any("test" in path.lower() or "spec" in path.lower() for path in files):
        suggestions.append("Add focused tests for the main success path and at least one failure path.")
    suggestions.append("Include the exact command used for local verification in the PR description.")
    if added + removed > 250:
        suggestions.append("Ask reviewers to inspect the highest-risk file first, then review generated or documentation changes separately.")

    confidence = "High"
    if not files or added + removed > 500:
        confidence = "Medium"
    if len(diff.strip()) < 80:
        confidence = "Low"

    return Review(summary=summary, risks=risks, suggestions=suggestions, confidence=confidence)


def format_review(pr_url: str, review: Review) -> str:
    lines = [
        "## Structured PR Review",
        "",
        f"PR: {pr_url}",
        "",
        "### Summary of changes",
    ]
    lines.extend(f"- {item}" for item in review.summary)
    lines.extend(["", "### Identified risks"])
    lines.extend(f"- {item}" for item in review.risks)
    lines.extend(["", "### Improvement suggestions"])
    lines.extend(f"- {item}" for item in review.suggestions)
    lines.extend(["", f"### Confidence score: {review.confidence}", ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and emit structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Optional local diff file for offline testing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        parse_pr_url(args.pr)
        if args.diff_file:
            with open(args.diff_file, "r", encoding="utf-8") as handle:
                diff = handle.read()
        else:
            diff = fetch_diff(args.pr)
        print(format_review(args.pr, analyze_diff(diff)))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
