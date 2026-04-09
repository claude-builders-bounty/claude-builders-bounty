import argparse
import os
import re
import requests
from anthropic import Anthropic

def fetch_pr_diff(pr_url: str) -> str:
    """
    Fetches the diff of a GitHub Pull Request from its URL.
    Example URL: https://github.com/owner/repo/pull/123
    """
    match = re.match(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")

    owner, repo, pr_number = match.groups()
    diff_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"

    headers = {}
    # GITHUB_TOKEN is optional but recommended for higher rate limits or private repos
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        headers["Accept"] = "application/vnd.github.v3.diff"

    print(f"Fetching diff from: {diff_url}")
    response = requests.get(diff_url, headers=headers)
    response.raise_for_status() # Raise an exception for HTTP errors
    return response.text

def review_diff_with_claude(diff: str) -> str:
    """
    Sends the PR diff to Claude for review and returns the structured Markdown comment.
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    if not client.api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

    system_prompt = """
You are a highly experienced Senior Software Engineer specializing in code review.
Your task is to review a given pull request diff and provide constructive feedback
in a structured Markdown format. Adhere strictly to the specified format.

Focus on:
- Overall purpose and impact of changes.
- Potential bugs, performance issues, security vulnerabilities.
- Code readability, maintainability, adherence to best practices.
- Missing tests, documentation, or error handling.

Output Format:
## PR Review by Claude
### Summary of Changes
[2-3 sentences describing the overall purpose and impact of the changes.]

### Identified Risks
*   [Risk 1: Description]
*   [Risk 2: Description]
...
(If no risks are found, state "No significant risks identified.")

### Improvement Suggestions
*   [Suggestion 1: Description]
*   [Suggestion 2: Description]
...
(If no suggestions are found, state "No specific improvement suggestions.")

### Confidence Score
[Low / Medium / High]
(Assess based on complexity of changes, clarity, and potential impact. High for well-understood, low-risk changes; Low for complex, risky, or unclear changes.)
"""

    user_message = f"""
Here is the pull request diff for your review:

