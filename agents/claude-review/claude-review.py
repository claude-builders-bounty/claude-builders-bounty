#!/usr/bin/env python3
"""claude-review: AI-powered PR review agent.

Takes a PR URL, fetches the diff, analyzes it, and outputs a structured
Markdown review comment.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --post
  claude-review --diff-file changes.diff

Requires:
  - GITHUB_TOKEN environment variable (for fetching PR diffs and posting comments)
  - ANTHROPIC_API_KEY environment variable (for Claude API)
  - Or: claude CLI installed (used as fallback for analysis)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class PRInfo:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    diff: str
    additions: int
    deletions: int
    changed_files: int


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        print(f"Error: Invalid PR URL: {url}", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2), int(match.group(3))


def github_api(path: str, token: str, method: str = "GET", data: Optional[dict] = None) -> dict:
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_pr(owner: str, repo: str, number: int, token: str) -> PRInfo:
    pr = github_api(f"/repos/{owner}/{repo}/pulls/{number}", token)
    diff_url = pr.get("diff_url")
    if not diff_url:
        print("Error: Could not get diff URL from PR", file=sys.stderr)
        sys.exit(1)

    req = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review", "Authorization": f"token {token}"})
    with urllib.request.urlopen(req) as resp:
        diff = resp.read().decode("utf-8")

    return PRInfo(
        owner=owner,
        repo=repo,
        number=number,
        title=pr.get("title", ""),
        body=pr.get("body", ""),
        diff=diff,
        additions=pr.get("additions", 0),
        deletions=pr.get("deletions", 0),
        changed_files=pr.get("changed_files", 0),
    )


def analyze_with_claude_cli(diff: str, pr_title: str, pr_body: str) -> str:
    prompt = f"""You are a senior software engineer reviewing a pull request. Analyze the following PR diff and provide a structured review.

PR Title: {pr_title}
PR Description: {pr_body}

Diff:
```
{diff[:50000]}
```

Respond with EXACTLY this Markdown format (no preamble, no postamble):

## Summary

[2-3 sentences summarizing what this PR changes]

## Identified Risks

- [Risk 1]
- [Risk 2]
- (list all risks you find, or write "None identified" if clean)

## Improvement Suggestions

- [Suggestion 1]
- [Suggestion 2]
- (list actionable improvements, or write "None" if clean)

## Confidence Score

**[Low / Medium / High]** — [1 sentence explaining the confidence level]
"""

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return fallback_analysis(diff, pr_title, pr_body, result.stderr)
    return result.stdout.strip()


def analyze_with_anthropic_api(diff: str, pr_title: str, pr_body: str, api_key: str) -> str:
    prompt = f"""You are a senior software engineer reviewing a pull request. Analyze the following PR diff and provide a structured review.

PR Title: {pr_title}
PR Description: {pr_body}

Diff:
```
{diff[:50000]}
```

Respond with EXACTLY this Markdown format (no preamble, no postamble):

## Summary

[2-3 sentences summarizing what this PR changes]

## Identified Risks

- [Risk 1]
- [Risk 2]
- (list all risks you find, or write "None identified" if clean)

## Improvement Suggestions

- [Suggestion 1]
- [Suggestion 2]
- (list actionable improvements, or write "None" if clean)

## Confidence Score

**[Low / Medium / High]** — [1 sentence explaining the confidence level]
"""

    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"].strip()


def fallback_analysis(diff: str, pr_title: str, pr_body: str, error: str = "") -> str:
    lines = diff.split("\n")
    added = [l for l in lines if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in lines if l.startswith("-") and not l.startswith("---")]
    files = set()
    for l in lines:
        if l.startswith("diff --git"):
            parts = l.split(" ")
            if len(parts) >= 4:
                files.add(parts[-1].lstrip("b/"))

    risks = []
    diff_text = "\n".join(added)
    if re.search(r"(password|secret|api_key|token)\s*=", diff_text, re.IGNORECASE):
        risks.append("- Possible hardcoded secret or credential detected in added lines")
    if re.search(r"eval\s*\(", diff_text):
        risks.append("- Use of `eval()` detected — security risk")
    if re.search(r"(DROP\s+TABLE|DELETE\s+FROM\s+[^;]*;)", diff_text, re.IGNORECASE):
        risks.append("- Destructive SQL operation detected in diff")
    if re.search(r"(TODO|FIXME|HACK|XXX)", diff_text):
        risks.append("- Unresolved TODO/FIXME comments in added code")
    if any("console.log" in l for l in added):
        risks.append("- Debug `console.log` statements in added code")
    if not risks:
        risks.append("- None identified")

    suggestions = []
    if len(added) > 200:
        suggestions.append("- Large diff — consider splitting into smaller PRs for easier review")
    if not any("test" in f.lower() for f in files) and len(added) > 20:
        suggestions.append("- No test files changed — consider adding tests for new functionality")
    if not suggestions:
        suggestions.append("- None")

    confidence = "Medium"
    if not risks or risks == ["- None identified"]:
        confidence = "High"
    elif len(risks) > 3:
        confidence = "Low"

    return f"""## Summary

This PR ("{pr_title}") modifies {len(files)} file(s) with {len(added)} addition(s) and {len(removed)} deletion(s). {pr_body[:150] + "..." if len(pr_body) > 150 else pr_body}

## Identified Risks

{chr(10).join(risks)}

## Improvement Suggestions

{chr(10).join(suggestions)}

## Confidence Score

**{confidence}** — {"Static analysis fallback used (Claude CLI/API unavailable" + (f": {error[:100]}" if error else "") + ")." if error else "Review based on pattern analysis of the diff."}
"""


def post_review_comment(owner: str, repo: str, number: int, review: str, token: str) -> str:
    body = f"## 🤖 Automated PR Review\n\n{review}\n\n---\n*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty)*"
    result = github_api(
        f"/repos/{owner}/{repo}/issues/{number}/comments",
        token,
        method="POST",
        data={"body": body},
    )
    return result.get("html_url", "")


def main():
    parser = argparse.ArgumentParser(description="AI-powered PR review agent")
    parser.add_argument("--pr", required=False, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", required=False, help="Path to a diff file to review instead of fetching from GitHub")
    parser.add_argument("--post", action="store_true", help="Post the review as a comment on the PR")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown", help="Output format")
    args = parser.parse_args()

    if not args.pr and not args.diff_file:
        parser.error("Either --pr or --diff-file is required")

    token = os.environ.get("GITHUB_TOKEN", "")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if args.diff_file:
        with open(args.diff_file) as f:
            diff = f.read()
        pr_info = PRInfo("", "", 0, "Local diff review", "", diff, 0, 0, 0)
    else:
        if not token:
            print("Error: GITHUB_TOKEN environment variable required for --pr", file=sys.stderr)
            sys.exit(1)
        owner, repo, number = parse_pr_url(args.pr)
        pr_info = fetch_pr(owner, repo, number, token)

    # Try Claude CLI first, then API, then fallback
    review = ""
    try:
        review = analyze_with_claude_cli(pr_info.diff, pr_info.title, pr_info.body)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        if api_key:
            try:
                review = analyze_with_anthropic_api(pr_info.diff, pr_info.title, pr_info.body, api_key)
            except Exception as e:
                review = fallback_analysis(pr_info.diff, pr_info.title, pr_info.body, str(e))
        else:
            review = fallback_analysis(pr_info.diff, pr_info.title, pr_info.body, "No Claude CLI or API key available")

    if args.post and args.pr:
        if not token:
            print("Error: GITHUB_TOKEN required for --post", file=sys.stderr)
            sys.exit(1)
        url = post_review_comment(owner, repo, number, review, token)
        if args.output == "json":
            print(json.dumps({"review": review, "comment_url": url}))
        else:
            print(f"Review posted: {url}")
            print()
            print(review)
    else:
        if args.output == "json":
            print(json.dumps({
                "pr": args.pr or "local",
                "title": pr_info.title,
                "additions": pr_info.additions,
                "deletions": pr_info.deletions,
                "changed_files": pr_info.changed_files,
                "review": review,
            }))
        else:
            print(review)


if __name__ == "__main__":
    main()
