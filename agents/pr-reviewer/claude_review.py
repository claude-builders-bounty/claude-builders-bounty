#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    changed_files: int
    additions: int
    deletions: int
    html_url: str


def parse_pr_url(url):
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
    if not match:
        raise ValueError("Expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def request(url, accept="application/vnd.github+json", method="GET", body=None):
    headers = {
        "Accept": accept,
        "User-Agent": "claude-pr-review-agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return json.loads(raw.decode("utf-8"))
            return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {error.code} {details}") from error


def fetch_pull_request(owner, repo, number):
    data = request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=data.get("title", ""),
        body=data.get("body") or "",
        author=(data.get("user") or {}).get("login", "unknown"),
        changed_files=int(data.get("changed_files") or 0),
        additions=int(data.get("additions") or 0),
        deletions=int(data.get("deletions") or 0),
        html_url=data.get("html_url", ""),
    )


def fetch_diff(owner, repo, number):
    return request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
        accept="application/vnd.github.v3.diff",
    )


def changed_paths(diff):
    paths = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                paths.append(parts[1].strip())
    return paths


def summarize(pr, paths):
    file_preview = ", ".join(paths[:5]) if paths else "the submitted files"
    sentences = [
        f"This PR changes {pr.changed_files} file(s) with {pr.additions} additions and {pr.deletions} deletions.",
        f"The visible diff focuses on {file_preview}.",
    ]
    if pr.body.strip():
        sentences.append("The PR description provides additional implementation context for reviewers.")
    return " ".join(sentences[:3])


def risk_signals(diff, paths, pr):
    lowered = diff.lower()
    risks = []
    if pr.changed_files >= 15 or pr.additions + pr.deletions >= 800:
        risks.append("Large diff size may make manual review harder; consider splitting follow-up changes if behavior is broad.")
    if any(path.endswith((".sql", ".db", "migration.py")) or "migration" in path.lower() for path in paths):
        risks.append("Database or migration-related files changed; verify rollback and data compatibility.")
    if any(word in lowered for word in ["auth", "token", "secret", "password", "permission"]):
        risks.append("Security-sensitive terms appear in the diff; verify secret handling and authorization boundaries.")
    if any(path.endswith((".yml", ".yaml")) and ".github/workflows/" in path for path in paths):
        risks.append("GitHub workflow changes can affect CI permissions; review token scopes and trigger safety.")
    if "delete from" in lowered or "drop table" in lowered or "truncate" in lowered:
        risks.append("Destructive SQL appears in the diff; confirm it is guarded, reversible, and tested.")
    if not risks:
        risks.append("No major risks identified from the diff alone.")
    return risks


def suggestions(diff, paths):
    lowered = diff.lower()
    suggestions = []
    has_tests = any("test" in path.lower() or "spec" in path.lower() for path in paths)
    if not has_tests:
        suggestions.append("Add or update focused tests for the changed behavior where the project has a test harness.")
    if "readme" not in " ".join(path.lower() for path in paths) and any(path.endswith((".py", ".js", ".ts", ".tsx")) for path in paths):
        suggestions.append("Document any new command, configuration, or operational behavior introduced by the code.")
    if "todo" in lowered or "fixme" in lowered:
        suggestions.append("Resolve or track TODO/FIXME markers before merging.")
    if not suggestions:
        suggestions.append("Keep the PR description aligned with the final diff so reviewers can verify intent quickly.")
    return suggestions


def confidence(pr, diff, risks):
    total_changes = pr.additions + pr.deletions
    if total_changes <= 250 and risks == ["No major risks identified from the diff alone."]:
        return "High"
    if total_changes <= 800:
        return "Medium"
    return "Low"


def render_review(pr, diff):
    paths = changed_paths(diff)
    risks = risk_signals(diff, paths, pr)
    advice = suggestions(diff, paths)
    score = confidence(pr, diff, risks)
    lines = [
        "## Summary",
        "",
        summarize(pr, paths),
        "",
        "## Identified Risks",
        "",
    ]
    lines.extend(f"- {item}" for item in risks)
    lines.extend(["", "## Improvement Suggestions", ""])
    lines.extend(f"- {item}" for item in advice)
    lines.extend(["", "## Confidence", "", score, ""])
    return "\n".join(lines)


def post_comment(pr, body):
    request(
        f"https://api.github.com/repos/{pr.owner}/{pr.repo}/issues/{pr.number}/comments",
        method="POST",
        body={"body": body},
    )


def main():
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL.")
    parser.add_argument("--output", help="Optional file path for the Markdown review.")
    parser.add_argument("--post-comment", action="store_true", help="Post the review as a GitHub PR comment.")
    args = parser.parse_args()

    owner, repo, number = parse_pr_url(args.pr)
    pr = fetch_pull_request(owner, repo, number)
    diff = fetch_diff(owner, repo, number)
    review = render_review(pr, diff)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(review)
    else:
        print(review)

    if args.post_comment:
        post_comment(pr, review)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
