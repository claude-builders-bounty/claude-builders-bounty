#!/usr/bin/env python3
"""
Claude Code Sub-Agent: PR Reviewer
Reviews a GitHub PR and posts a structured comment.
"""

import os
import json
import subprocess
import anthropic
from pathlib import Path

REPO_DIR = os.environ.get("REPO_DIR", ".")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch PR diff using gh CLI."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}",
         "-H", "Accept: application/vnd.github.v3.diff"],
        capture_output=True, text=True
    )
    return result.stdout

def get_pr_files(owner: str, repo: str, pr_number: int) -> list:
    """Get list of changed files."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}/files",
         "--jq", ".[].filename"],
        capture_output=True, text=True
    )
    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

def get_pr_metadata(owner: str, repo: str, pr_number: int) -> dict:
    """Get PR title, description, and changed files."""
    result = subprocess.run(
        ["gh", "pr", "view", str(pr_number),
         "--repo", f"{owner}/{repo}",
         "--json", "title,body,additions,deletions,changedFiles"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def review_pr(owner: str, repo: str, pr_number: int) -> str:
    """Review a PR using Claude."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Gather context
    metadata = get_pr_metadata(owner, repo, pr_number)
    diff = get_pr_diff(owner, repo, pr_number)
    files = get_pr_files(owner, repo, pr_number)
    
    # Truncate diff if too large
    if len(diff) > 50000:
        diff = diff[:50000] + "\n... (diff truncated)"
    
    prompt = f"""Review this pull request and provide a structured analysis.

## PR Info
- Title: {metadata['title']}
- Description: {metadata.get('body', 'N/A')}
- Files changed: {metadata['changedFiles']}
- Additions: {metadata['additions']}
- Deletions: {metadata['deletions']}

## Changed Files
{chr(10).join(f'- {f}' for f in files)}

## Diff
```diff
{diff}
```

## Required Output Format

Provide your review in this exact format:

### Summary
[One paragraph overview of the PR]

### Code Quality
[Rate: ⭐⭐⭐⭐⭐ or specific feedback]

### Issues Found
[List any bugs, security issues, or concerns. Use "None found" if clean]

### Suggestions
[Improvements that could be made]

### Verdict
[APPROVE / REQUEST_CHANGES / COMMENT]

### Confidence
[High / Medium / Low]

Be concise. Focus on the most impactful feedback."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

def post_review(owner: str, repo: str, pr_number: int, review: str):
    """Post review as a PR comment."""
    comment = f"""## 🤖 Automated PR Review

{review}

---
*Reviewed by Claude Code Sub-Agent*"""
    
    subprocess.run(
        ["gh", "pr", "review", str(pr_number),
         "--repo", f"{owner}/{repo}",
         "--body", comment,
         "--comment"],
        capture_output=True, text=True
    )

def main():
    import sys
    if len(sys.argv) < 4:
        print("Usage: python agent.py <owner> <repo> <pr_number>")
        sys.exit(1)
    
    owner, repo, pr_number = sys.argv[1], sys.argv[2], int(sys.argv[3])
    
    print(f"Reviewing {owner}/{repo}#{pr_number}...")
    review = review_pr(owner, repo, pr_number)
    print(review)
    
    post_review(owner, repo, pr_number, review)
    print(f"✅ Review posted to {owner}/{repo}#{pr_number}")

if __name__ == "__main__":
    main()
