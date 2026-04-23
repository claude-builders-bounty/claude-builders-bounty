#!/usr/bin/env python3
"""
Claude PR Review Agent

Analyzes GitHub pull requests and generates structured code reviews using Claude API.

Usage:
    claude-pr-review --pr https://github.com/owner/repo/pull/123
    claude-pr-review --pr URL --post  # Post as comment
    claude-pr-review --pr URL --output review.md

Features:
- Smart confidence scoring based on complexity
- Cost tracking (tokens + USD)
- Structured review format (Summary, Security, Quality, Suggestions)
- Verdict system (APPROVE/COMMENT/REQUEST_CHANGES)
- Line-specific feedback
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, Tuple, Optional
from urllib import request, error
from datetime import datetime


# =============================================================================
# CONFIGURATION
# =============================================================================

GITHUB_API_BASE = "https://api.github.com"
CLAUDE_API_BASE = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Cost per 1M tokens (April 2026 pricing)
COST_INPUT_PER_1M = 3.00  # $3/1M input tokens
COST_OUTPUT_PER_1M = 15.00  # $15/1M output tokens


# =============================================================================
# GITHUB API FUNCTIONS
# =============================================================================

def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """
    Parse GitHub PR URL into owner, repo, PR number.

    Args:
        url: GitHub PR URL (https://github.com/owner/repo/pull/123)

    Returns:
        Tuple of (owner, repo, pr_number)

    Raises:
        ValueError: If URL format is invalid
    """
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)

    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")

    owner, repo, pr_number = match.groups()
    return owner, repo, int(pr_number)


def github_api_request(endpoint: str, token: str, method: str = "GET") -> Dict:
    """
    Make authenticated GitHub API request.

    Args:
        endpoint: API endpoint (e.g., /repos/owner/repo/pulls/123)
        token: GitHub personal access token
        method: HTTP method (GET, POST)

    Returns:
        JSON response as dict

    Raises:
        Exception: If API request fails
    """
    url = f"{GITHUB_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Claude-PR-Review-Agent"
    }

    req = request.Request(url, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=30) as response:
            if method == "GET" and "diff" in endpoint:
                # Return raw diff text for diff endpoint
                return response.read().decode('utf-8')
            return json.loads(response.read().decode('utf-8'))
    except error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"GitHub API error {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"GitHub API request failed: {str(e)}")


def fetch_pr_metadata(owner: str, repo: str, pr_number: int, token: str) -> Dict:
    """
    Fetch PR metadata (title, author, stats).

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        token: GitHub token

    Returns:
        Dict with PR metadata
    """
    endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
    pr_data = github_api_request(endpoint, token)

    return {
        "number": pr_data["number"],
        "title": pr_data["title"],
        "author": pr_data["user"]["login"],
        "additions": pr_data["additions"],
        "deletions": pr_data["deletions"],
        "files_changed": pr_data["changed_files"],
        "body": pr_data.get("body", ""),
        "url": pr_data["html_url"]
    }


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """
    Fetch PR diff.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        token: GitHub token

    Returns:
        Diff text
    """
    # Use media type to get diff format
    endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
    url = f"{GITHUB_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "Claude-PR-Review-Agent"
    }

    req = request.Request(url, headers=headers)

    try:
        with request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        raise Exception(f"Failed to fetch PR diff: {str(e)}")


# =============================================================================
# CLAUDE API FUNCTIONS
# =============================================================================

def build_review_prompt(diff: str, metadata: Dict) -> str:
    """
    Build Claude prompt for PR review.

    Args:
        diff: PR diff text
        metadata: PR metadata dict

    Returns:
        Formatted prompt string
    """
    prompt = f"""You are an expert code reviewer. Analyze this pull request and provide a structured review.

**PR Information:**
- Title: {metadata['title']}
- Author: @{metadata['author']}
- Files Changed: {metadata['files_changed']}
- Lines: +{metadata['additions']} -{metadata['deletions']}

**Instructions:**
1. Provide a 2-3 sentence summary of the changes
2. Identify security issues (SQL injection, XSS, hardcoded secrets, auth issues)
3. Assess code quality (complexity, error handling, naming, separation of concerns)
4. Suggest improvements (not required changes, but nice-to-haves)
5. Be constructive and specific - reference line numbers when possible

**Output Format (use markdown):**
```
### 📊 Summary
[2-3 sentences describing what changed and why]

### 🔒 Security Analysis
- ✅ [Good practice found]
- ⚠️ Line X: [Issue description]
- ⚠️ Line Y: [Issue description]

### 💎 Code Quality
- ✅ [Positive aspect]
- ⚠️ Line X: [Issue description]
- ✅ [Another positive]

### 💡 Improvement Suggestions
1. [Suggestion 1]
2. [Suggestion 2]
3. [Suggestion 3]
```

**PR Diff:**
```diff
{diff[:15000]}  # Limit to ~15K chars to stay within context
```

Generate the review now:"""

    return prompt


def call_claude_api(prompt: str, api_key: str) -> Tuple[str, int, int]:
    """
    Call Claude API to generate review.

    Args:
        prompt: Review prompt
        api_key: Anthropic API key

    Returns:
        Tuple of (review_text, input_tokens, output_tokens)

    Raises:
        Exception: If API call fails
    """
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": CLAUDE_MODEL,
        "max_tokens": 4000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    req = request.Request(
        CLAUDE_API_BASE,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method="POST"
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))

            review_text = result["content"][0]["text"]
            input_tokens = result["usage"]["input_tokens"]
            output_tokens = result["usage"]["output_tokens"]

            return review_text, input_tokens, output_tokens
    except error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"Claude API error {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"Claude API request failed: {str(e)}")


# =============================================================================
# CONFIDENCE SCORING
# =============================================================================

def calculate_confidence(pr_data: Dict) -> str:
    """
    Calculate confidence score based on PR complexity.

    Args:
        pr_data: Dict with files_changed, additions, deletions, has_tests, security_issues

    Returns:
        "HIGH", "MEDIUM", or "LOW"
    """
    score = 100

    # File complexity penalty
    if pr_data.get("files_changed", 0) > 10:
        score -= 20
    elif pr_data.get("files_changed", 0) > 5:
        score -= 10

    # Lines changed penalty
    total_lines = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
    if total_lines > 500:
        score -= 20
    elif total_lines > 200:
        score -= 10

    # No tests penalty
    if not pr_data.get("has_tests", True):
        score -= 30

    # Security issues penalty
    security_issues = pr_data.get("security_issues", [])
    for issue in security_issues:
        if "critical" in issue.lower():
            score -= 40
        elif "warning" in issue.lower():
            score -= 10

    # Map score to confidence level
    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"


def determine_verdict(review_data: Dict) -> str:
    """
    Determine review verdict based on findings.

    Args:
        review_data: Dict with security_issues, code_quality_issues, confidence

    Returns:
        "APPROVE", "COMMENT", or "REQUEST_CHANGES"
    """
    security_issues = review_data.get("security_issues", [])
    code_quality_issues = review_data.get("code_quality_issues", [])

    # Critical security issues = REQUEST_CHANGES
    for issue in security_issues:
        if any(word in issue.upper() for word in ["CRITICAL", "EXPOSED", "VULNERABILITY"]):
            return "REQUEST_CHANGES"

    # No issues = APPROVE
    if not security_issues and not code_quality_issues:
        return "APPROVE"

    # Minor issues = COMMENT
    return "COMMENT"


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def format_review(review_content: str, metadata: Dict, confidence: str,
                 verdict: str, tokens_used: int = 0, cost: float = 0.0) -> str:
    """
    Format review with header and footer.

    Args:
        review_content: Review text from Claude
        metadata: PR metadata
        confidence: Confidence score (HIGH/MEDIUM/LOW)
        verdict: Review verdict (APPROVE/COMMENT/REQUEST_CHANGES)
        tokens_used: Total tokens used
        cost: Estimated cost in USD

    Returns:
        Formatted review markdown
    """
    header = f"""## 🤖 PR Review by Claude

**PR:** #{metadata['number']} - {metadata['title']}
**Author:** @{metadata['author']}
**Files Changed:** {metadata['files_changed']} (+{metadata['additions']} -{metadata['deletions']})
**Complexity:** {"High" if metadata['files_changed'] > 10 else "Medium" if metadata['files_changed'] > 5 else "Low"}

---

"""

    footer = f"""
---

### 🎯 Confidence Score: {confidence}
**Reasoning:** Based on PR size ({metadata['files_changed']} files, {metadata['additions'] + metadata['deletions']} lines) and complexity analysis.

### ✅ Recommendation: {verdict}
{"Looks good! Ready to merge." if verdict == "APPROVE" else "Please address the issues noted above." if verdict == "REQUEST_CHANGES" else "Consider the suggestions above."}

---

*Reviewed by Claude {CLAUDE_MODEL} | Tokens: {tokens_used:,} | Cost: ${cost:.3f}*
*Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
"""

    return header + review_content + footer


def post_pr_comment(owner: str, repo: str, pr_number: int, comment: str, token: str):
    """
    Post review as PR comment.

    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        comment: Comment text
        token: GitHub token
    """
    endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
    url = f"{GITHUB_API_BASE}{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "Claude-PR-Review-Agent"
    }

    data = json.dumps({"body": comment}).encode('utf-8')

    req = request.Request(url, data=data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Comment posted: {result['html_url']}")
    except Exception as e:
        print(f"❌ Failed to post comment: {str(e)}", file=sys.stderr)
        raise


def generate_review(diff: str, metadata: Dict, claude_api_key: str) -> Tuple[str, Dict]:
    """
    Generate complete PR review.

    Args:
        diff: PR diff text
        metadata: PR metadata
        claude_api_key: Anthropic API key

    Returns:
        Tuple of (formatted_review, stats_dict)
    """
    # Build prompt and call Claude
    prompt = build_review_prompt(diff, metadata)
    review_text, input_tokens, output_tokens = call_claude_api(prompt, claude_api_key)

    # Calculate cost
    total_tokens = input_tokens + output_tokens
    cost = (input_tokens / 1_000_000 * COST_INPUT_PER_1M) + \
           (output_tokens / 1_000_000 * COST_OUTPUT_PER_1M)

    # Analyze review for confidence and verdict
    has_tests = "test" in diff.lower()
    security_issues = [line for line in review_text.split('\n') if '⚠️' in line and 'security' in line.lower()]

    pr_data = {
        **metadata,
        "has_tests": has_tests,
        "security_issues": security_issues
    }

    confidence = calculate_confidence(pr_data)
    verdict = determine_verdict({
        "security_issues": security_issues,
        "code_quality_issues": [],
        "confidence": confidence
    })

    # Format final review
    formatted = format_review(
        review_text, metadata, confidence, verdict,
        total_tokens, cost
    )

    stats = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost": cost,
        "confidence": confidence,
        "verdict": verdict
    }

    return formatted, stats


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude PR Review Agent - AI-powered code reviews",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pr https://github.com/owner/repo/pull/123
  %(prog)s --pr URL --output review.md
  %(prog)s --pr URL --post
        """
    )

    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL to review"
    )
    parser.add_argument(
        "--output",
        help="Save review to file instead of stdout"
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post review as PR comment (requires GITHUB_TOKEN)"
    )
    parser.add_argument(
        "--show-cost",
        action="store_true",
        help="Show detailed cost breakdown"
    )

    args = parser.parse_args()

    # Get API keys from environment
    github_token = os.environ.get("GITHUB_TOKEN", "")
    claude_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not github_token:
        print("❌ Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not claude_api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        # Parse PR URL
        print(f"🔍 Analyzing PR: {args.pr}")
        owner, repo, pr_number = parse_pr_url(args.pr)

        # Fetch PR data
        print(f"📥 Fetching PR #{pr_number} from {owner}/{repo}...")
        metadata = fetch_pr_metadata(owner, repo, pr_number, github_token)
        diff = fetch_pr_diff(owner, repo, pr_number, github_token)

        # Generate review
        print("🤖 Generating review with Claude...")
        review, stats = generate_review(diff, metadata, claude_api_key)

        # Output review
        if args.output:
            with open(args.output, 'w') as f:
                f.write(review)
            print(f"✅ Review saved to {args.output}")
        else:
            print("\n" + "="*80 + "\n")
            print(review)
            print("\n" + "="*80 + "\n")

        # Show cost breakdown if requested
        if args.show_cost:
            print(f"\n💰 Cost Breakdown:")
            print(f"  Input tokens:  {stats['input_tokens']:,}")
            print(f"  Output tokens: {stats['output_tokens']:,}")
            print(f"  Total tokens:  {stats['total_tokens']:,}")
            print(f"  Estimated cost: ${stats['cost']:.3f}")
            print(f"  Confidence: {stats['confidence']}")
            print(f"  Verdict: {stats['verdict']}")

        # Post as comment if requested
        if args.post:
            print("📤 Posting review as PR comment...")
            post_pr_comment(owner, repo, pr_number, review, github_token)

        print(f"\n✅ Review complete!")

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
