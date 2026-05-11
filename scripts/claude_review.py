#!/usr/bin/env python3
"""Generate a structured Markdown review from a GitHub pull request diff."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


PR_URL = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")
FILE_HEADER = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_LINE = re.compile(r"^@@")
MAX_DIFF_CHARS = 45_000
REQUIRED_HEADINGS = (
    "## PR Review",
    "### Summary of Changes",
    "### Identified Risks",
    "### Improvement Suggestions",
    "### Confidence Score:",
)


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


@dataclass
class PullRequestData:
    ref: PullRequestRef
    title: str
    author: str
    additions: int
    deletions: int
    changed_files: int
    diff: str
    url: str


def parse_pr_url(value: str) -> PullRequestRef:
    match = PR_URL.match(value)
    if not match:
        raise ValueError("Expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestRef(owner=owner, repo=repo, number=int(number))


def github_request(url: str, accept: str) -> bytes:
    headers = {
        "Accept": accept,
        "User-Agent": "claude-review",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return response.read()


def fetch_pull_request(ref: PullRequestRef) -> PullRequestData:
    api_base = f"https://api.github.com/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
    metadata = json.loads(github_request(api_base, "application/vnd.github+json"))
    diff = github_request(api_base, "application/vnd.github.v3.diff").decode("utf-8", errors="replace")
    return PullRequestData(
        ref=ref,
        title=metadata.get("title", f"PR #{ref.number}"),
        author=metadata.get("user", {}).get("login", "unknown"),
        additions=int(metadata.get("additions", 0)),
        deletions=int(metadata.get("deletions", 0)),
        changed_files=int(metadata.get("changed_files", 0)),
        diff=diff,
        url=metadata.get("html_url", f"https://github.com/{ref.owner}/{ref.repo}/pull/{ref.number}"),
    )


def changed_paths(diff: str) -> list[str]:
    paths: list[str] = []
    for line in diff.splitlines():
        match = FILE_HEADER.match(line)
        if match and match.group(1) != "/dev/null":
            paths.append(match.group(1))
    return sorted(set(paths))


def count_hunks(diff: str) -> int:
    return sum(1 for line in diff.splitlines() if HUNK_LINE.match(line))


def contains_any(values: Iterable[str], needles: Iterable[str]) -> bool:
    lowered = [value.lower() for value in values]
    return any(needle in value for value in lowered for needle in needles)


def markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def summary(pr: PullRequestData, paths: list[str]) -> str:
    file_preview = ", ".join(paths[:4])
    if len(paths) > 4:
        file_preview += f", and {len(paths) - 4} more"

    return (
        f"This PR, **{pr.title}**, changes {pr.changed_files} file(s) with "
        f"{pr.additions} additions and {pr.deletions} deletions. "
        f"The main touched paths are: {file_preview or 'no paths detected from the diff'}. "
        "The review below is based on file names, diff hunks, and risk patterns visible in the patch."
    )


def risks(pr: PullRequestData, paths: list[str]) -> list[str]:
    diff_lower = pr.diff.lower()
    total_delta = pr.additions + pr.deletions
    risks_found: list[str] = []

    if total_delta > 800:
        risks_found.append("Large diff size raises review risk; split or add extra verification notes if possible.")
    if contains_any(paths, ["migration", "schema", ".sql", "prisma", "drizzle"]):
        risks_found.append("Database or migration files changed; verify rollback behavior and compatibility with existing data.")
    if contains_any(paths, ["package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"]):
        risks_found.append("Dependency or lockfile changes can affect installs and CI reproducibility.")
    if contains_any(paths, ["auth", "session", "token", "permission", "security"]):
        risks_found.append("Authentication or authorization surface appears to be touched; check access-control edge cases.")
    if "delete from" in diff_lower and " where " not in diff_lower:
        risks_found.append("The diff includes a DELETE FROM statement without an obvious WHERE clause.")
    if not any(re.search(r"(^|/)(test|tests|__tests__|spec|fixtures?)(/|$)", path.lower()) for path in paths):
        risks_found.append("No test files are visible in the diff; behavioral changes may be under-verified.")
    if not risks_found:
        risks_found.append("No high-risk pattern was detected from file names and diff text; still validate behavior manually.")

    return risks_found


def suggestions(pr: PullRequestData, paths: list[str]) -> list[str]:
    suggestions_found: list[str] = []

    if not any(re.search(r"(^|/)(test|tests|__tests__|spec|fixtures?)(/|$)", path.lower()) for path in paths):
        suggestions_found.append("Add or link a focused test that exercises the changed behavior.")
    if contains_any(paths, ["readme", "docs/", ".md"]):
        suggestions_found.append("Preview the Markdown or docs output to catch formatting regressions.")
    if contains_any(paths, [".github/workflows", "action.yml", "Dockerfile"]):
        suggestions_found.append("Run the workflow or container build in a fork before merge.")
    if pr.additions + pr.deletions > 800:
        suggestions_found.append("Consider splitting mechanical changes from behavioral changes to simplify review.")
    if not suggestions_found:
        suggestions_found.append("Keep the PR description tied to the verification commands reviewers can reproduce.")

    return suggestions_found


def confidence(pr: PullRequestData, paths: list[str]) -> str:
    total_delta = pr.additions + pr.deletions
    if not pr.diff.strip() or not paths:
        return "Low"
    if total_delta <= 500 and any(re.search(r"(^|/)(test|tests|__tests__|spec|fixtures?)(/|$)", path.lower()) for path in paths):
        return "High"
    if total_delta <= 1000:
        return "Medium"
    return "Low"


def build_review(pr: PullRequestData) -> str:
    paths = changed_paths(pr.diff)
    return "\n".join(
        [
            "## PR Review",
            "",
            f"Source: {pr.url}",
            f"Author: @{pr.author}",
            "",
            "### Summary of Changes",
            summary(pr, paths),
            "",
            "### Identified Risks",
            markdown_list(risks(pr, paths)),
            "",
            "### Improvement Suggestions",
            markdown_list(suggestions(pr, paths)),
            "",
            f"### Confidence Score: {confidence(pr, paths)}",
            "",
            f"_Generated from {len(paths)} changed path(s) and {count_hunks(pr.diff)} diff hunk(s)._",
        ]
    )


def truncate_diff(diff: str) -> str:
    if len(diff) <= MAX_DIFF_CHARS:
        return diff
    omitted = len(diff) - MAX_DIFF_CHARS
    return f"{diff[:MAX_DIFF_CHARS]}\n\n[diff truncated: {omitted} characters omitted]"


def claude_prompt(pr: PullRequestData) -> str:
    paths = changed_paths(pr.diff)
    path_list = "\n".join(f"- {path}" for path in paths) or "- No changed paths detected"
    return f"""You are a Claude Code pull request review agent.

Review the GitHub PR diff below. Ground every claim in the diff. Do not invent behavior not visible in the patch.
Use plain ASCII Markdown. Bullet lists must use `- ` hyphen bullets.

Return only Markdown with exactly these sections:

## PR Review
Source: <PR URL>
Author: <GitHub handle>

### Summary of Changes
Write 2-3 concise sentences.

### Identified Risks
Use bullets. Include "No clear risks found from this diff." only if there are no concrete risks.

### Improvement Suggestions
Use bullets. Suggestions must be actionable for the author or maintainer.

### Confidence Score: Low | Medium | High
Choose one confidence level and add one short sentence explaining it.

PR metadata:
- URL: {pr.url}
- Title: {pr.title}
- Author: @{pr.author}
- Files changed: {pr.changed_files}
- Additions: {pr.additions}
- Deletions: {pr.deletions}

Changed paths:
{path_list}

Diff:
```diff
{truncate_diff(pr.diff)}
```
"""


def validate_claude_review(markdown: str) -> bool:
    if not markdown.strip():
        return False
    if not all(heading in markdown for heading in REQUIRED_HEADINGS):
        return False
    return bool(re.search(r"### Confidence Score:\s*(Low|Medium|High)\b", markdown))


def build_claude_review(pr: PullRequestData) -> str | None:
    executable = shutil.which("claude")
    if os.environ.get("CLAUDE_REVIEW_OFFLINE") == "1" or not executable:
        return None

    timeout = int(os.environ.get("CLAUDE_REVIEW_TIMEOUT", "180"))
    try:
        result = subprocess.run(
            [executable, "-p"],
            input=claude_prompt(pr),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    review = result.stdout.strip()
    if not validate_claude_review(review):
        return None
    return review


def post_comment(pr: PullRequestData, body: str) -> str:
    if not os.environ.get("GITHUB_TOKEN"):
        raise RuntimeError("GITHUB_TOKEN is required to post a PR comment")
    comments_url = f"https://api.github.com/repos/{pr.ref.owner}/{pr.ref.repo}/issues/{pr.ref.number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Content-Type": "application/json",
        "User-Agent": "claude-review",
    }
    request = Request(comments_url, data=payload, headers=headers, method="POST")
    with urlopen(request, timeout=30) as response:
        created = json.loads(response.read())
    return created.get("html_url", comments_url)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument(
        "--engine",
        choices=("auto", "claude", "heuristic"),
        default=os.environ.get("CLAUDE_REVIEW_ENGINE", "auto"),
        help="Review engine. auto uses Claude Code when available and falls back to the local heuristic.",
    )
    parser.add_argument("--output", help="Write Markdown review to this file instead of stdout only")
    parser.add_argument("--post", action="store_true", help="Post the review as a GitHub issue comment. Requires GITHUB_TOKEN.")
    args = parser.parse_args(argv)

    try:
        pr = fetch_pull_request(parse_pr_url(args.pr))
        review = None
        if args.engine in ("auto", "claude"):
            review = build_claude_review(pr)
            if review is None and args.engine == "claude":
                raise RuntimeError("Claude Code review engine is unavailable or returned invalid Markdown")
        if review is None:
            review = build_review(pr)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(review)
                handle.write("\n")
        if args.post:
            url = post_comment(pr, review)
            print(f"Posted review: {url}")
        else:
            print(review)
        return 0
    except (HTTPError, URLError, ValueError, RuntimeError) as error:
        print(f"claude-review: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
