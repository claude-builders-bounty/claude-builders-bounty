#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub PR."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


PR_URL_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:\D.*)?$")


@dataclass
class PullRequestRef:
    owner: str
    repo: str
    number: int


def parse_pr_url(url: str) -> PullRequestRef:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("PR URL must look like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestRef(owner, repo, int(number))


def github_get(path: str) -> Any:
    request = urllib.request.Request(f"https://api.github.com{path}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("User-Agent", "claude-pr-review-agent")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_pr(ref: PullRequestRef) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pr = github_get(f"/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}")
    files = github_get(f"/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}/files?per_page=100")
    return pr, files


def infer_risks(pr: dict[str, Any], files: list[dict[str, Any]]) -> list[str]:
    risks: list[str] = []
    total_changes = sum(file.get("changes", 0) for file in files)
    filenames = [file.get("filename", "") for file in files]
    body = pr.get("body") or ""

    if total_changes > 500:
        risks.append(f"Large diff size ({total_changes} changed lines) increases review and regression risk.")
    if not re.search(r"#\d+|fixes\s+#\d+|closes\s+#\d+", body, re.I):
        risks.append("The PR body does not clearly link to an issue or acceptance criteria.")
    if not any(re.search(r"(test|spec)", name, re.I) for name in filenames):
        risks.append("No obvious test or spec files are included, so behavior may be under-verified.")
    if any(name.endswith((".lock", ".min.js", ".snap")) for name in filenames):
        risks.append("Generated or lock-like files are present and should be checked for intentional changes.")
    if any(re.search(r"(auth|secret|token|credential|payment|wallet)", name, re.I) for name in filenames):
        risks.append("Security-sensitive paths changed; review trust boundaries and secret handling carefully.")
    if not risks:
        risks.append("No major structural risk is obvious from metadata and file names; still review changed code paths manually.")
    return risks


def infer_suggestions(files: list[dict[str, Any]]) -> list[str]:
    suggestions = [
        "Map each changed file back to the linked issue's acceptance criteria before merge.",
        "Run the smallest relevant test command locally and paste the result into the PR thread.",
    ]
    if len(files) > 8:
        suggestions.append("Consider splitting unrelated changes if reviewers cannot evaluate the diff in one pass.")
    if not any(re.search(r"readme|docs?", file.get("filename", ""), re.I) for file in files):
        suggestions.append("Add a short README or usage note if the change introduces a new workflow or command.")
    return suggestions


def confidence(files: list[dict[str, Any]], risks: list[str]) -> str:
    total_changes = sum(file.get("changes", 0) for file in files)
    if total_changes > 800 or len(risks) >= 4:
        return "Low"
    if total_changes > 250 or len(risks) >= 2:
        return "Medium"
    return "High"


def render_review(pr_url: str, pr: dict[str, Any], files: list[dict[str, Any]]) -> str:
    title = pr.get("title", "Untitled PR")
    total_changes = sum(file.get("changes", 0) for file in files)
    file_list = ", ".join(file.get("filename", "") for file in files[:6])
    if len(files) > 6:
        file_list += f", and {len(files) - 6} more"

    risks = infer_risks(pr, files)
    suggestions = infer_suggestions(files)
    score = confidence(files, risks)

    lines = [
        "## Summary of Changes",
        "",
        f"This PR, **{title}**, updates {len(files)} file(s) with about {total_changes} changed line(s).",
        f"The visible review surface includes: {file_list or 'no changed files returned by the API'}.",
        "The assessment below is based on PR metadata and changed-file context; reviewers should still inspect the code diff before merge.",
        "",
        "## Identified Risks",
        "",
        *[f"- {risk}" for risk in risks],
        "",
        "## Improvement Suggestions",
        "",
        *[f"- {suggestion}" for suggestion in suggestions],
        "",
        "## Confidence",
        "",
        score,
        "",
        f"Reviewed PR: {pr_url}",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    args = parser.parse_args(argv)

    try:
        ref = parse_pr_url(args.pr)
        pr, files = fetch_pr(ref)
        print(render_review(args.pr, pr, files))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
