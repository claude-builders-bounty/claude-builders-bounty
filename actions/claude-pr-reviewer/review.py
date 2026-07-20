#!/usr/bin/env python3
import os
import json
import requests
from anthropic import Anthropic

def get_pr_diff(repo, pr_number, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    url = f'https://api.github.com/repos/{repo}/pulls/{pr_number}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def post_comment(repo, pr_number, token, comment):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{repo}/issues/{pr_number}/comments'
    response = requests.post(url, headers=headers, json={'body': comment})
    response.raise_for_status()

def analyze_diff(diff_text, api_key, model):
    client = Anthropic(api_key=api_key)
    
    prompt = f"""You are an expert software engineer and code reviewer. Please analyze the following pull request diff and provide a structured Markdown review comment.

Your output MUST be formatted exactly like this:

### 📝 Summary of Changes
(Provide a 2-3 sentence summary of what this PR does)

### ⚠️ Identified Risks
- (List any security, performance, or logic risks)
- (If none, state "No major risks identified")

### 💡 Improvement Suggestions
- (List any refactoring, clean code, or optimization suggestions)
- (If none, state "Code looks solid, no suggestions")

### 🎯 Confidence Score
(Low / Medium / High) - Briefly explain why

Here is the diff:
```diff
{diff_text}
```
"""

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

def main():
    token = os.environ.get('GITHUB_TOKEN')
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    model = os.environ.get('CLAUDE_MODEL', 'claude-3-7-sonnet-20250219')
    repo = os.environ.get('GITHUB_REPOSITORY')
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    
    if not all([token, api_key, repo, event_path]):
        print("Missing required environment variables.")
        return

    with open(event_path, 'r') as f:
        event = json.load(f)
        
    if 'pull_request' not in event:
        print("Not a pull request event.")
        return
        
    pr_number = event['pull_request']['number']
    
    print(f"Fetching diff for PR #{pr_number}...")
    diff_text = get_pr_diff(repo, pr_number, token)
    
    if not diff_text or len(diff_text.strip()) == 0:
        print("Empty diff, skipping review.")
        return
        
    # Truncate diff if it's too large for the context window (~100k chars is safe)
    if len(diff_text) > 100000:
        diff_text = diff_text[:100000] + "\n\n... (diff truncated for size)"
    
    print("Analyzing diff with Claude...")
    review = analyze_diff(diff_text, api_key, model)
    
    # Append branding/footer
    review += "\n\n---\n*🤖 Reviewed by [Claude PR Reviewer Agent](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/actions/claude-pr-reviewer)*"
    
    print("Posting comment to GitHub...")
    post_comment(repo, pr_number, token, review)
    print("Done!")

if __name__ == "__main__":
    main()
