#!/usr/bin/env python3
"""
Claude Code PR Review Agent

Analyzes pull request diffs and generates structured review comments.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --diff diff.txt --repo owner/repo

Features:
- Fetches PR diff from GitHub API
- Analyzes code changes with Claude API
- Generates structured markdown review
- Posts comment to PR (optional)
- Retry logic with exponential backoff
- Comprehensive error handling
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# =============================================================================
# CONFIGURATION
# =============================================================================

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
CLAUDE_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-20250514')

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
TIMEOUT = 30  # seconds for API requests

# =============================================================================
# VALIDATION
# =============================================================================

def validate_github_token(token: str) -> bool:
    """Validate GitHub token format and permissions."""
    if not token:
        return False
    # GitHub token format: ghp_ followed by 36 alphanumeric characters
    if not re.match(r'^ghp_[a-zA-Z0-9]{36}$', token):
        print("⚠️  Warning: GITHUB_TOKEN format looks invalid (expected ghp_...)")
        return False
    return True

def validate_claude_api_key(key: str) -> bool:
    """Validate Claude API key format."""
    if not key:
        return False
    # Anthropic API key format: sk-ant-...
    if not key.startswith('sk-ant-'):
        print("⚠️  Warning: ANTHROPIC_API_KEY format looks invalid (expected sk-ant-...)")
        return False
    return True

def require_env_var(name: str, value: str, validator=None) -> str:
    """Require an environment variable to be set and valid."""
    if not value:
        raise ValueError(f"{name} environment variable is required")
    if validator and not validator(value):
        raise ValueError(f"{name} validation failed")
    return value

# =============================================================================
# RETRY UTILITIES
# =============================================================================

def retry_with_backoff(func, max_retries=MAX_RETRIES, delay=RETRY_DELAY, exceptions=(Exception,)):
    """Execute function with exponential backoff retry logic."""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                print(f"⚠️  Attempt {attempt + 1}/{max_retries} failed: {e}")
                print(f"   Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ All {max_retries} attempts failed")
    
    raise last_exception

# =============================================================================
# GITHUB API
# =============================================================================

def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """Fetch PR details and diff from GitHub API with retry logic."""
    
    def _fetch():
        require_env_var('GITHUB_TOKEN', GITHUB_TOKEN, validate_github_token)
        
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        
        # Fetch PR metadata first
        req = urllib.request.Request(
            pr_url,
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Claude-Review-Agent/1.0'
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                pr_data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(f"PR #{pr_number} not found in {owner}/{repo}")
            elif e.code == 401:
                raise ValueError("GitHub API authentication failed - check GITHUB_TOKEN")
            elif e.code == 403:
                raise ValueError("GitHub API rate limit exceeded or insufficient permissions")
            else:
                raise ValueError(f"GitHub API error: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            raise ValueError(f"Network error connecting to GitHub API: {e.reason}")
        
        # Fetch PR diff
        req = urllib.request.Request(
            pr_url,
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+diff',
                'User-Agent': 'Claude-Review-Agent/1.0'
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                diff_text = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            raise ValueError(f"Failed to fetch PR diff: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            raise ValueError(f"Network error fetching diff: {e.reason}")
        
        return {
            'diff': diff_text,
            'title': pr_data.get('title', ''),
            'body': pr_data.get('body', ''),
            'author': pr_data.get('user', {}).get('login', ''),
            'files_changed': pr_data.get('changed_files', 0),
            'additions': pr_data.get('additions', 0),
            'deletions': pr_data.get('deletions', 0),
            'state': pr_data.get('state', 'open'),
            'created_at': pr_data.get('created_at', ''),
        }
    
    return retry_with_backoff(_fetch, exceptions=(ValueError,))

def post_pr_comment(owner: str, repo: str, pr_number: int, comment: str) -> Dict[str, Any]:
    """Post comment to PR with retry logic."""
    
    def _post():
        require_env_var('GITHUB_TOKEN', GITHUB_TOKEN, validate_github_token)
        
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        
        data = {'body': comment}
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {GITHUB_TOKEN}',
                'Content-Type': 'application/json',
                'User-Agent': 'Claude-Review-Agent/1.0'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 403:
                raise ValueError("No permission to comment on this PR")
            elif e.code == 404:
                raise ValueError(f"PR #{pr_number} not found")
            else:
                raise ValueError(f"Failed to post comment: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            raise ValueError(f"Network error posting comment: {e.reason}")
    
    return retry_with_backoff(_post, exceptions=(ValueError,))

# =============================================================================
# CLAUDE API
# =============================================================================

def analyze_with_claude(pr_data: Dict[str, Any], owner: str, repo: str, pr_number: int) -> str:
    """Send PR diff to Claude for analysis with retry logic."""
    
    def _analyze():
        require_env_var('ANTHROPIC_API_KEY', CLAUDE_API_KEY, validate_claude_api_key)
        
        system_prompt = """You are an expert code reviewer. Analyze the pull request diff and provide a structured, constructive review.

Your review should:
1. Start with a brief summary of what changes were made
2. Highlight positive aspects (good practices, clean code, etc.)
3. Identify potential issues (bugs, security concerns, performance issues)
4. Suggest improvements (code quality, readability, best practices)
5. End with a clear recommendation (LGTM, needs changes, or requires discussion)

Be specific, reference line numbers when possible, and maintain a helpful, encouraging tone.

Format your response in markdown with clear section headers."""

        # Truncate diff if too large (Claude max context)
        max_diff_size = 100000
        diff_text = pr_data['diff']
        if len(diff_text) > max_diff_size:
            diff_text = diff_text[:max_diff_size] + "\n\n[... diff truncated ...]"

        user_prompt = f"""Please review this pull request:

**Repository:** {owner}/{repo}
**PR #{pr_number}**
**Title:** {pr_data['title']}
**Author:** @{pr_data['author']}

**Changes:**
- Files changed: {pr_data['files_changed']}
- Additions: {pr_data['additions']}
- Deletions: {pr_data['deletions']}

**PR Description:**
{pr_data['body'] or 'No description provided.'}

**Diff:**
```diff
{diff_text}
```

Please provide a structured code review in markdown format."""

        url = "https://api.anthropic.com/v1/messages"
        data = {
            'model': CLAUDE_MODEL,
            'max_tokens': 4096,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': user_prompt}]
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {CLAUDE_API_KEY}',
                'Content-Type': 'application/json',
                'x-api-key': CLAUDE_API_KEY,
                'anthropic-version': '2023-06-01',
                'User-Agent': 'Claude-Review-Agent/1.0'
            },
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['content'][0]['text']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            if e.code == 401:
                raise ValueError("Claude API authentication failed - check ANTHROPIC_API_KEY")
            elif e.code == 429:
                raise ValueError("Claude API rate limit exceeded")
            elif e.code == 500:
                raise ValueError(f"Claude API server error: {e.code}")
            else:
                raise ValueError(f"Claude API error: {e.code} - {error_body[:200]}")
        except urllib.error.URLError as e:
            raise ValueError(f"Network error connecting to Claude API: {e.reason}")
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected Claude API response format: {e}")
    
    return retry_with_backoff(_analyze, exceptions=(ValueError,))

# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def format_review_comment(review: str, pr_data: Dict[str, Any], owner: str, repo: str, pr_number: int) -> str:
    """Format the review comment for posting."""
    header = f"""## 🤖 Automated PR Review by Claude

**PR:** #{pr_number} - {pr_data['title']}
**Author:** @{pr_data['author']}
**Changes:** {pr_data['files_changed']} files, +{pr_data['additions']} -{pr_data['deletions']}

---

"""
    footer = f"""
---

*This review was generated automatically by Claude Code PR Review Agent.*

**Configuration:**
- Model: {CLAUDE_MODEL}
- Repository: {owner}/{repo}

To report issues or provide feedback, please open an issue in the repository."""
    
    return header + review + footer

# =============================================================================
# CLI
# =============================================================================

def parse_github_url(url: str) -> tuple:
    """Parse GitHub PR URL into owner, repo, pr_number."""
    pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.search(pattern, url)
    
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    
    return match.group(1), match.group(2), int(match.group(3))

def main():
    parser = argparse.ArgumentParser(
        description='Claude Code PR Review Agent - Automated code review for GitHub PRs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  GITHUB_TOKEN         GitHub Personal Access Token (required)
  ANTHROPIC_API_KEY    Claude API Key (required)
  CLAUDE_MODEL         Claude model to use (default: claude-sonnet-4-20250514)

Examples:
  # Review a PR and post comment
  claude-review --pr https://github.com/owner/repo/pull/123 --post
  
  # Review and save to file
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
  
  # Review a diff file
  claude-review --diff changes.diff --repo owner/repo
"""
    )
    parser.add_argument(
        '--pr',
        type=str,
        help='GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)'
    )
    parser.add_argument(
        '--diff',
        type=str,
        help='Path to diff file (alternative to --pr)'
    )
    parser.add_argument(
        '--repo',
        type=str,
        help='Repository in format owner/repo (required with --diff)'
    )
    parser.add_argument(
        '--post',
        action='store_true',
        help='Post review as comment on PR'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save review to file instead of posting'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.pr and not args.diff:
        parser.error("Either --pr or --diff is required")
    
    if args.diff and not args.repo:
        parser.error("--repo is required when using --diff")
    
    # Pre-flight validation
    print("🔍 Validating configuration...")
    if not validate_github_token(GITHUB_TOKEN):
        print("⚠️  Warning: GITHUB_TOKEN may be invalid")
    if not validate_claude_api_key(CLAUDE_API_KEY):
        print("⚠️  Warning: ANTHROPIC_API_KEY may be invalid")
    
    try:
        # Fetch or load diff
        if args.pr:
            owner, repo, pr_number = parse_github_url(args.pr)
            print(f"📥 Fetching PR #{pr_number} from {owner}/{repo}...")
            pr_data = fetch_pr_diff(owner, repo, pr_number)
        else:
            owner, repo = args.repo.split('/')
            pr_number = 0
            with open(args.diff, 'r') as f:
                diff_text = f.read()
            pr_data = {
                'diff': diff_text,
                'title': 'Manual diff review',
                'body': '',
                'author': 'unknown',
                'files_changed': diff_text.count('diff --git'),
                'additions': diff_text.count('\n+'),
                'deletions': diff_text.count('\n-'),
                'state': 'unknown',
                'created_at': '',
            }
        
        print(f"📊 Analyzing {pr_data['files_changed']} files ({pr_data['additions']} additions, {pr_data['deletions']} deletions)...")
        
        # Analyze with Claude
        print("🤖 Sending to Claude for analysis...")
        review = analyze_with_claude(pr_data, owner, repo, pr_number)
        
        # Format output
        formatted_review = format_review_comment(review, pr_data, owner, repo, pr_number)
        
        # Output
        if args.post and args.pr:
            print(f"📝 Posting review to PR #{pr_number}...")
            result = post_pr_comment(owner, repo, pr_number, formatted_review)
            print(f"✅ Review posted! {result.get('html_url', 'N/A')}")
        elif args.output:
            with open(args.output, 'w') as f:
                f.write(formatted_review)
            print(f"✅ Review saved to {args.output}")
        else:
            print("\n" + "=" * 80)
            print(formatted_review)
            print("=" * 80)
        
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
