#!/usr/bin/env python3
"""
Claude Code Sub-Agent: PR Reviewer
Takes a GitHub PR URL or diff, analyzes changes, and outputs a structured Markdown review.
"""

import sys
import json
import urllib.request
import re

def parse_pr_url(url):
    # e.g. https://github.com/owner/repo/pull/123
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return m.groups()

def fetch_pr_diff(owner, repo, pr_number, token=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/vnd.github.v3.diff')
    if token:
        req.add_header('Authorization', f'token {token}')
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode('utf-8')

def analyze_diff(diff_text):
    lines = diff_text.splitlines()
    files_changed = 0
    additions = 0
    deletions = 0
    risks = []
    suggestions = []

    for line in lines:
        if line.startswith('diff --git'):
            files_changed += 1
        elif line.startswith('+') and not line.startswith('+++'):
            additions += 1
            if 'eval(' in line or 'exec(' in line or 'os.system' in line:
                risks.append(f"Potential unsafe execution found: `{line.strip()}`")
            if 'password' in line.lower() or 'secret' in line.lower() or 'api_key' in line.lower():
                risks.append(f"Possible hardcoded secret or credential: `{line.strip()}`")
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1

    if files_changed > 10:
        risks.append("Large PR scope (>10 files changed). Consider breaking down into smaller PRs.")
    if additions > 500:
        suggestions.append("High addition volume (>500 lines). Ensure adequate test coverage is included.")
    
    if not risks:
        risks.append("No high-severity security risks or anti-patterns detected in diff.")
    if not suggestions:
        suggestions.append("Code structure is clean. Ensure unit tests pass before merging.")

    summary = f"PR introduces changes across {files_changed} file(s) with {additions} additions and {deletions} deletions."
    
    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: claude-review --pr <PR_URL>")
        sys.exit(1)
        
    url = sys.argv[2] if sys.argv[1] == '--pr' else sys.argv[1]
    try:
        owner, repo, pr_num = parse_pr_url(url)
        print(f"Analyzing PR #{pr_num} on {owner}/{repo}...")
        # For offline testing or API fallback
        diff = fetch_pr_diff(owner, repo, pr_num)
        analysis = analyze_diff(diff)
        
        print("\n## PR Review Summary")
        print(f"- **Summary**: {analysis['summary']}")
        print("\n### Identified Risks")
        for r in analysis['risks']:
            print(f"- {r}")
        print("\n### Improvement Suggestions")
        for s in analysis['suggestions']:
            print(f"- {s}")
            
    except Exception as e:
        print(f"Error reviewing PR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
