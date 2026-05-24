#!/usr/bin/env python3
import argparse
import urllib.request
import urllib.parse
import json
import sys
import os

def fetch_pr_diff(pr_url):
    """Fetches the unified diff of a GitHub PR directly via GitHub API without any external dependencies."""
    try:
        parts = urllib.parse.urlparse(pr_url).path.strip('/').split('/')
        if len(parts) >= 4 and parts[2] == 'pull':
            owner, repo, _, pr_num = parts[:4]
        else:
            raise ValueError("Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123")
    except Exception as e:
        print(f"Error parsing URL: {e}", file=sys.stderr)
        sys.exit(1)

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    
    req = urllib.request.Request(api_url, headers={
        'User-Agent': 'claude-reviewer-cli',
        'Accept': 'application/vnd.github.v3.diff'
    })
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        print(f"GitHub API Error: {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching diff from GitHub: {e}", file=sys.stderr)
        sys.exit(1)

def analyze_with_claude(diff_text):
    """Sends the diff to Anthropic API for Markdown-structured analysis."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please export it: export ANTHROPIC_API_KEY='your-key-here'", file=sys.stderr)
        sys.exit(1)

    url = "https://api.anthropic.com/v1/messages"
    
    system_prompt = """You are an expert Senior Code Reviewer and Security Analyst.
Your task is to review a GitHub PR diff and output a structured Markdown response.
You MUST STRICTLY follow this Markdown structure without any deviations or JSON formatting.

### Summary
[Write 2-3 sentences summarizing the changes]

### Risks
- [List any identified risks, security flaws, edge-case bugs, or anti-patterns]
- [If absolutely none, explicitly state "No major risks identified"]

### Suggestions
- [List concrete improvement suggestions]
- [Focus on best practices, code readability, and performance]

### Confidence
[Low / Medium / High]
"""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    # Truncate diff if it's insanely large to prevent token limits (approx ~80k tokens safety)
    if len(diff_text) > 300000:
        diff_text = diff_text[:300000] + "\n\n...[DIFF TRUNCATED DUE TO SIZE]..."

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": f"Review this PR diff:\n\n```diff\n{diff_text}\n```"}
        ]
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['content'][0]['text']
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        print(f"Anthropic API Error: {e.code}\n{err_msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error calling Anthropic API: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude PR Reviewer Agent - Zero Dependencies")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()

    print(f"Fetching diff for {args.pr}...", file=sys.stderr)
    diff = fetch_pr_diff(args.pr)
    
    if not diff.strip():
         print("Warning: The PR diff is empty. Nothing to review.", file=sys.stderr)
         sys.exit(0)

    print("Analyzing diff with Claude 3.5 Sonnet...", file=sys.stderr)
    review_markdown = analyze_with_claude(diff)
    
    print("\n" + review_markdown + "\n")

if __name__ == "__main__":
    main()
