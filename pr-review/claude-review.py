#!/usr/bin/env python3
"""claude-review — Claude Code sub-agent that reviews a PR and posts a structured comment.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

Requires:
  - gh CLI (authenticated) for fetching PR data
  - ANTHROPIC_API_KEY environment variable for Claude API
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error


def parse_pr_url(url):
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        sys.exit(f"Error: invalid PR URL: {url}\nExpected: https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), m.group(3)


def run_gh(*args):
    result = subprocess.run(["gh"] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"gh command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout


def fetch_pr_diff(owner, repo, pr_number):
    return run_gh("pr", "diff", str(pr_number), "-R", f"{owner}/{repo}")


def fetch_pr_metadata(owner, repo, pr_number):
    raw = run_gh("pr", "view", str(pr_number), "-R", f"{owner}/{repo}",
                 "--json", "title,body,author,state,mergeable,additions,deletions,files,createdAt")
    return json.loads(raw)


def call_claude(prompt, system_prompt, api_key):
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        sys.exit(f"Claude API error ({e.code}): {body}")


SYSTEM_PROMPT = """You are a senior code reviewer. Given a PR diff and metadata, produce a structured review.

Output format:
## Review: {PR title}

### Summary
2-3 sentence overview of what this PR does and whether it accomplishes its goal.

### Identified Risks
- Risk description (severity: High/Medium/Low)

### Improvement Suggestions
- Suggestion description (priority: High/Medium/Low)

### Confidence Score
**Confidence: High/Medium/Low**

Explain why in one sentence.

Be constructive, specific, and actionable. Reference exact lines when possible."""
GITHUB_ACTION_SYSTEM_PROMPT = """You are a senior code reviewer integrated into a GitHub Action. Given a PR diff and metadata, produce a structured review comment.

Output format:
## Review Summary
2-3 sentence overview.

## Risks
- Risk description

## Suggestions
- Improvement suggestion

## Verdict
**Confidence: High/Medium/Low**"""


def format_review(title, diff, metadata, system_prompt):
    prompt = f"""PR Title: {title}
Author: {metadata.get('author', {}).get('login', 'unknown')}
State: {metadata.get('state', 'unknown')}
Files changed: {len(metadata.get('files', []))}
Additions: {metadata.get('additions', 0)}
Deletions: {metadata.get('deletions', 0)}

--- DIFF START ---
{diff[:15000]}
--- DIFF END ---

Please review this PR following the required format."""
    return call_claude(prompt, system_prompt, os.environ["ANTHROPIC_API_KEY"])


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR review agent")
    parser.add_argument("--pr", required=True, help="PR URL (https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--github-action", action="store_true", help="Use GitHub Action output format")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Error: ANTHROPIC_API_KEY environment variable is required")

    owner, repo, pr_number = parse_pr_url(args.pr)

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    diff = fetch_pr_diff(owner, repo, pr_number)
    metadata = fetch_pr_metadata(owner, repo, pr_number)
    title = metadata.get("title", f"PR #{pr_number}")

    print(f"Reviewing {metadata.get('additions', 0)} additions across {len(metadata.get('files', []))} files...", file=sys.stderr)
    system = GITHUB_ACTION_SYSTEM_PROMPT if args.github_action else SYSTEM_PROMPT
    review = format_review(title, diff, metadata, system)

    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(review)


if __name__ == "__main__":
    main()
