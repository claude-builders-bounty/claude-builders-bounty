#!/usr/bin/env python3
"""Review a GitHub PR and emit a structured Markdown comment."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


PR_RE = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")


@dataclass(frozen=True)
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    changed_files: int
    additions: int
    deletions: int
    files: list[dict[str, Any]]


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_RE.fullmatch(url.strip())
    if not match:
        raise SystemExit("Expected PR URL like https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def github_json(path: str) -> Any:
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "claude-review"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub API request failed ({exc.code}): {message}") from exc


def load_pull_request(url: str) -> PullRequest:
    owner, repo, number = parse_pr_url(url)
    pr = github_json(f"/repos/{owner}/{repo}/pulls/{number}")
    files = github_json(f"/repos/{owner}/{repo}/pulls/{number}/files?per_page=100")
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=pr.get("title", ""),
        body=pr.get("body") or "",
        changed_files=pr.get("changed_files", len(files)),
        additions=pr.get("additions", sum(file.get("additions", 0) for file in files)),
        deletions=pr.get("deletions", sum(file.get("deletions", 0) for file in files)),
        files=files,
    )


def summarize(pr: PullRequest) -> str:
    filenames = [file["filename"] for file in pr.files[:5]]
    areas = ", ".join(filenames) if filenames else "the repository"
    return (
        f"This PR changes {pr.changed_files} file(s), with {pr.additions} additions "
        f"and {pr.deletions} deletions. The main touched areas are {areas}, so review "
        "should focus on whether those edits match the stated intent and preserve "
        "existing behavior."
    )


def detect_risks(pr: PullRequest) -> list[str]:
    risks: list[str] = []
    filenames = [file["filename"] for file in pr.files]
    total_delta = pr.additions + pr.deletions
    if total_delta > 500:
        risks.append("Large diff size increases the chance that behavior changes are hidden in unrelated edits.")
    if any(name.endswith((".sql", ".sqlite", ".db")) or "migration" in name.lower() for name in filenames):
        risks.append("Database or migration files changed; verify upgrade and rollback expectations with real data.")
    if any(name.endswith((".yml", ".yaml")) and (".github/workflows" in name or "deploy" in name.lower()) for name in filenames):
        risks.append("CI or deployment configuration changed; check secrets, permissions, and trigger scope.")
    if any("auth" in name.lower() or "permission" in name.lower() or "security" in name.lower() for name in filenames):
        risks.append("Authentication, authorization, or security-adjacent files changed; test denied and allowed paths.")
    if any(file.get("status") == "removed" for file in pr.files):
        risks.append("Files were removed; confirm no imports, docs, or runtime paths still reference them.")
    if not risks:
        risks.append("No high-risk file patterns were detected, but reviewer should still verify tests cover the changed behavior.")
    return risks


def suggestions(pr: PullRequest) -> list[str]:
    suggestions = [
        "Run the repository's lint, typecheck, and test commands before merge.",
        "Confirm the PR description includes the user-facing behavior change and manual verification notes.",
    ]
    test_files = [file["filename"] for file in pr.files if re.search(r"(^|/)(test|tests|__tests__)/|\\.test\\.|\\.spec\\.", file["filename"])]
    if not test_files:
        suggestions.insert(0, "Add or identify tests that cover the changed behavior; no obvious test file was modified.")
    if pr.changed_files > 10:
        suggestions.append("Consider splitting unrelated changes so each review has one clear behavioral purpose.")
    return suggestions


def confidence(pr: PullRequest, risks: list[str]) -> str:
    if pr.changed_files <= 4 and pr.additions + pr.deletions <= 150 and len(risks) == 1:
        return "High"
    if pr.changed_files <= 12 and pr.additions + pr.deletions <= 600:
        return "Medium"
    return "Low"


def render_review(pr: PullRequest) -> str:
    risks = detect_risks(pr)
    confidence_score = confidence(pr, risks)
    lines = [
        "## PR Review",
        "",
        "### Summary",
        "",
        summarize(pr),
        "",
        "### Identified Risks",
        "",
    ]
    lines.extend(f"- {risk}" for risk in risks)
    lines.extend(["", "### Improvement Suggestions", ""])
    lines.extend(f"- {suggestion}" for suggestion in suggestions(pr))
    lines.extend(["", f"### Confidence: {confidence_score}", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    args = parser.parse_args(argv)
    pr = load_pull_request(args.pr)
    print(render_review(pr))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
