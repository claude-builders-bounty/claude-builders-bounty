#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
import anthropic

def fetch_pr_data(pr_url, github_token=None):
    """Fetches the PR details and the diff from GitHub."""
    # Parse URL: https://github.com/{owner}/{repo}/pull/{number}
    parts = pr_url.rstrip("/").split("/")
    if len(parts) < 4 or parts[-2] != "pull":
        print("Error: Invalid GitHub PR URL format.", file=sys.stderr)
        sys.exit(1)
        
    owner = parts[-4]
    repo = parts[-3]
    pr_number = parts[-1]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        
    # Fetch PR Metadata
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching PR data: {response.status_code} - {response.text}", file=sys.stderr)
        sys.exit(1)
        
    pr_data = response.json()
    
    # Fetch PR Diff
    diff_headers = headers.copy()
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    diff_response = requests.get(api_url, headers=diff_headers)
    
    if diff_response.status_code != 200:
        print(f"Error fetching PR diff: {diff_response.status_code}", file=sys.stderr)
        sys.exit(1)
        
    diff_text = diff_response.text
    
    return pr_data, diff_text

def generate_review(pr_data, diff_text, anthropic_key):
    """Uses Claude to generate a structured PR review."""
    client = anthropic.Anthropic(api_key=anthropic_key)
    
    system_prompt = """You are an elite, senior staff software engineer performing a code review on a Pull Request.
You will be provided with the PR metadata and the raw diff.
Your task is to analyze the changes and output a highly structured, rigorous Markdown review.

The output MUST contain exactly these sections in this order:
## 📊 PR Overview
- **Author:** [username]
- **Files Changed:** [number]
- **Additions:** [number] / **Deletions:** [number]

## 📝 Summary of Changes
Provide a brief narrative (2-3 sentences) explaining what this PR accomplishes.

## ⚠️ Identified Risks
List potential bugs, security flaws, performance bottlenecks, or logic errors. 
For each, assign a severity rating:
- 🔴 **High:** Security vulnerabilities, infinite loops, data corruption.
- 🟡 **Medium:** Performance issues, unhandled edge cases.
- 🟢 **Low:** Minor logic issues.
(If none, state "No significant risks identified.")

## 💡 Improvement Suggestions
Actionable recommendations to improve code quality, readability, or maintainability.

## 🛡️ Best Practices Check
Assess adherence to standard clean code practices (e.g., DRY, SOLID, no magic numbers, no hardcoded secrets). 

## 🎯 Confidence Score
[0-100%] based on how well you understand the language and framework used.
"""

    prompt = f"""Please review the following Pull Request.

Title: {pr_data.get('title')}
Body: {pr_data.get('body')}

Diff:
```diff
{diff_text}
```
"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error calling Anthropic API: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude-powered PR Review Agent")
    parser.add_argument("--pr", required=True, help="The full URL of the GitHub Pull Request")
    parser.add_argument("--output", help="Optional file path to save the Markdown review")
    args = parser.parse_args()

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")

    if not anthropic_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching PR data for {args.pr}...", file=sys.stderr)
    pr_data, diff_text = fetch_pr_data(args.pr, github_token)
    
    if len(diff_text.strip()) == 0:
        print("Error: The PR diff is empty. Nothing to review.", file=sys.stderr)
        sys.exit(1)
        
    # Simple truncation for massive PRs to avoid token limits (Claude 3.5 Sonnet supports 200k, so 500k chars is well within limit)
    if len(diff_text) > 500000:
        print("Warning: PR diff is extremely large. Truncating for review.", file=sys.stderr)
        diff_text = diff_text[:500000] + "\n\n...[DIFF TRUNCATED]..."

    print("Analyzing changes with Claude...", file=sys.stderr)
    review_markdown = generate_review(pr_data, diff_text, anthropic_key)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_markdown)
        print(f"Review saved to {args.output}", file=sys.stderr)
    else:
        print("\n" + "="*50 + "\n")
        print(review_markdown)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
