#!/usr/bin/env python3
import sys
import os
import re
import urllib.request
import json
import argparse

def get_pr_diff(pr_url, github_token=None):
    match = re.match(r'https://github.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError("Invalid Pull Request URL format.")
    
    owner, repo, pr_num = match.groups()
    diff_url = f"https://github.com/{owner}/{repo}/pull/{pr_num}.diff"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
        
    req = urllib.request.Request(diff_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
        req_api = urllib.request.Request(api_url, headers={
            'Accept': 'application/vnd.github.v3.diff',
            'User-Agent': 'Mozilla/5.0',
            **({'Authorization': f'token {github_token}'} if github_token else {})
        })
        with urllib.request.urlopen(req_api) as response:
            return response.read().decode('utf-8')

def call_claude_api(diff, api_key):
    url = "https://api.anthropic.com/v1/messages"
    
    system_prompt = (
        "You are an expert software engineer and code reviewer. Your task is to analyze the provided git diff of a Pull Request "
        "and return a structured Markdown review comment. You must follow this format strictly:\n\n"
        "### Summary of Changes\n"
        "Provide a concise summary of the changes introduced in the PR (2-3 sentences max).\n\n"
        "### Identified Risks\n"
        "List any potential bugs, security issues, performance bottlenecks, or architectural concerns introduced by the changes.\n\n"
        "### Improvement Suggestions\n"
        "List constructive suggestions to improve the code quality, readability, test coverage, or documentation.\n\n"
        "### Confidence Score\n"
        "Provide a confidence score for the changes: **Low** / **Medium** / **High** (with a brief 1-sentence justification)."
    )
    
    if len(diff) > 100000:
        diff = diff[:100000] + "\n\n[Diff truncated due to size limit...]"
        
    messages = [
        {"role": "user", "content": f"Please review the following PR diff:\n\n```diff\n{diff}\n```"}
    ]
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1500,
        "system": system_prompt,
        "messages": messages
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['content'][0]['text']
    except urllib.error.HTTPError as e:
        error_info = e.read().decode('utf-8')
        raise RuntimeError(f"Anthropic API Error: {error_info}")
    except Exception as e:
        raise RuntimeError(f"Failed to communicate with Anthropic API: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Zero-dependency Claude PR Reviewer")
    parser.add_argument('--pr', required=True, help="GitHub Pull Request URL")
    args = parser.parse_args()
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
        
    github_token = os.environ.get("GITHUB_TOKEN")
    
    try:
        print(f"[*] Fetching diff for PR: {args.pr}...", file=sys.stderr)
        diff = get_pr_diff(args.pr, github_token)
        if not diff.strip():
            print("Error: PR diff is empty.", file=sys.stderr)
            sys.exit(1)
            
        print("[*] Generating review via Claude API...", file=sys.stderr)
        review = call_claude_api(diff, api_key)
        
        print(review)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
