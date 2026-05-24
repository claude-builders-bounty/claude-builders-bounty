#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import json
import urllib.request
import urllib.error

def get_pr_diff(pr_url):
    try:
        # We use the GitHub CLI to fetch the diff
        result = subprocess.run(["gh", "pr", "view", pr_url, "--diff"], 
                                capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR diff from {pr_url}.")
        print(f"Make sure you have 'gh' CLI installed and are logged in.")
        print(f"stderr: {e.stderr}")
        sys.exit(1)

def call_claude(diff_text):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    system_prompt = """You are an expert software engineer performing a code review.
Please review the provided git diff and output a structured Markdown review.

Your output MUST strictly follow this Markdown structure:

### Summary of Changes
[Provide a 2-3 sentence summary of the changes.]

### Identified Risks
- [List any bugs, security vulnerabilities, or performance risks. If none, state "None identified."]
- ...

### Improvement Suggestions
- [List suggestions for cleaner code, better patterns, etc. If none, state "Looks good as is."]
- ...

### Confidence Score
[Output ONLY: Low, Medium, or High]
"""

    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": f"Here is the PR diff:\n\n```diff\n{diff_text}\n```\n\nPlease review it."}
        ]
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        print(f"Anthropic API Error: {e.code} {e.reason}")
        print(error_msg)
        sys.exit(1)
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="URL of the GitHub Pull Request to review")
    args = parser.parse_args()

    print(f"Fetching diff for PR: {args.pr} ...", file=sys.stderr)
    diff_text = get_pr_diff(args.pr)
    
    if not diff_text.strip():
        print("The PR diff is empty. Nothing to review.")
        sys.exit(0)
        
    print(f"Analyzing diff ({len(diff_text)} characters) with Claude...", file=sys.stderr)
    review_markdown = call_claude(diff_text)
    
    print("\n" + review_markdown)

if __name__ == "__main__":
    main()
