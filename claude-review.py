#!/usr/bin/env python3
import os
import sys
import argparse
import urllib.request
import json

def fetch_pr_diff(pr_url):
    diff_url = pr_url.rstrip("/") + ".diff"
    try:
        req = urllib.request.Request(diff_url, headers={'User-Agent': 'claude-reviewer'})
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching PR diff from {diff_url}: {e}", file=sys.stderr)
        sys.exit(1)

def analyze_with_claude(diff, api_key):
    url = "https://api.anthropic.com/v1/messages"
    
    prompt = f"""You are an expert code reviewer. Analyze the following Pull Request diff and provide a structured Markdown review.

Your response MUST exactly follow this structure:
### Summary
[2-3 sentences summarizing the changes]

### Identified Risks
- [Risk 1]
- [Risk 2]
(or "None identified" if none)

### Improvement Suggestions
- [Suggestion 1]
- [Suggestion 2]
(or "None at this time" if perfectly written)

### Confidence Score
[Low / Medium / High]

Here is the diff to review:
```diff
{diff}
```"""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"]
    except Exception as e:
        print(f"Error calling Anthropic API: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching diff for {args.pr}...", file=sys.stderr)
    diff = fetch_pr_diff(args.pr)
    
    if not diff.strip():
        print("PR diff is empty.", file=sys.stderr)
        sys.exit(1)

    print("Analyzing with Claude API...", file=sys.stderr)
    review_markdown = analyze_with_claude(diff, api_key)
    
    print("\n" + "="*50 + "\n")
    print(review_markdown)
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
