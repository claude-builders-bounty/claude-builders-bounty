#!/usr/bin/env python3
"""
Claude Code PR Review Agent

A CLI tool and GitHub Action that reviews PRs using Claude AI,
returning structured Markdown review comments.

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123
    python3 claude-review.py --pr 123 --repo owner/repo --token ghp_xxx

GitHub Action:
    uses: ./.github/workflows/pr-review.yml
"""

import os
import re
import sys
import json
import argparse
import subprocess
from datetime import datetime
from typing import Optional

try:
    import anthropic
except ImportError:
    print("Error: anthropic package required. Install: pip install anthropic")
    sys.exit(1)


# Configuration
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2048


def get_pr_diff(pr_url: str, token: str, repo: Optional[str] = None) -> str:
    """Fetch PR diff via GitHub CLI or API."""
    # Try gh CLI first (already authenticated)
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/pulls/{pr_url.split('/')[-1]}", "--jq", ".body, .title, .base.ref"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            pass  # gh works
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fall back to direct API call
    import urllib.request
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    
    # Parse PR URL or number
    pr_number = pr_url.split("/")[-1] if pr_url else pr_url
    
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        return f"Error fetching PR: {e}"


def analyze_pr_diff(diff: str, pr_info: dict = None) -> dict:
    """
    Analyze PR diff using Claude API.
    
    Returns structured review with:
    - summary: 2-3 sentence summary
    - risks: list of identified risks
    - suggestions: improvement suggestions
    - confidence: Low/Medium/High
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        return {
            "error": "ANTHROPIC_API_KEY environment variable not set",
            "summary": "Could not analyze PR without API key",
            "risks": [],
            "suggestions": ["Set ANTHROPIC_API_KEY environment variable"],
            "confidence": "Low"
        }
    
    client = anthropic.Anthropic(api_key=api_key)
    
    pr_title = pr_info.get("title", "Unknown PR") if pr_info else "Unknown PR"
    pr_description = pr_info.get("body", "No description provided") if pr_info else "No description"
    
    system_prompt = """You are an expert code reviewer. Analyze pull request diffs and provide structured, actionable feedback.

Respond ONLY with valid JSON in this exact format:
{
    "summary": "2-3 sentence summary of what this PR does",
    "risks": ["risk 1", "risk 2", "risk 3"],
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
    "confidence": "High" or "Medium" or "Low",
    "line_count": number of files or lines changed
}

Be critical but constructive. Focus on:
- Security vulnerabilities (injection, auth bypass, data exposure)
- Performance issues (N+1 queries, missing indexes, inefficient algorithms)
- Code quality (readability, maintainability, test coverage)
- Potential bugs (race conditions, error handling, edge cases)
- Architectural concerns (coupling, SOLID violations)

If you cannot fully analyze the diff, estimate confidence accordingly."""

    diff_preview = diff[:15000] if len(diff) > 15000 else diff
    
    user_message = f"""Review this pull request:

**Title**: {pr_title}
**Description**: {pr_description}

**Diff**:
```
{diff_preview}
```

Respond with ONLY JSON, no markdown code blocks or other text."""

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        
        # Parse JSON response
        response_text = response.content[0].text.strip()
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {
                "error": "Could not parse Claude response",
                "raw_response": response_text[:500],
                "summary": "Analysis completed but response format unexpected",
                "risks": [],
                "suggestions": [],
                "confidence": "Low"
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "summary": f"Error calling Claude API: {e}",
            "risks": [],
            "suggestions": ["Check API key and try again"],
            "confidence": "Low"
        }


def format_review_comment(review: dict, pr_url: str) -> str:
    """Format review as GitHub-compatible Markdown."""
    
    confidence_emoji = {
        "High": "✅",
        "Medium": "⚠️",
        "Low": "❌"
    }
    
    emoji = confidence_emoji.get(review.get("confidence", "Low"), "⚠️")
    
    risks = review.get("risks", [])
    suggestions = review.get("suggestions", [])
    
    risks_md = ""
    if risks:
        risks_md = "## Risks\n" + "\n".join(f"- {r}" for r in risks[:5]) + "\n\n"
    
    suggestions_md = ""
    if suggestions:
        suggestions_md = "## Suggestions\n" + "\n".join(f"- {s}" for s in suggestions[:5]) + "\n\n"
    
    confidence = review.get("confidence", "Unknown")
    
    comment = f"""## 🤖 Claude Code PR Review

{emoji} **Confidence**: {confidence}

### Summary
{review.get("summary", "No summary available")}

{risks_md}{suggestions_md}---
*Reviewed by Claude Code AI — {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*PR: {pr_url}*
"""
    
    return comment


def post_review_comment(pr_url: str, comment: str, token: str) -> bool:
    """Post review comment to GitHub PR."""
    import urllib.request
    import urllib.parse
    
    # Parse PR URL to get repo and PR number
    parts = pr_url.replace("https://github.com/", "").split("/")
    if len(parts) < 4:
        print(f"Error: Could not parse PR URL: {pr_url}")
        return False
    
    repo = f"{parts[0]}/{parts[1]}"
    pr_number = parts[3]
    
    api_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = json.dumps({"body": comment}).encode("utf-8")
    
    req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status in (200, 201):
                print(f"✅ Review posted successfully!")
                return True
            else:
                print(f"Error: HTTP {response.status}")
                return False
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"GitHub API error: {e.code} - {error_body}")
        return False
    except Exception as e:
        print(f"Error posting comment: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Agent")
    parser.add_argument("--pr", required=True, help="PR URL or number")
    parser.add_argument("--repo", help="Repository (owner/repo) - required if using PR number")
    parser.add_argument("--token", help="GitHub token (or set GH_TOKEN env var)")
    parser.add_argument("--post", action="store_true", help="Post review as GitHub comment")
    parser.add_argument("--output", choices=["json", "markdown", "both"], default="markdown", help="Output format")
    
    args = parser.parse_args()
    
    # Get token
    token = args.token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    
    # Get repo from CLI or env
    if not args.repo:
        # Try to get from gh cli
        try:
            result = subprocess.run(["gh", "repo", "view", "--jq", ".full_name"], 
                                   capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                args.repo = result.stdout.strip()
        except:
            pass
    
    if not args.repo:
        print("Error: --repo required or run in a git repository")
        sys.exit(1)
    
    print(f"🔍 Fetching PR {args.pr} from {args.repo}...")
    
    # Fetch PR info and diff
    diff = get_pr_diff(args.pr, token, args.repo)
    
    pr_info = {"title": "PR Review", "body": ""}
    
    if not diff or diff.startswith("Error"):
        print(diff or "Failed to fetch PR diff")
        sys.exit(1)
    
    print(f"📊 Analyzing {len(diff)} bytes of changes...")
    
    # Analyze with Claude
    review = analyze_pr_diff(diff, pr_info)
    
    if review.get("error"):
        print(f"⚠️ {review['error']}")
    
    # Format output
    if args.output in ("markdown", "both"):
        comment = format_review_comment(review, args.pr)
        print("\n" + "="*60)
        print(comment)
        print("="*60 + "\n")
    
    if args.output in ("json", "both"):
        print(json.dumps(review, indent=2))
    
    # Post to GitHub if requested
    if args.post and token:
        comment = format_review_comment(review, args.pr)
        success = post_review_comment(args.pr, comment, token)
        sys.exit(0 if success else 1)
    else:
        print("💡 Use --post to post review as GitHub PR comment")


if __name__ == "__main__":
    main()
