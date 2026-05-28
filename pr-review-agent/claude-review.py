#!/usr/bin/env python3
"""
claude-review — PR review sub-agent for Claude Code

Analyzes a GitHub PR diff using Claude API and returns a structured review.
Works via CLI or as a GitHub Action.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr 123 --repo owner/repo
    claude-review --pr 123 --repo owner/repo --github-token ghp_xxx

Environment Variables:
    ANTHROPIC_API_KEY    Required. Your Anthropic API key.
    GITHUB_TOKEN         Optional. GitHub token (defaults to GH_TOKEN or gh CLI).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, and PR number."""
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def get_github_token() -> str:
    """Get GitHub token from env or gh CLI."""
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        return token
    try:
        result = subprocess.run(
            ['gh', 'auth', 'token'], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    raise ValueError(
        "GitHub token not found. Set GITHUB_TOKEN env var or install gh CLI."
    )


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Fetch the diff of a GitHub PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3.diff',
        'User-Agent': 'claude-review-agent/1.0',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f"GitHub API error {e.code}: {body}")


def fetch_pr_metadata(owner: str, repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR metadata (title, description, changed files)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'claude-review-agent/1.0',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f"GitHub API error {e.code}: {body}")


def get_anthropic_api_key() -> str:
    """Get Anthropic API key from environment."""
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Get one at https://console.anthropic.com"
        )
    return key


def call_claude_api(prompt: str, api_key: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Call Claude API with a prompt and return the response."""
    data = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'User-Agent': 'claude-review-agent/1.0',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['content'][0]['text']
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f"Anthropic API error {e.code}: {body}")


def build_review_prompt(title: str, description: str, diff: str, changed_files: list) -> str:
    """Build the prompt for Claude to review the PR."""
    files_summary = "\n".join(f"- {f['filename']} ({f['status']}, +{f.get('additions', '?')}/-{f.get('deletions', '?')})" for f in changed_files[:20])

    return f"""You are a senior code reviewer. Analyze the following PR and provide a structured review.

## PR Title
{title}

## Description
{description or '(No description provided)'}

## Changed Files
{files_summary}

## Diff
```diff
{diff[:80000]}
```

## Review Format

Return your review in this exact Markdown structure:

### Summary
2-3 sentences describing what this PR does.

### Identified Risks
- Risk 1
- Risk 2

### Improvement Suggestions
- Suggestion 1
- Suggestion 2

### Confidence Score
**High / Medium / Low**

### Detailed Notes (if any)
"""


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR using Claude")
    parser.add_argument('--pr', required=True, help='PR URL or number (use with --repo)')
    parser.add_argument('--repo', help='owner/repo (required if --pr is a number)')
    parser.add_argument('--github-token', help='GitHub token')
    parser.add_argument('--model', default='claude-sonnet-4-20250514', help='Claude model')
    parser.add_argument('--output', help='Save output to file')
    args = parser.parse_args()

    # Parse PR identifier
    if args.pr.startswith('https://'):
        owner, repo, pr_number = parse_pr_url(args.pr)
    else:
        if not args.repo:
            parser.error("--repo is required when --pr is a number")
        owner, repo_name = args.repo.split('/')
        pr_number = int(args.pr)
        repo = repo_name

    # Get tokens
    github_token = args.github_token or get_github_token()
    anthropic_key = get_anthropic_api_key()

    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    # Fetch data
    meta = fetch_pr_metadata(owner, repo, pr_number, github_token)
    diff = fetch_pr_diff(owner, repo, pr_number, github_token)
    changed_files = meta.get('files', [])

    title = meta.get('title', '')
    description = meta.get('body', '')

    print(f"📝 Reviewing: {title}", file=sys.stderr)
    print(f"📄 Files changed: {len(changed_files)}", file=sys.stderr)
    print(f"📏 Diff size: {len(diff)} chars", file=sys.stderr)

    # Build prompt and call Claude
    prompt = build_review_prompt(title, description, diff, changed_files)
    print(f"🤖 Calling Claude API ({args.model})...", file=sys.stderr)

    review = call_claude_api(prompt, anthropic_key, args.model)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(review)
        print(f"✅ Review saved to {args.output}", file=sys.stderr)
    else:
        print(review)


if __name__ == '__main__':
    main()
