#!/usr/bin/env python3
"""
claude-review.py - Claude Code sub-agent that reviews GitHub PRs and outputs structured Markdown.

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123
    python3 claude-review.py --pr OWNER/REPO/123

Output: Structured Markdown review with:
- Summary of Changes (2-3 sentences)
- Identified Risks (list)
- Improvement Suggestions (list)
- Confidence Score (Low/Medium/High)
- Overall Verdict (Approve/Changes requested/Comment)
"""

import argparse
import json
import os
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

GITHUB_API = "https://api.github.com"


def fetch_pr(owner, repo, pr_number, token=None):
    """Fetch PR data from GitHub API."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = Request(url, headers=headers)
    with urlopen(req) as resp:
        return json.loads(resp.read().decode())


def fetch_pr_diff(owner, repo, pr_number, token=None):
    """Fetch PR diff from GitHub API."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = Request(url, headers=headers)
    with urlopen(req) as resp:
        return resp.read().decode()


def call_claude(pr_data, diff, token=None):
    """Call Claude Code CLI for review."""
    title = pr_data.get("title", "")
    body = pr_data.get("body", "") or ""
    base = pr_data.get("base", {}).get("ref", "")
    head = pr_data.get("head", {}).get("ref", "")
    
    # Truncate diff for token limits
    diff_truncated = diff[:60000] if len(diff) > 60000 else diff
    
    prompt = f"""Review this GitHub PR and produce structured Markdown output.

## PR Title
{title}

## PR Body
{body[:2000]}

## Diff (truncated to 60K chars)
```diff
{diff_truncated}
```

## Output Format (use exactly these sections)

### Summary of Changes
[2-3 sentences describing what this PR does]

### Identified Risks
- [List potential issues: breaking changes, edge cases, security, performance, etc.]

### Improvement Suggestions
- [List concrete suggestions to improve code quality, tests, docs, etc.]

### Confidence Score
**Low** / **Medium** / **High** — [brief justification]

### Overall Verdict
**Approve** / **Changes Requested** / **Comment** — [brief justification]
"""
    
    # Try to use Claude Code CLI
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Fallback: generate basic review without LLM
    return generate_basic_review(pr_data, diff)


def generate_basic_review(pr_data, diff):
    """Generate a basic review without LLM (fallback)."""
    title = pr_data.get("title", "")
    files_changed = pr_data.get("changed_files", 0)
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)
    
    return f"""### Summary of Changes
PR "{title}" modifies {files_changed} files with +{additions}/-{deletions} lines.

### Identified Risks
- Verify all changed files are intentional
- Check for breaking changes in public APIs
- Review test coverage for new functionality
- Validate any new dependencies or imports

### Improvement Suggestions
- Add tests for new functionality
- Update documentation if public API changed
- Consider edge cases and error handling
- Run linter and formatter

### Confidence Score
**Medium** — Basic review completed. Full review requires LLM access.

### Overall Verdict
**Comment** — Manual review recommended for production code.
"""


def parse_pr_url(pr_arg):
    """Parse PR argument in form 'OWNER/REPO/NUMBER' or full URL."""
    if pr_arg.startswith("http"):
        # https://github.com/owner/repo/pull/123
        parts = pr_arg.rstrip("/").split("/")
        owner = parts[-4]
        repo = parts[-3]
        number = int(parts[-1])
    else:
        parts = pr_arg.split("/")
        owner = parts[0]
        repo = parts[1]
        number = int(parts[2])
    return owner, repo, number


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR reviewer")
    parser.add_argument("--pr", required=True, help="PR URL or OWNER/REPO/NUMBER")
    parser.add_argument("--token", help="GitHub token (or use GITHUB_TOKEN env)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Warning: No GitHub token. Rate limits may apply.", file=sys.stderr)
    
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except (ValueError, IndexError) as e:
        print(f"Error: Invalid PR argument '{args.pr}': {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Fetching PR {owner}/{repo}#{pr_number}...", file=sys.stderr)
    
    try:
        pr_data = fetch_pr(owner, repo, pr_number, token)
        diff = fetch_pr_diff(owner, repo, pr_number, token)
    except HTTPError as e:
        print(f"Error fetching PR: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Calling Claude for review...", file=sys.stderr)
    review = call_claude(pr_data, diff, token)
    
    # Print header
    header = f"# PR Review: {owner}/{repo}#{pr_number}\n\n"
    header += f"**Title:** {pr_data.get('title', '')}\n\n"
    header += f"**Author:** {pr_data.get('user', {}).get('login', 'unknown')}\n\n"
    header += f"**URL:** https://github.com/{owner}/{repo}/pull/{pr_number}\n\n"
    header += "---\n\n"
    
    output = header + review
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
