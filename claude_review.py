#!/usr/bin/env python3
"""
Claude Review Agent - PR Reviewer for GitHub
Analyzes PR diffs and posts structured Markdown review comments.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr 123 --repo owner/repo
"""

import asyncio
import aiohttp
import os
import re
import sys
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
NIM_API_KEY = os.getenv('NVIDIA_NIM_API_KEY')
NIM_BASE_URL = os.getenv('NVIDIA_NIM_BASE_URL', 'https://integrate.api.nvidia.com/v1')
NIM_MODEL = os.getenv('NVIDIA_NIM_DEFAULT_MODEL', 'nvidia/nemotron-3-ultra-550b-a55b')

HEADERS_GH = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

HEADERS_NIM = {
    'Authorization': f'Bearer {NIM_API_KEY}',
    'Content-Type': 'application/json'
}

class PRReviewer:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def parse_pr_url(self, pr_input):
        """Parse PR input - can be URL or number with repo."""
        # URL format: https://github.com/owner/repo/pull/123
        url_match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_input)
        if url_match:
            return url_match.group(1), url_match.group(2), int(url_match.group(3))
        
        # Number format: 123 (requires --repo)
        return None, None, None
    
    async def fetch_pr_diff(self, owner, repo, pr_number):
        """Fetch PR diff from GitHub."""
        url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
        
        async with self.session.get(url, headers=HEADERS_GH) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to fetch PR: {resp.status} - {await resp.text()}")
            pr_data = await resp.json()
        
        # Get diff
        diff_url = pr_data['diff_url']
        async with self.session.get(diff_url, headers={'Accept': 'application/vnd.github.v3.diff'}) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to fetch diff: {resp.status}")
            diff = await resp.text()
        
        return {
            'title': pr_data['title'],
            'body': pr_data.get('body', ''),
            'diff': diff,
            'files': pr_data.get('changed_files', 0),
            'additions': pr_data.get('additions', 0),
            'deletions': pr_data.get('deletions', 0),
            'html_url': pr_data['html_url'],
            'user': pr_data['user']['login'],
            'base_branch': pr_data['base']['ref'],
            'head_branch': pr_data['head']['ref']
        }
    
    async def analyze_with_nim(self, diff, title, body):
        """Analyze PR diff using NVIDIA NIM (Nemotron)."""
        
        # Truncate diff if too large (keep first 15000 chars)
        max_diff = 15000
        if len(diff) > max_diff:
            diff = diff[:max_diff] + f"\n\n... [DIFF TRUNCATED - {len(diff)} total chars]"
        
        system_prompt = """You are an expert code reviewer. Analyze the PR diff and provide a structured review.

Output ONLY valid Markdown with these exact sections:

## Summary
2-3 sentences summarizing what this PR does.

## Risks
- Risk 1 (specific, actionable)
- Risk 2 (specific, actionable)
- Risk 3 (specific, actionable)
If no significant risks, write: "No significant risks identified."

## Suggestions
- Suggestion 1 (specific, actionable)
- Suggestion 2 (specific, actionable)
- Suggestion 3 (specific, actionable)
If no suggestions, write: "No suggestions at this time."

## Confidence Score
[Low / Medium / High] - Brief justification (1 sentence)"""

        user_prompt = f"""PR Title: {title}

PR Description:
{body or "(no description)"}

Diff:
```diff
{diff}
```"""

        payload = {
            'model': NIM_MODEL,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 2048,
            'stream': False
        }
        
        async with self.session.post(
            f'{NIM_BASE_URL}/chat/completions',
            json=payload,
            headers=HEADERS_NIM
        ) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"NIM API error: {resp.status} - {error}")
            data = await resp.json()
        
        # Handle NIM response format
        content = ""
        if 'choices' in data and data['choices']:
            message = data['choices'][0].get('message', {})
            content = message.get('content', '')
            if not content:
                content = message.get('reasoning_content', '')
        
        return content
    
    def format_review(self, analysis, pr_info):
        """Format the final review comment."""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        
        header = f"## 🤖 Automated Code Review\n\n*Reviewed by [Claude Review Agent](https://github.com/claude-builders-bounty/claude-builders-bounty) on {timestamp}*\n\n"
        header += f"**PR:** [{pr_info['title']}]({pr_info['html_url']}) | **Author:** @{pr_info['user']} | **Files:** {pr_info['files']} | **+{pr_info['additions']}/-{pr_info['deletions']}**\n\n"
        header += f"**Base:** `{pr_info['base_branch']}` ← **Head:** `{pr_info['head_branch']}`\n\n---\n\n"
        
        return header + analysis + "\n\n---\n*This review was generated automatically. Please verify findings manually.*"
    
    async def post_review_comment(self, owner, repo, pr_number, review_body):
        """Post review as a comment on the PR."""
        url = f'https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments'
        payload = {'body': review_body}
        
        async with self.session.post(url, json=payload, headers=HEADERS_GH) as resp:
            if resp.status not in (200, 201):
                raise Exception(f"Failed to post comment: {resp.status} - {await resp.text()}")
            return await resp.json()
    
    async def create_github_action(self):
        """Generate GitHub Action workflow YAML."""
        return '''name: 🤖 Automated PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout PR
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install aiohttp python-dotenv

      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NVIDIA_NIM_API_KEY: ${{ secrets.NVIDIA_NIM_API_KEY }}
          NVIDIA_NIM_BASE_URL: ${{ vars.NVIDIA_NIM_BASE_URL }}
          NVIDIA_NIM_DEFAULT_MODEL: ${{ vars.NVIDIA_NIM_DEFAULT_MODEL }}
        run: |
          python -m pip install --upgrade pip
          pip install aiohttp python-dotenv
          python claude_review.py --pr ${{ github.event.pull_request.number }} --repo ${{ github.repository }} --post-comment

      - name: Post Review Comment
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            // Comment posting handled by the script above
            pass

'''

async def main():
    parser = argparse.ArgumentParser(description='Claude Review Agent - PR Reviewer')
    parser.add_argument('--pr', required=True, help='PR URL or number')
    parser.add_argument('--repo', help='Repository (owner/repo) - required if PR is a number')
    parser.add_argument('--post-comment', action='store_true', help='Post review as comment on PR')
    parser.add_argument('--github-action', action='store_true', help='Output GitHub Action workflow YAML')
    parser.add_argument('--output', help='Output file for review (default: stdout)')
    
    args = parser.parse_args()
    
    # Parse PR
    owner, repo, pr_number = None, None, None
    
    if args.pr.startswith('http'):
        owner, repo, pr_number = PRReviewer().parse_pr_url(args.pr)
        if not owner:
            print("Error: Invalid PR URL format")
            sys.exit(1)
    else:
        if not args.repo:
            print("Error: --repo required when PR is a number")
            sys.exit(1)
        owner, repo = args.repo.split('/')
        pr_number = int(args.pr)
    
    if args.github_action:
        async with PRReviewer() as reviewer:
            workflow = await reviewer.create_github_action()
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(workflow)
            else:
                print(workflow)
        return
    
    print(f"🔍 Analyzing PR #{pr_number} from {owner}/{repo}...")
    
    async with PRReviewer() as reviewer:
        # Fetch PR data
        pr_info = await reviewer.fetch_pr_diff(owner, repo, pr_number)
        print(f"   Title: {pr_info['title']}")
        print(f"   Files: {pr_info['files']} | +{pr_info['additions']}/-{pr_info['deletions']}")
        
        # Analyze with NIM
        print("🧠 Analyzing with Nemotron 3 Ultra 550B...")
        analysis = await reviewer.analyze_with_nim(
            pr_info['diff'], 
            pr_info['title'], 
            pr_info['body']
        )
        
        # Format review
        review = reviewer.format_review(analysis, pr_info)
        
        # Output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(review)
            print(f"✅ Review saved to {args.output}")
        else:
            print("\n" + "="*60)
            print(review)
            print("="*60)
        
        # Post comment if requested
        if args.post_comment:
            print("\n📝 Posting review comment...")
            result = await reviewer.post_review_comment(owner, repo, pr_number, review)
            print(f"✅ Comment posted: {result['html_url']}")

if __name__ == '__main__':
    asyncio.run(main())