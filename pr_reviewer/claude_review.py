#!/usr/bin/env python3
"""Generate and optionally post a structured Markdown review for a GitHub PR."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")
FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
HUNK_RE = re.compile(r"^@@ ")


@dataclass
class DiffStats:
    files: list[str]
    additions: int
    deletions: int
    hunks: int
    changed_lines: list[str]


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("Expected PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def request_text(url: str, *, token: str | None = None, accept: str = "text/plain") -> str:
    headers = {
        "Accept": accept,
        "User-Agent": "claude-review-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub request failed: HTTP {exc.code} {body}") from exc


def fetch_diff(pr_url: str, token: str | None) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    return request_text(api_url, token=token, accept="application/vnd.github.v3.diff")


def fetch_pr_metadata(pr_url: str, token: str | None) -> dict:
    owner, repo, number = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    raw = request_text(api_url, token=token, accept="application/vnd.github+json")
    return json.loads(raw)


def post_comment(pr_url: str, markdown: str, token: str) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    payload = json.dumps({"body": markdown}).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "claude-review-agent",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))
        return body.get("html_url", api_url)


def diff_stats(diff: str) -> DiffStats:
    files: list[str] = []
    changed_lines: list[str] = []
    additions = 0
    deletions = 0
    hunks = 0

    for line in diff.splitlines():
        file_match = FILE_RE.match(line)
        if file_match and file_match.group(1) != "/dev/null":
            files.append(file_match.group(1))
            continue

        if HUNK_RE.match(line):
            hunks += 1
            continue

        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
            changed_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
            changed_lines.append(line[1:])

    return DiffStats(files=files, additions=additions, deletions=deletions, hunks=hunks, changed_lines=changed_lines)


def summarize(metadata: dict, stats: DiffStats) -> str:
    title = metadata.get("title") or "Untitled PR"
    author = (metadata.get("user") or {}).get("login") or "unknown author"
    file_count = len(stats.files)
    change_count = stats.additions + stats.deletions
    first_sentence = (
        f"This PR, **{title}**, was opened by `{author}` and changes "
        f"{file_count} file(s) with {stats.additions} additions and {stats.deletions} deletions."
    )
    second_sentence = (
        f"The diff spans {stats.hunks} hunk(s), so the review focus is on behavior changes, "
        "test coverage, and operational risk."
        if change_count
        else "The PR has no visible diff in the fetched patch."
    )
    return f"{first_sentence} {second_sentence}"


def contains_any(lines: Iterable[str], patterns: Iterable[str]) -> bool:
    joined = "\n".join(lines).lower()
    return any(pattern in joined for pattern in patterns)


def identify_risks(stats: DiffStats) -> list[str]:
    risks: list[str] = []
    files = stats.files
    lines = stats.changed_lines

    if stats.additions + stats.deletions > 800:
        risks.append("Large diff size may hide unrelated behavior changes; split or add focused reviewer notes if possible.")
    if any(path.endswith((".sql", "schema.prisma")) or "migration" in path.lower() for path in files):
        risks.append("Database/schema changes require migration rollback notes and data compatibility checks.")
    if any(path.startswith(".github/workflows/") for path in files):
        risks.append("CI workflow changes can affect release safety; verify permissions, triggers, and secrets exposure.")
    if contains_any(lines, ["process.env", "api_key", "secret", "token", "password"]):
        risks.append("Secret-handling code changed; verify no credentials are logged, exposed to clients, or committed.")
    if contains_any(lines, ["dangerouslysetinnerhtml", "innerhtml", "eval(", "exec(", "shell=true"]):
        risks.append("Dynamic execution or HTML injection patterns changed; review input sanitization carefully.")
    if contains_any(lines, ["delete from", "truncate", "drop table", "rm -rf"]):
        risks.append("Destructive operation detected; ensure it is guarded, scoped, and covered by tests.")
    if not any(("test" in path.lower() or "spec" in path.lower()) for path in files):
        risks.append("No test files changed; confirm the PR is low-risk or add regression coverage.")

    return risks or ["No major structural risks were detected from the diff heuristics."]


def suggestions(stats: DiffStats) -> list[str]:
    suggestions_list = [
        "Confirm the PR description explains user-visible behavior and any migration or deployment steps.",
        "Run the repository's lint, typecheck, and test commands before merge.",
    ]

    if not any(("test" in path.lower() or "spec" in path.lower()) for path in stats.files):
        suggestions_list.append("Add or update tests for the most important changed path.")
    if len(stats.files) > 10:
        suggestions_list.append("Group the file changes in the PR description so reviewers can audit by area.")
    if any(path.endswith((".md", ".mdx")) for path in stats.files):
        suggestions_list.append("Preview documentation rendering and check links before merge.")

    return suggestions_list


def confidence(stats: DiffStats) -> str:
    total = stats.additions + stats.deletions
    has_tests = any(("test" in path.lower() or "spec" in path.lower()) for path in stats.files)
    if total <= 250 and has_tests:
        return "High"
    if total <= 600:
        return "Medium"
    return "Low"


def render_review(pr_url: str, metadata: dict, diff: str) -> str:
    stats = diff_stats(diff)
    risk_items = "\n".join(f"- {item}" for item in identify_risks(stats))
    suggestion_items = "\n".join(f"- {item}" for item in suggestions(stats))
    file_items = "\n".join(f"- `{path}`" for path in stats.files[:12])
    if len(stats.files) > 12:
        file_items += f"\n- ...and {len(stats.files) - 12} more"

    return f"""## Claude PR Review

PR: {pr_url}

### Summary

{summarize(metadata, stats)}

### Files Reviewed

{file_items or "- No files found in diff."}

### Identified Risks

{risk_items}

### Improvement Suggestions

{suggestion_items}

### Confidence

**{confidence(stats)}**
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument("--output", help="Write Markdown review to this file")
    parser.add_argument("--post", action="store_true", help="Post the review as a GitHub PR comment")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token. Defaults to GITHUB_TOKEN")
    args = parser.parse_args()

    diff = fetch_diff(args.pr, args.token)
    metadata = fetch_pr_metadata(args.pr, args.token)
    review = render_review(args.pr, metadata, diff)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as output_file:
            output_file.write(review)

    print(review)

    if args.post:
        if not args.token:
            print("--post requires GITHUB_TOKEN or --token", file=sys.stderr)
            return 2
        url = post_comment(args.pr, review, args.token)
        print(f"Posted review comment: {url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
