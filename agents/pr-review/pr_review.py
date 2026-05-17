#!/usr/bin/env python3
"""
Claude Code PR Review Agent
Usage: claude-review --pr https://github.com/owner/repo/pull/123
Or: python pr_review.py --pr <pr_url>
"""

import argparse
import json
import urllib.request
import urllib.error
import sys
import os

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
MODEL = 'claude-sonnet-4-20250514'

def fetch_pr_diff(pr_url):
    """Fetch PR diff using GitHub API"""
    # Parse PR URL
    parts = pr_url.rstrip('/').split('/')
    owner = parts[3]
    repo = parts[4]
    pr_number = parts[6]
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {
        'Accept': 'application/vnd.github.v3.diff',
        'User-Agent': 'Claude-Code-PR-Review/1.0'
    }
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        files = json.loads(resp.read().decode('utf-8'))
    
    # Also fetch the full diff
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req2 = urllib.request.Request(diff_url, headers=headers)
    with urllib.request.urlopen(req2, timeout=60) as resp:
        pr_data = json.loads(resp.read().decode('utf-8'))
    
    return {
        'title': pr_data['title'],
        'body': pr_data['body'],
        'files': files,
        'diff_url': pr_data.get('diff_url', '')
    }

def get_diff_content(diff_url):
    """Fetch raw diff content"""
    headers = {'User-Agent': 'Claude-Code-PR-Review/1.0'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    req = urllib.request.Request(diff_url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode('utf-8')

def analyze_with_claude(pr_data, diff_content):
    """Send PR data to Claude API for review"""
    if not CLAUDE_API_KEY:
        print("[ERROR] CLAUDE_API_KEY environment variable not set!")
        sys.exit(1)
    
    # Prepare prompt
    prompt = f"""You are a senior software engineer reviewing a PR.

PR Title: {pr_data['title']}

PR Description:
{pr_data['body'][:500]}

Changed Files:
{json.dumps([{'filename': f['filename'], 'status': f['status'], 'additions': f['additions'], 'deletions': f['deletions']} for f in pr_data['files']], indent=2)}

Diff (first 3000 chars):
{diff_content[:3000]}

Please provide a structured review with:
1. Summary of changes (2-3 sentences)
2. Identified risks (list, be specific)
3. Improvement suggestions (list, actionable)
4. Confidence score: Low / Medium / High (based on how confident you are in this review)

Format as Markdown. Be concise and actionable."""

    # Call Claude API
    api_url = "https://api.anthropic.com/v1/messages"
    headers = {
        'x-api-key': CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    return result['content'][0]['text']

def post_review_comment(pr_url, review_text):
    """Post the review as a PR comment (optional)"""
    parts = pr_url.rstrip('/').split('/')
    owner = parts[3]
    repo = parts[4]
    pr_number = parts[6]
    
    if not GITHUB_TOKEN:
        print("[WARN] GITHUB_TOKEN not set, skipping comment post.")
        return
    
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "body": f"## 🤖 Automated PR Review (by Claude Code Agent)\n\n{review_text}"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            print(f"[OK] Review posted as comment to PR #{pr_number}")
    except urllib.error.HTTPError as e:
        print(f"[WARN] Could not post comment: {e}")

def main():
    parser = argparse.ArgumentParser(description='Claude Code PR Review Agent')
    parser.add_argument('--pr', required=True, help='PR URL (e.g., https://github.com/owner/repo/pull/123)')
    parser.add_argument('--post-comment', action='store_true', help='Post review as PR comment')
    args = parser.parse_args()
    
    print(f"[PR Review Agent] Reviewing: {args.pr}\n")
    
    # Step 1: Fetch PR data
    print("[1/3] Fetching PR data...")
    pr_data = fetch_pr_diff(args.pr)
    print(f"  Title: {pr_data['title']}")
    print(f"  Files changed: {len(pr_data['files'])}")
    
    # Step 2: Get diff content
    print("\n[2/3] Fetching diff content...")
    diff_content = get_diff_content(pr_data['diff_url'])
    print(f"  Diff size: {len(diff_content)} chars")
    
    # Step 3: Analyze with Claude
    print("\n[3/3] Analyzing with Claude API...")
    review = analyze_with_claude(pr_data, diff_content)
    
    # Output review
    print("\n" + "=" * 70)
    print("REVIEW OUTPUT")
    print("=" * 70)
    print(review)
    print("=" * 70)
    
    # Optionally post as comment
    if args.post_comment:
        post_review_comment(args.pr, review)
    
    # Save to file
    with open('review_output.md', 'w', encoding='utf-8') as f:
        f.write(f"# PR Review: {pr_data['title']}\n\n")
        f.write(f"PR URL: {args.pr}\n\n")
        f.write(review)
    print("\n[OK] Review saved to: review_output.md")

if __name__ == '__main__':
    main()
