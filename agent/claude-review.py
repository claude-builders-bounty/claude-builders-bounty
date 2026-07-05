#!/usr/bin/env python3
"""
claude-review.py — Claude Code PR Review Agent

A CLI tool that takes a GitHub PR URL, fetches the diff,
analyzes it using Claude API, and outputs a structured Markdown review.

Usage:
  export ANTHROPIC_API_KEY=sk-xxx
  export GITHUB_TOKEN=ghp_xxx
  claude-review --pr https://github.com/owner/repo/pull/123
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def parse_pr_url(url: str) -> tuple[str, str, str]:
    """Parse a GitHub PR URL into owner, repo, pr_number."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid PR URL: {url}")
    return match.group(1), match.group(2), match.group(3)


def fetch_pr_diff(owner: str, repo: str, pr_number: str) -> str:
    """Fetch the PR diff from GitHub API."""
    token = os.environ.get("GITHUB_TOKEN", "")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def fetch_pr_metadata(owner: str, repo: str, pr_number: str) -> dict:
    """Fetch PR metadata (title, description, files changed)."""
    token = os.environ.get("GITHUB_TOKEN", "")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    # Get changed files
    files_url = data.get("commits_url", "").replace("/commits", "/files")
    files_req = urllib.request.Request(files_url, headers=headers)
    with urllib.request.urlopen(files_req) as resp:
        files_data = json.loads(resp.read().decode("utf-8"))

    return {
        "title": data.get("title", ""),
        "description": data.get("body", "") or "",
        "author": data.get("user", {}).get("login", "unknown"),
        "files_changed": [f["filename"] for f in files_data],
        "additions": data.get("additions", 0),
        "deletions": data.get("deletions", 0),
        "changed_files": data.get("changed_files", 0),
    }


def analyze_with_claude(diff: str, metadata: dict) -> str:
    """Send diff to Claude API for analysis."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Fallback: do local analysis (no API key)
        return local_analysis(diff, metadata)

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    if not diff.strip():
        diff_placeholder = "No diff content available."
    else:
        diff_placeholder = diff[:50000]  # Truncate to avoid token limits

    prompt = f"""You are a senior code reviewer. Review the following PR and provide a structured analysis.

PR Title: {metadata['title']}
PR Description: {metadata['description'][:2000]}
Author: {metadata['author']}
Files Changed: {', '.join(metadata['files_changed'][:30])}
Stats: +{metadata['additions']} / -{metadata['deletions']} across {metadata['changed_files']} files

DIFF:
```
{diff_placeholder}
```

Please provide your review in the following structured Markdown format:

## 📋 Summary
2-3 sentences summarizing what this PR does.

## ⚠️ Identified Risks
- Risk 1: ...
- Risk 2: ...

## 💡 Improvement Suggestions
- Suggestion 1: ...
- Suggestion 2: ...

## ✅ Confidence Score
**High / Medium / Low**

Base your confidence on: how well the changes match the description, test coverage evidence, code quality, and potential edge cases handled."""

    data = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    return result["content"][0]["text"]


def local_analysis(diff: str, metadata: dict) -> str:
    """Fallback local analysis when no API key is available."""
    lines = diff.split("\n")
    added = [l for l in lines if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in lines if l.startswith("-") and not l.startswith("---")]

    summary = (
        f"This PR by **{metadata['author']}** makes changes across "
        f"{metadata['changed_files']} file(s), adding {metadata['additions']} "
        f"and removing {metadata['deletions']} lines."
    )

    risks = []
    suggestions = []

    # Check for common risk patterns
    if any("TODO" in l or "FIXME" in l or "HACK" in l for l in added):
        risks.append("Contains TODO/FIXME/HACK comments — may indicate incomplete work.")
    if any("print(" in l or "console.log" in l for l in added):
        risks.append("Contains debug print/console.log statements that should be removed.")
    if any("password" in l.lower() or "secret" in l.lower() or "token" in l.lower() for l in added):
        risks.append("Potential hardcoded secrets in the diff — verify no credentials are exposed.")
    if any("rm -rf" in l or "DROP TABLE" in l for l in added):
        risks.append("Contains destructive operations — double-check intent.")
    if not added and not removed:
        risks.append("No actual code changes detected in the diff.")
    if not metadata["description"].strip():
        risks.append("PR has no description — unclear what the intent is.")

    if risks:
        suggestions.append("Address the identified risks before merging.")
    suggestions.append("Consider adding or updating tests to cover the changes.")

    # Confidence assessment
    has_tests = any("test" in f.lower() for f in metadata["files_changed"])
    has_description = bool(metadata["description"].strip())
    confidence = "High" if (has_tests and has_description and len(risks) == 0) else \
                 "Medium" if (has_description and len(risks) <= 1) else "Low"

    # Build output
    output = "## 📋 Summary\n\n"
    output += f"{summary}\n\n"

    output += f"**Files changed:** {', '.join(metadata['files_changed'][:10])}\n\n"

    output += "## ⚠️ Identified Risks\n\n"
    if risks:
        for r in risks:
            output += f"- {r}\n"
    else:
        output += "- No significant risks identified.\n"
    output += "\n"

    output += "## 💡 Improvement Suggestions\n\n"
    for s in suggestions:
        output += f"- {s}\n"
    output += "\n"

    output += "## ✅ Confidence Score\n\n"
    output += f"**{confidence}**\n\n"

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — Analyze GitHub PRs with structured output"
    )
    parser.add_argument(
        "--pr", "-p",
        required=True,
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: print to stdout)"
    )
    args = parser.parse_args()

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    metadata = fetch_pr_metadata(owner, repo, pr_number)
    diff = fetch_pr_diff(owner, repo, pr_number)

    print("Analyzing changes...", file=sys.stderr)
    review = analyze_with_claude(diff, metadata)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
            f.write(f"\n---\n*Review generated by claude-review-agent for {args.pr}*\n")
        print(f"Review written to {args.output}")
    else:
        print(review)
        print(f"\n---\n*Review generated by claude-review-agent for {args.pr}*")


if __name__ == "__main__":
    main()
