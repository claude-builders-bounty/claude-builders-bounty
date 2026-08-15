#!/usr/bin/env python3
import sys
import os
import argparse
import urllib.request
import urllib.parse
import json
import re

# Ponytail mode active — minimal, zero-dep python implementation

def fetch_diff(pr_url):
    # Normalize URL: strip trailing slash
    pr_url = pr_url.rstrip('/')
    
    # Check if it is a valid GitHub PR URL
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
        
    owner, repo, pr_number = match.groups()
    diff_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
    
    req = urllib.request.Request(
        diff_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to fetch diff from {diff_url}: {e}")

def get_claude_review(diff_content, api_key):
    # Default to OpenAI-compatible endpoint (9router), fallback to Anthropic.
    base_url = os.environ.get("CLAUDE_REVIEW_API_URL", "https://api.anthropic.com/v1/messages")
    model = os.environ.get("CLAUDE_REVIEW_MODEL", "claude-3-5-sonnet-20241022")

    if "chat/completions" in base_url or "v1/chat" in base_url:
        # OpenAI-compatible endpoint
        system_prompt = (
            "You are an expert software engineer and security auditor. "
            "Analyze the provided Git diff and generate a structured review in Markdown. "
            "Your review MUST contain exactly these four sections:\n\n"
            "### Summary of Changes\n"
            "[Provide a concise 2-3 sentence summary of what the PR does]\n\n"
            "### Identified Risks\n"
            "[List potential bugs, security vulnerabilities, edge cases, performance issues, or architectural flaws. If none, state so]\n\n"
            "### Improvement Suggestions\n"
            "[List actionable suggestions for code quality, formatting, optimization, readability, or testing]\n\n"
            "### Confidence Score\n"
            "[State either Low, Medium, or High, followed by a brief reason]"
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Review this Git diff:\n\n```diff\n{diff_content}\n```"}
            ],
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    else:
        # Anthropic native API
        system_prompt = (
            "You are an expert software engineer and security auditor. "
            "Analyze the provided Git diff and generate a structured review in Markdown. "
            "Your review MUST contain exactly these four sections:\n\n"
            "### Summary of Changes\n"
            "[Provide a concise 2-3 sentence summary of what the PR does]\n\n"
            "### Identified Risks\n"
            "[List potential bugs, security vulnerabilities, edge cases, performance issues, or architectural flaws. If none, state so]\n\n"
            "### Improvement Suggestions\n"
            "[List actionable suggestions for code quality, formatting, optimization, readability, or testing]\n\n"
            "### Confidence Score\n"
            "[State either Low, Medium, or High, followed by a brief reason]"
        )
        payload = {
            "model": model,
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"Review this Git diff:\n\n```diff\n{diff_content}\n```"}
            ]
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(base_url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if "chat/completions" in base_url or "v1/chat" in base_url:
                return res_data['choices'][0]['message']['content']
            return res_data['content'][0]['text']
    except Exception as e:
        if hasattr(e, 'read'):
            err_msg = e.read().decode('utf-8')
            raise RuntimeError(f"Review API request failed: {err_msg}")
        raise RuntimeError(f"Review API request failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR using Claude.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    
    args = parser.parse_args()
    
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_REVIEW_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY (or CLAUDE_REVIEW_API_KEY) environment variable is not set.", file=sys.stderr)
        sys.exit(1)
        
    try:
        print(f"Fetching diff for PR: {args.pr}...", file=sys.stderr)
        diff_content = fetch_diff(args.pr)
        
        # Guard against empty/huge diffs
        if not diff_content.strip():
            print("Error: PR diff is empty.", file=sys.stderr)
            sys.exit(1)
            
        if len(diff_content) > 100000:
            print("Warning: Diff is large. Truncating to first 100KB for processing.", file=sys.stderr)
            diff_content = diff_content[:100000]
            
        print("Analyzing diff with Claude...", file=sys.stderr)
        review = get_claude_review(diff_content, api_key)
        
        print("\n=== CLAUDE REVIEW ===")
        print(review)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
