#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from typing import Callable, TextIO


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


@dataclass(frozen=True)
class ReviewResult:
    summary: list[str]
    risks: list[str]
    suggestions: list[str]
    confidence: str


def parse_pr_url(url: str) -> PullRequestRef:
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(f"Unsupported PR URL: {url}")
    owner, repo, number = match.groups()
    return PullRequestRef(owner=owner, repo=repo, number=int(number))


def fetch_pull_request(ref: PullRequestRef) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "claude-review"}
    pr_req = urllib.request.Request(
        f"https://api.github.com/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}",
        headers=headers,
    )
    with urllib.request.urlopen(pr_req, timeout=30) as response:
        payload = json.load(response)
    diff_req = urllib.request.Request(
        f"https://github.com/{ref.owner}/{ref.repo}/pull/{ref.number}.diff",
        headers={"User-Agent": "claude-review"},
    )
    with urllib.request.urlopen(diff_req, timeout=30) as response:
        diff_text = response.read().decode("utf-8", errors="replace")
    return {
        "title": payload.get("title", ""),
        "body": payload.get("body", "") or "",
        "diff": diff_text,
    }


def heuristically_review_pull_request(title: str, body: str, diff_text: str) -> ReviewResult:
    files_changed = len(re.findall(r"^diff --git ", diff_text, flags=re.MULTILINE))
    additions = len(re.findall(r"^\+[^+]", diff_text, flags=re.MULTILINE))
    deletions = len(re.findall(r"^-[^-]", diff_text, flags=re.MULTILINE))

    summary = [
        f"This PR touches {files_changed or 1} file(s) with roughly {additions} additions and {deletions} deletions.",
        f"The primary change appears to be: {title.strip() or 'an update without a title'}.",
    ]
    if body.strip():
        summary.append(f"Author context: {body.strip().splitlines()[0][:140]}")

    risks: list[str] = []
    suggestions: list[str] = []

    lowered = diff_text.lower()
    if "--force" in lowered:
        risks.append("Force-push related logic appears in the diff and can have destructive side effects if mis-scoped.")
        suggestions.append("Add an explicit guard or confirmation path around force-push behavior.")
    if "secrets: inherit" in lowered or "github/workflows" in lowered:
        risks.append("Workflow or CI changes are present, so release and permission behavior should be verified carefully.")
        suggestions.append("Document the expected workflow permissions and add a validation step for CI behavior.")
    if "delete from" in lowered or "drop table" in lowered or "truncate" in lowered:
        risks.append("Database-destructive operations appear in the diff and need careful rollback and scoping checks.")
        suggestions.append("Add a migration safety note or tests covering destructive query paths.")
    if not risks:
        risks.append("No obvious high-severity issue stands out from the diff alone, but runtime and edge-case behavior still need verification.")
    if not suggestions:
        suggestions.append("Add or reference at least one focused validation step so reviewers can confirm the changed behavior quickly.")

    confidence = "High" if files_changed <= 3 and additions <= 120 else "Medium"
    if files_changed > 10 or additions > 400:
        confidence = "Low"

    return ReviewResult(summary=summary[:3], risks=risks, suggestions=suggestions, confidence=confidence)


def build_review_markdown(
    summary: list[str],
    risks: list[str],
    suggestions: list[str],
    confidence: str,
) -> str:
    return "\n".join(
        [
            "# PR Review",
            "",
            "## Summary",
            *[f"- {line}" for line in summary],
            "",
            "## Risks",
            *[f"- {line}" for line in risks],
            "",
            "## Improvement Suggestions",
            *[f"- {line}" for line in suggestions],
            "",
            "## Confidence",
            confidence,
            "",
        ]
    )


def _claude_available() -> bool:
    return which("claude") is not None


def run_with_claude(ref: PullRequestRef, pr_payload: dict[str, str]) -> str:
    prompt = f"""Review this GitHub pull request and produce structured Markdown with exactly these sections:
## Summary
## Risks
## Improvement Suggestions
## Confidence

Pull request URL: https://github.com/{ref.owner}/{ref.repo}/pull/{ref.number}
Title: {pr_payload['title']}
Body:
{pr_payload['body']}

Diff:
{pr_payload['diff']}
"""
    result = subprocess.run(
        ["claude", "-p", prompt],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip() + "\n"


def main(
    argv: list[str] | None = None,
    stdout: TextIO | None = None,
    fetcher: Callable[[PullRequestRef], dict[str, str]] = fetch_pull_request,
) -> int:
    parser = argparse.ArgumentParser(prog="claude-review")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--output", help="Optional path to write the Markdown review")
    parser.add_argument("--heuristic", action="store_true", help="Skip Claude invocation and use local heuristics")
    args = parser.parse_args(argv)

    out = stdout or sys.stdout
    ref = parse_pr_url(args.pr)
    pr_payload = fetcher(ref)

    if _claude_available() and not args.heuristic:
        markdown = run_with_claude(ref, pr_payload)
    else:
        review = heuristically_review_pull_request(
            title=pr_payload.get("title", ""),
            body=pr_payload.get("body", ""),
            diff_text=pr_payload.get("diff", ""),
        )
        markdown = build_review_markdown(
            summary=review.summary,
            risks=review.risks,
            suggestions=review.suggestions,
            confidence=review.confidence,
        )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    out.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
