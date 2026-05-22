#!/usr/bin/env python3
"""
review-pr.py - Review a GitHub PR via the GitHub API.

Usage:
    python scripts/review-pr.py <PR_URL or owner/repo#number>

Requirements:
    pip install anthropic requests

Environment:
    GITHUB_TOKEN - GitHub personal access token
    ANTHROPIC_API_KEY - Anthropic API key
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def api_get(url, token):
    """Make an authenticated GET request to the GitHub API."""
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "pr-review-agent/1.0",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def api_post(url, token, body):
    """Make an authenticated POST request to the GitHub API."""
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "pr-review-agent/1.0",
    }, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def normalize_pr_ref(ref):
    """Convert PR URL to API endpoint."""
    if ref.startswith("http"):
        m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", ref)
        if m:
            return m.group(1), m.group(2), int(m.group(3))
        raise ValueError(f"Invalid PR URL: {ref}")
    m = re.match(r"([^/]+)/([^#]+)#(\d+)", ref)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(f"Invalid PR reference: {ref}. Use owner/repo#number or full URL.")


def fetch_pr(owner, repo, number, token):
    """Fetch PR details and diff from GitHub."""
    pr = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}", token)
    files = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files?per_page=100", token)

    diff_parts = []
    for f in files:
        if f.get("patch"):
            diff_parts.append(f"--- {f['filename']} (+{f['additions']}/-{f['deletions']}) ---\n{f['patch']}")

    return {
        "title": pr["title"],
        "body": pr.get("body", "") or "",
        "url": pr["html_url"],
        "author": pr["user"]["login"],
        "files_changed": len(files),
        "additions": pr["additions"],
        "deletions": pr["deletions"],
        "diff": "\n\n".join(diff_parts),
    }


def review_with_claude(pr_data):
    """Send PR data to Claude for review."""
    try:
        import anthropic
    except ImportError:
        print("[ERROR] anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""You are a senior software engineer conducting a thorough code review.

## PR: {pr_data['title']}

**Author:** {pr_data['author']}
**Files changed:** {pr_data['files_changed']} (+{pr_data['additions']}/-{pr_data['deletions']})

### Description
{pr_data['body']}

### Diff
```
{pr_data['diff'][:8000]}
```

Provide a structured review with these exact sections:

## Summary
(2-3 sentences summarizing what this PR does)

## Risks
- (List specific risks: security, correctness, performance, edge cases)
(If no significant risks, write "No significant risks identified.")

## Improvement Suggestions
- (List specific, actionable suggestions)
(If the code is clean, write "Code looks clean. No major suggestions.")

## Verdict
(APPROVE / REQUEST_CHANGES / COMMENT with one-line justification)

Keep each section concise. Be specific — reference exact code patterns when possible."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <PR_URL or owner/repo#number>")
        sys.exit(1)

    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        print("[ERROR] GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    # Check for dry-run mode (no API key needed)
    dry_run = os.environ.get("ANTHROPIC_API_KEY") is None

    ref = sys.argv[1]
    try:
        owner, repo, number = normalize_pr_ref(ref)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"🔍 Fetching PR #{number} from {owner}/{repo}...")
    pr = fetch_pr(owner, repo, number, gh_token)
    print(f"   Title: {pr['title']}")
    print(f"   Files: {pr['files_changed']} (+{pr['additions']}/-{pr['deletions']})")

    if dry_run:
        print("\n⚠️  No ANTHROPIC_API_KEY set — outputting prompt only:")
        print(f"\nPR: {pr['title']}\n{pr['body']}\n\nDiff:\n{pr['diff'][:2000]}...")
        sys.exit(0)

    print("\n🤖 Running Claude review...")
    review = review_with_claude(pr)

    print("\n" + "=" * 60)
    print(review)
    print("=" * 60)

    # Post review as PR comment
    print(f"\n📤 Posting review to {pr['url']}...")
    try:
        api_post(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments",
            gh_token,
            {"body": review},
        )
        print("✅ Review posted successfully!")
    except Exception as e:
        print(f"⚠️  Could not post comment: {e}")
        print("   Review output above can be posted manually.")


if __name__ == "__main__":
    main()
