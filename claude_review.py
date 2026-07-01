#!/usr/bin/env python3
"""
claude-review — CLI tool that reviews a GitHub PR and posts structured Markdown output.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --output report.md
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, and PR number."""
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN or GH_TOKEN environment variable is required")
    return token


def get_deepseek_api_key() -> tuple[str, str]:
    """Get DeepSeek API key and URL."""
    key = os.environ.get("DEEPSEEK_API_KEY")
    url = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    return key, url


def fetch_pr_info(owner: str, repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR metadata from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review/1.0",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Fetch PR diff from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    })
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def fetch_pr_commits(owner: str, repo: str, pr_number: int, token: str) -> list[dict]:
    """Fetch PR commits from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review/1.0",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def review_with_deepseek(diff: str, pr_info: dict, commits: list[dict], api_key: str, api_url: str) -> str:
    """Send PR diff to DeepSeek for analysis and return structured review."""
    
    # Prepare commit messages summary
    commit_msgs = "\n".join(f"- {c['commit']['message'].split(chr(10))[0]}" for c in commits[:10])
    
    # Truncate very large diffs
    if len(diff) > 30000:
        diff = diff[:30000] + "\n\n... [diff truncated]"
    
    prompt = f"""You are a senior code reviewer. Review the following GitHub Pull Request and provide structured feedback.

## PR Information
- Title: {pr_info.get('title', 'N/A')}
- Author: {pr_info['user']['login'] if pr_info.get('user') else 'N/A'}
- Files changed: {pr_info.get('changed_files', 'N/A')}
- Additions: {pr_info.get('additions', 'N/A')}
- Deletions: {pr_info.get('deletions', 'N/A')}
- Commits:
{commit_msgs}

## Diff
```diff
{diff}
```

## Instructions
Analyze this PR and provide a structured review with:

1. **Summary** (2-3 sentences describing what the PR does)
2. **Identified Risks** (bullet list of potential issues, bugs, or concerns)
3. **Improvement Suggestions** (bullet list of actionable suggestions)
4. **Confidence Score** (Low / Medium / High — based on how confident you are in your review)

Be thorough but practical. Focus on:
- Correctness (does the code do what it should?)
- Security (any vulnerabilities?)
- Performance (any bottlenecks?)
- Maintainability (is the code clean and well-structured?)
- Edge cases (what could break?)
"""
    
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a senior software engineer doing code review. Output structured Markdown."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }).encode("utf-8")
    
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return f"**Error calling LLM API:** HTTP {e.code}\n\n```\n{body}\n```"
    except Exception as e:
        return f"**Error calling LLM API:** {e}"


def format_review(review: str, pr_url: str) -> str:
    """Wrap the review in a nice Markdown document."""
    return f"""# 🤖 PR Review — Automated

**PR:** [{pr_url}]({pr_url})

---

{review}

---

*Review generated by [claude-review](https://github.com/AISoftMaster/claude-review)*
"""


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR using AI")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    try:
        # Parse PR URL
        owner, repo, pr_number = parse_pr_url(args.pr)
        
        # Get tokens
        github_token = get_github_token()
        deepseek_key, deepseek_url = get_deepseek_api_key()
        
        # Fetch PR info
        print(f"🔍 Fetching PR {owner}/{repo}#{pr_number}...", file=sys.stderr)
        pr_info = fetch_pr_info(owner, repo, pr_number, github_token)
        diff = fetch_pr_diff(owner, repo, pr_number, github_token)
        commits = fetch_pr_commits(owner, repo, pr_number, github_token)
        
        print(f"📝 Files: {pr_info.get('changed_files', '?')}  "
              f"++{pr_info.get('additions', '?')}  "
              f"--{pr_info.get('deletions', '?')}", file=sys.stderr)
        print(f"🤖 Analyzing with DeepSeek...", file=sys.stderr)
        
        # Review with DeepSeek
        review = review_with_deepseek(diff, pr_info, commits, deepseek_key, deepseek_url)
        
        # Format output
        output = format_review(review, args.pr)
        
        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"✅ Review written to {args.output}", file=sys.stderr)
        else:
            print(output)
            
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        print(f"❌ HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
