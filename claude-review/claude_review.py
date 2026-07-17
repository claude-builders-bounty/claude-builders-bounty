#!/usr/bin/env python3
"""claude-review: AI-powered PR reviewer using Claude."""

import argparse
import json
import os
import re
import sys
from urllib.parse import urlparse

try:
    import anthropic
except ImportError:
    print("Error: anthropic package required. Install with: pip install anthropic", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests package required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    # Supports: https://github.com/owner/repo/pull/123
    #           github.com/owner/repo/pull/123
    #           owner/repo#123
    pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, pr_url)
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    # Short form: owner/repo#123
    short = r"([^/]+)/([^#]+)#(\d+)"
    match = re.match(short, pr_url)
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    raise ValueError(f"Cannot parse PR URL: {pr_url}")


def fetch_pr_metadata(owner: str, repo: str, pr_number: int, token: str | None = None) -> dict:
    """Fetch PR metadata from GitHub API."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str | None = None) -> str:
    """Fetch the diff of a PR from GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3.diff",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_pr_files(owner: str, repo: str, pr_number: int, token: str | None = None) -> list[dict]:
    """Fetch file-level stats for a PR."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following GitHub PR diff and produce a structured review in Markdown.

## PR Information
- Title: {title}
- Author: {author}
- Description: {description}
- Files changed: {files_changed}

## Diff
```
{diff}
```

## Required Output Format

Respond in exactly this Markdown structure:

### Summary
(2–3 sentence summary of what this PR does and its overall quality)

### Risks
(Bulleted list of potential risks, bugs, security concerns, or regressions. If none, state "No significant risks identified.")

### Suggestions
(Bulleted list of concrete improvement suggestions — readability, performance, correctness, style. If none, state "No suggestions — looks good.")

### Confidence
- **Level**: Low / Medium / High
- **Reason**: (1 sentence explaining why this confidence level)

---

Be specific, actionable, and constructive. Reference file names and line numbers when possible.
If the diff is very large, focus on the most important changes.
If something looks correct, say so — don't invent issues.
"""


def review_pr(owner: str, repo: str, pr_number: int, model: str = "claude-sonnet-4-20250514") -> str:
    """Fetch a PR diff and return a structured Claude review."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Warning: No GITHUB_TOKEN set. Rate limits may apply.", file=sys.stderr)

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    metadata = fetch_pr_metadata(owner, repo, pr_number, token)
    diff = fetch_pr_diff(owner, repo, pr_number, token)
    files = fetch_pr_files(owner, repo, pr_number, token)

    if not diff.strip():
        return "No diff found for this PR."

    # Truncate very large diffs to fit context window
    max_chars = 100_000
    if len(diff) > max_chars:
        diff = diff[:max_chars] + f"\n\n... [truncated — diff was {len(diff)} chars total]"

    prompt = REVIEW_PROMPT.format(
        title=metadata.get("title", "Unknown"),
        author=metadata.get("user", {}).get("login", "Unknown"),
        description=metadata.get("body", "No description")[:500],
        files_changed=", ".join(f["filename"] for f in files[:20]),
        diff=diff,
    )

    print("Sending to Claude for review...", file=sys.stderr)
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    review = message.content[0].text
    return review


def main():
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="AI-powered PR reviewer using Claude",
    )
    parser.add_argument(
        "pr_url",
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write review to file instead of stdout",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON with metadata",
    )

    args = parser.parse_args()

    try:
        owner, repo, pr_number = parse_pr_url(args.pr_url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    review = review_pr(owner, repo, pr_number, model=args.model)

    if args.json_output:
        output = {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "review": review,
        }
        result = json.dumps(output, indent=2)
    else:
        result = f"# Review of PR #{pr_number}\n\n**Repository**: {owner}/{repo}\n**PR**: [#{pr_number}](https://github.com/{owner}/{repo}/pull/{pr_number})\n\n---\n\n{review}"

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
