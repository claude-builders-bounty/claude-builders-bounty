#!/usr/bin/env python3
"""
claude-review-agent — Claude Code PR review sub-agent

Takes a GitHub PR URL, fetches the diff, analyzes it with Claude,
and posts a structured Markdown review comment to the PR.

Usage:
    python3 claude-review-agent.py --pr https://github.com/owner/repo/pull/123

Requirements:
    - gh CLI (authenticated)
    - Python 3.8+
    - anthropic package: pip install anthropic
"""

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


@dataclass
class PRInfo:
    url: str
    owner: str
    repo: str
    pr_number: int
    title: str = ""
    body: str = ""
    author: str = ""
    files: list = field(default_factory=list)
    diff: str = ""


def run_cmd(cmd: list, timeout: int = 30) -> str:
    """Run a shell command and return stdout."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out after {timeout}s: {' '.join(cmd)}")


def fetch_pr_info(pr_url: str) -> PRInfo:
    """Fetch PR details using gh CLI."""
    # Parse URL
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+)', pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")

    owner, repo, pr_num = match.groups()

    REPO_ARG = f'{owner}/{repo}'
    PR_ARG = pr_num

    # Fetch PR data
    title = run_cmd(['gh', 'pr', 'view', PR_ARG, '--repo', REPO_ARG, '--json', 'title', '--jq', '.title'])
    body = run_cmd(['gh', 'pr', 'view', PR_ARG, '--repo', REPO_ARG, '--json', 'body', '--jq', '.body // ""'])
    author = run_cmd(['gh', 'pr', 'view', PR_ARG, '--repo', REPO_ARG, '--json', 'author', '--jq', '.author.login'])

    try:
        files_raw = run_cmd(['gh', 'pr', 'view', PR_ARG, '--repo', REPO_ARG, '--json', 'files', '--jq', '[.files[].path]'])
        files = json.loads(files_raw) if files_raw else []
    except Exception:
        files = []

    diff = run_cmd(['gh', 'pr', 'diff', PR_ARG, '--repo', REPO_ARG], timeout=60)

    return PRInfo(
        url=pr_url,
        owner=owner,
        repo=repo,
        pr_number=int(pr_num),
        title=title,
        body=body or "",
        author=author,
        files=files,
        diff=diff
    )


REVIEW_PROMPT_TEMPLATE = """You are an expert code reviewer. Analyze the following pull request and provide a structured review.

## PR Information
- Title: {title}
- Author: @{author}
- URL: {url}
- Files: {files}

## Your Task
Provide your review in this exact Markdown format:

## 📋 Summary
[2-3 sentences describing what this PR does and why]

## ⚠️ Risks
- [Risk 1 - specific and actionable]
- [Risk 2 - specific and actionable]
- [Risk 3 - specific and actionable]

## 💡 Improvements
- [Suggestion 1 - specific and actionable]
- [Suggestion 2 - specific and actionable]
- [Suggestion 3 - specific and actionable]

## 🎯 Confidence
Confidence: [Low/Medium/High]
Reasoning: [Brief explanation of your confidence level]

## 📁 Diff
```
{diff}
```

Focus on: security issues, bugs, edge cases, performance problems, maintainability,
and actionable improvements. Be specific about line numbers and code snippets when relevant.
"""


def analyze_with_anthropic(pr: PRInfo, model: str = "claude-3-5-sonnet-20241022") -> str:
    """Analyze PR diff using Anthropic Claude API."""
    if not HAS_ANTHROPIC:
        raise RuntimeError("anthroic package not installed. Run: pip install anthropic")

    client = anthropic.Anthropic()

    prompt = REVIEW_PROMPT_TEMPLATE.format(
        title=pr.title,
        author=pr.author,
        url=pr.url,
        files=', '.join(pr.files) if pr.files else 'Unknown',
        diff=pr.diff[:12000]  # Limit to first 12k chars to stay within token limits
    )

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return message.content[0].text


def analyze_with_claude_cli(pr: PRInfo) -> str:
    """Analyze PR diff using claude CLI."""
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        title=pr.title,
        author=pr.author,
        url=pr.url,
        files=', '.join(pr.files) if pr.files else 'Unknown',
        diff=pr.diff[:12000]
    )

    try:
        result = subprocess.run(
            ['claude', '--print', prompt],
            capture_output=True,
            text=True,
            env={**os.environ, 'CLAUDE_NO_SPINNER': '1'},
            timeout=120
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        raise RuntimeError(f"claude CLI failed: {e}")

    raise RuntimeError("claude CLI returned no output")


def analyze_with_zai_api(pr: PRInfo) -> str:
    """Analyze PR diff using ZAI/GLM API."""
    import urllib.request

    zai_api = os.environ.get('ZAI_API', 'https://api.z.ai/api/coding/paas/v4/chat/completions')
    zai_key = os.environ.get('ZAI_API_KEY', '')

    if not zai_key:
        raise RuntimeError("ZAI_API_KEY env var not set")

    prompt = REVIEW_PROMPT_TEMPLATE.format(
        title=pr.title,
        author=pr.author,
        url=pr.url,
        files=', '.join(pr.files) if pr.files else 'Unknown',
        diff=pr.diff[:10000]  # Limit to first 10k chars
    )

    data = json.dumps({
        'model': 'glm-4.7',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 4096
    }).encode('utf-8')

    req = urllib.request.Request(
        zai_api,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {zai_key}'
        }
    )

    try:
        resp = urllib.request.urlopen(req, timeout=120)
        result = json.loads(resp.read().decode('utf-8'))
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        if not content and 'usage' in result:
            # ZAI might return usage without content in some response formats
            content = result.get('reply', '')
        return content if content else 'Review generation returned empty response'
    except Exception as e:
        raise RuntimeError(f"ZAI API call failed: {e}")


def generate_review(pr: PRInfo) -> str:
    """Generate review using available method."""

    # Try ZAI API first (most likely to be configured)
    if os.environ.get('ZAI_API_KEY'):
        try:
            return analyze_with_zai_api(pr)
        except Exception as e:
            print(f"ZAI API: {e}", file=sys.stderr)

    # Try Anthropic API second
    if HAS_ANTHROPIC:
        try:
            return analyze_with_anthropic(pr)
        except Exception as e:
            print(f"Anthropic API: {e}", file=sys.stderr)

    # Try claude CLI
    try:
        return analyze_with_claude_cli(pr)
    except Exception as e:
        print(f"claude CLI: {e}", file=sys.stderr)

    # Fallback: Generate a structured review from static analysis
    print("Warning: No API available, using static analysis fallback")
    return generate_static_review(pr)


def summary_generator(title: str, author: str, file_count: int, added: int, removed: int) -> str:
    """Generate a summary sentence from PR metadata."""
    lang = "Python" if file_count > 0 else "code"
    return (
        f"This PR by @{author} modifies {file_count} file(s) "
        f"({added} lines added, {removed} removed) for the project \"{title[:60]}{'...' if len(title) > 60 else ''}\". "
        f"The changes appear to be focused on {lang} implementation updates."
    )


def generate_static_review(pr: PRInfo) -> str:
    """Generate a structured review using static analysis when no API is available."""

    diff_lines = pr.diff.split('\n')
    added_lines = [l for l in diff_lines if l.startswith('+') and not l.startswith('+++')]
    removed_lines = [l for l in diff_lines if l.startswith('-') and not l.startswith('---')]
    file_count = len(pr.files) if pr.files else 0

    # Analyze file types
    file_extensions = {}
    for f in (pr.files or []):
        ext = f.split('.')[-1] if '.' in f else 'unknown'
        file_extensions[ext] = file_extensions.get(ext, 0) + 1

    # Generate risk assessment based on patterns
    risks = []
    improvements = []

    # Check for common security issues in diff
    diff_lower = pr.diff.lower()
    if 'password' in diff_lower or 'secret' in diff_lower or 'api_key' in diff_lower:
        risks.append("⚠️ Potential secret/API key exposure in diff - ensure secrets are not hardcoded")
    if 'eval(' in diff_lower or 'exec(' in diff_lower:
        risks.append("⚠️ Use of eval()/exec() detected - potential code injection risk")
    if 'http://' in diff_lower and 'localhost' not in diff_lower:
        risks.append("⚠️ Non-HTTPS URL detected - data may be transmitted insecurely")

    # Check for improvements
    if len(added_lines) > 500:
        improvements.append("📦 Large PR (>500 lines added) - consider breaking into smaller, focused PRs")
    if file_count > 10:
        improvements.append("📁 Many files changed (>10) - ensure each commit is focused and atomic")

    if not risks:
        risks.append("✅ No obvious security issues detected in the changed code")

    if not improvements:
        improvements.append("💡 PR looks reasonably scoped - continue with thorough testing")

    ext_summary = ', '.join([f"{ext} ({count})" for ext, count in sorted(file_extensions.items())])

    return f"""## 📋 Summary
{summary_generator(pr.title, pr.author, file_count, len(added_lines), len(removed_lines))}

## ⚠️ Risks
{' '.join(risks)}

## 💡 Improvements
{' '.join(improvements)}

## 🎯 Confidence
Confidence: Low
Reasoning: Static analysis only - no AI model available for semantic code review. Manual review recommended for critical changes.

## 📁 Files Changed
{file_count} files changed: {ext_summary}

## 📊 Diff Statistics
- Lines added: {len(added_lines)}
- Lines removed: {len(removed_lines)}
- Total changed: {len(added_lines) + len(removed_lines)}

---
*Generated by claude-review-agent (static analysis mode)*"""


def post_review_comment(pr: PRInfo, review: str) -> str:
    """Post the review as a PR comment using gh CLI."""
    import shlex
    review_escaped = review.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

    result = subprocess.run(
        ['gh', 'api', f'repos/{pr.owner}/{pr.repo}/issues/{pr.pr_number}/comments',
         '-f', f'body={review_escaped}', '--jq', '.html_url'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to post comment: {result.stderr}")

    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description='Claude Code PR Review Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 claude-review-agent.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review-agent.py --pr https://github.com/owner/repo/pull/123 --post
  python3 claude-review-agent.py --pr https://github.com/owner/repo/pull/123 --model opus

Environment variables:
  CLAUDE_CODE   Alternative API endpoint for review generation
        """
    )
    parser.add_argument('--pr', required=True, help='GitHub PR URL')
    parser.add_argument('--post', action='store_true', help='Post review as PR comment')
    parser.add_argument('--model', default='claude-3-5-sonnet-20241022',
                       help='Anthropic model to use')

    args = parser.parse_args()

    print(f"Fetching PR info from {args.pr}...")
    pr = fetch_pr_info(args.pr)

    print(f"Analyzing PR #{pr.pr_number}: {pr.title}")
    print(f"Author: @{pr.author}")
    if pr.files:
        print(f"Files: {', '.join(pr.files[:10])}{' ...' if len(pr.files) > 10 else ''}")
    print(f"Diff size: {len(pr.diff):,} characters")

    print("\nGenerating review with Claude...")
    review = generate_review(pr)

    print("\n" + "="*60)
    print("STRUCTURED PR REVIEW")
    print("="*60)
    print(review)
    print("="*60)

    if args.post:
        print(f"\nPosting review to PR...")
        try:
            comment_url = post_review_comment(pr, review)
            print(f"Posted to: {comment_url}")
        except Exception as e:
            print(f"Failed to post: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())