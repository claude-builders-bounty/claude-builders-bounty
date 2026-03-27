#!/usr/bin/env python3
"""Claude Review Agent - PR diff analysis using GLM API via Claude Code Anthropic endpoint."""

import argparse, json, subprocess, sys, os, requests
from datetime import datetime

# Config
API_URL = "https://open.bigmodel.cn/api/anthropic/v1/messages"
API_KEY = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
MODEL = os.environ.get("ANTHROPIC_MODEL", "glm-5-turbo")

def get_pr_diff(pr_url):
    """Extract owner/repo and PR number, fetch diff via gh CLI."""
    parts = pr_url.rstrip("/").split("/")
    repo = f"{parts[-4]}/{parts[-3]}"
    pr_num = parts[-1]
    diff = subprocess.check_output(
        ["gh", "pr", "diff", str(pr_num), "--repo", repo],
        stderr=subprocess.PIPE
    ).decode()
    title = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/pulls/{pr_num}", "--jq", ".title"],
        stderr=subprocess.PIPE
    ).decode().strip()
    body = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/pulls/{pr_num}", "--jq", ".body"],
        stderr=subprocess.PIPE
    ).decode().strip()
    files_raw = subprocess.check_output(
        ["gh", "api", f"repos/{repo}/pulls/{pr_num}/files", "--jq", '.[].filename'],
        stderr=subprocess.PIPE
    ).decode().strip()
    files = files_raw.split("\n") if files_raw else []
    return {"title": title, "body": body, "diff": diff, "files": files, "repo": repo, "pr": pr_num}

def analyze(pr_data):
    """Send PR data to GLM for analysis."""
    # Truncate diff if too long
    diff = pr_data["diff"]
    if len(diff) > 15000:
        diff = diff[:15000] + "\n... (truncated)"
    
    prompt = f"""Review this Pull Request and provide a structured review.

PR Title: {pr_data['title']}
PR Description: {pr_data['body'] or '(no description)'}
Files Changed: {', '.join(pr_data['files'][:20])}

Diff:
```diff
{diff}
```

Respond in EXACTLY this Markdown format (no extra text before or after):

## Summary
[2-3 sentences summarizing the changes]

## Risks
- [risk 1]
- [risk 2]

## Suggestions
- [suggestion 1]
- [suggestion 2]

## Confidence: [Low/Medium/High]
[one sentence explaining confidence level]"""

    resp = requests.post(API_URL, 
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": MODEL,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=120
    )
    if resp.status_code != 200:
        print(f"API Error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["content"][0]["text"]

def main():
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument("--pr", required=True, help="PR URL")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    print(f"Fetching PR diff from {args.pr}...", file=sys.stderr)
    pr_data = get_pr_diff(args.pr)
    print(f"Analyzing {len(pr_data['files'])} files ({len(pr_data['diff'])} chars diff)...", file=sys.stderr)
    
    review = analyze(pr_data)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(f"# PR Review: {args.pr}\n\n{review}\n")
        print(f"Review saved to {args.output}", file=sys.stderr)
    else:
        print(review)

if __name__ == "__main__":
    main()
