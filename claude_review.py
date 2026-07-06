#!/usr/bin/env python3
"""
Claude Code sub-agent to review a GitHub PR and post structured comment.
Usage: python claude_review.py --pr https://github.com/owner/repo/pull/123
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

# Claude API endpoint
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

def fetch_pr_diff(pr_url):
    """Fetch the diff of a GitHub PR."""
    # Convert URL to API endpoint for diff
    match = re.match(r'https://github.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError("Invalid PR URL format")
    owner, repo, pr_number = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-pr-reviewer"
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR diff: {e}", file=sys.stderr)
        sys.exit(1)

def analyze_diff_with_claude(diff_text):
    """Send diff to Claude API and get structured review."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    prompt = f"""You are a code reviewer. Analyze the following GitHub PR diff and provide a structured review. Output only valid JSON with these fields:
- summary: a 2-3 sentence summary of the changes
- risks: a list of identified risks
- improvements: a list of improvement suggestions
- confidence: "Low", "Medium", or "High" (how confident you are in your review)

Diff:
```
{diff_text}
```

Respond only with the JSON object, no other text."""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    req = urllib.request.Request(CLAUDE_API_URL, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result['content'][0]['text']
            return json.loads(content)
    except urllib.error.HTTPError as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)

def format_review_markdown(review):
    """Format structured review as Markdown."""
    md = "## PR Review\n\n"
    md += f"### Summary\n{review['summary']}\n\n"
    md += "### Identified Risks\n"
    for risk in review['risks']:
        md += f"- {risk}\n"
    md += "\n### Improvement Suggestions\n"
    for imp in review['improvements']:
        md += f"- {imp}\n"
    md += f"\n### Confidence Score: {review['confidence']}\n"
    return md

def main():
    parser = argparse.ArgumentParser(description="Review a PR using Claude")
    parser.add_argument('--pr', required=True, help='Full URL of the PR')
    args = parser.parse_args()
    
    print("Fetching PR diff...", file=sys.stderr)
    diff = fetch_pr_diff(args.pr)
    
    print("Analyzing with Claude...", file=sys.stderr)
    review = analyze_diff_with_claude(diff)
    
    markdown = format_review_markdown(review)
    print(markdown)

if __name__ == "__main__":
    main()
