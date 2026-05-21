import argparse
import os
import sys
import re
import requests
from anthropic import Anthropic

def get_pr_diff(pr_url, gh_token=None):
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError("Invalid GitHub PR URL. Must be like https://github.com/owner/repo/pull/123")
    owner, repo, pr_number = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"
        
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    return response.text

def main():
    parser = argparse.ArgumentParser(description="Claude PR Reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    args = parser.parse_args()

    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is missing.", file=sys.stderr)
        sys.exit(1)

    gh_token = os.environ.get("GITHUB_TOKEN")

    try:
        diff = get_pr_diff(args.pr, gh_token)
    except Exception as e:
        print(f"Failed to fetch PR diff: {e}", file=sys.stderr)
        sys.exit(1)

    if not diff.strip():
        print("The PR diff is empty.", file=sys.stderr)
        sys.exit(1)

    client = Anthropic(api_key=anthropic_api_key)

    system_prompt = (
        "You are an expert code reviewer. "
        "Analyze the provided pull request diff and generate a structured Markdown review comment. "
        "Your output MUST contain EXACTLY the following sections and nothing else:\n\n"
        "### Summary of Changes\n"
        "(2-3 sentences summarizing the PR)\n\n"
        "### Identified Risks\n"
        "- (List any potential bugs, security issues, or regressions)\n\n"
        "### Improvement Suggestions\n"
        "- (List actionable code quality or architecture improvements)\n\n"
        "### Confidence Score\n"
        "(Must be exactly one of: Low, Medium, High based on your confidence in the review)"
    )

    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2048,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Here is the diff to review:\n\n```diff\n{diff}\n```"}
            ]
        )
        print(message.content[0].text)
    except Exception as e:
        print(f"Failed to generate review: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
