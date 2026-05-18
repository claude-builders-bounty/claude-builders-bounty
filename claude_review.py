#!/usr/bin/env python3
import sys
import os
import re
import json
import urllib.request
import argparse

HIGH_RISK_FILES = [
    r"auth", r"security", r"config", r"secret", r"wallet", r"private",
    r"\.env", r"access", r"permission", r"crypto", r"contract"
]

def get_pr_diff(pr_url):
    """Fetches the diff of a GitHub PR."""
    if not pr_url.endswith(".diff"):
        pr_url = pr_url.rstrip("/") + ".diff"
    
    try:
        req = urllib.request.Request(pr_url)
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching PR diff: {e}")
        return None

def is_high_risk(diff_content):
    """Detects if a PR modifies sensitive security files."""
    for pattern in HIGH_RISK_FILES:
        if re.search(pattern, diff_content, re.IGNORECASE):
            return True
    return False

def analyze_diff(diff_content, api_key, security_mode=False):
    """Sends the diff to Claude for analysis."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    system_prompt = "You are a senior software engineer and security auditor."
    if security_mode:
        system_prompt += " FOCUS: Identify security vulnerabilities, data leaks, and authorization bypasses."

    prompt = f"""{system_prompt} Review the following git diff and provide a structured Markdown review.

Diff Content:
```diff
{diff_content}
```

Your response must follow this structure:
### 📝 Summary of Changes
(2–3 concise sentences)

### 🚨 SECURITY AUDIT {"(CRITICAL FOCUS)" if security_mode else ""}
- (Detailed security analysis of changes)

### ⚠️ Potential Risks & Improvement Suggestions
- (List any bugs, performance issues, or cleaner code paths)

### 🛡️ Confidence Score
(Low / Medium / High)
"""

    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['content'][0]['text']
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Claude Code Security-First PR Reviewer")
    parser.add_argument("--pr", help="URL of a specific GitHub Pull Request")
    parser.add_argument("--repo", help="Owner/Repo to review all open PRs")
    parser.add_argument("--security", action="store_true", help="Enable Security Focus Mode")
    args = parser.parse_args()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)
        
    pr_urls = []
    if args.pr:
        pr_urls = [args.pr]
    elif args.repo:
        print(f"📡 Fetching open PRs for {args.repo}...")
        api_url = f"https://api.github.com/repos/{args.repo}/pulls?state=open"
        try:
            with urllib.request.urlopen(api_url) as res:
                prs = json.loads(res.read().decode())
                pr_urls = [p['html_url'] for p in prs]
        except Exception as e:
            print(f"Error fetching repo PRs: {e}")
            sys.exit(1)

    if not pr_urls:
        print("No PRs provided or found.")
        sys.exit(0)

    # Clear previous review file
    if os.path.exists("PR_REVIEW.md"):
        os.remove("PR_REVIEW.md")

    for url in pr_urls:
        print(f"\n🔍 Processing: {url}...")
        diff = get_pr_diff(url)
        if not diff: continue
        
        is_risk = is_high_risk(diff)
        if is_risk:
            print("🚨 HIGH RISK CHANGES DETECTED: Enabling Security Focus Mode.")
            
        review = analyze_diff(diff, api_key, security_mode=args.security or is_risk)
        if review:
            print(review)
            with open("PR_REVIEW.md", "a") as f:
                f.write(f"\n## Review for {url}\n{review}\n")
                f.write("\n---\n")
    
    print("\n✅ All reviews saved to PR_REVIEW.md")

if __name__ == "__main__":
    main()
