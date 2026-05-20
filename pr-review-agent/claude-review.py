#!/usr/bin/env python3
"""
🔍 CLAUDE PR REVIEW AGENT
Analyzes GitHub PRs and generates structured review comments

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr-number 123 --repo owner/repo

Requirements:
    - GITHUB_TOKEN environment variable
    - ANTHROPIC_API_KEY environment variable
"""

import argparse
import os
import sys
import re
from typing import Dict, Optional
import requests
import anthropic


class PRReviewAgent:
    """Claude-powered PR review agent"""

    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        self.client = anthropic.Anthropic(api_key=self.anthropic_key)
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def parse_pr_url(self, url: str) -> tuple:
        """Parse GitHub PR URL into owner, repo, pr_number"""
        pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
        match = re.search(pattern, url)

        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {url}")

        return match.group(1), match.group(2), int(match.group(3))

    def fetch_pr_diff(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Fetch PR diff and metadata from GitHub"""

        # Get PR info
        pr_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
        pr_response = requests.get(pr_url, headers=self.headers)
        pr_response.raise_for_status()
        pr_data = pr_response.json()

        # Get diff
        diff_headers = self.headers.copy()
        diff_headers['Accept'] = 'application/vnd.github.v3.diff'
        diff_response = requests.get(pr_url, headers=diff_headers)
        diff_response.raise_for_status()

        return {
            'title': pr_data['title'],
            'description': pr_data['body'] or '',
            'author': pr_data['user']['login'],
            'files_changed': pr_data['changed_files'],
            'additions': pr_data['additions'],
            'deletions': pr_data['deletions'],
            'diff': diff_response.text
        }

    def analyze_pr(self, pr_data: Dict) -> str:
        """Analyze PR using Claude and generate structured review"""

        prompt = f"""You are a senior staff engineer at a top-tier tech company (Google/Meta/Amazon level). Analyze this GitHub Pull Request with the rigor expected for production-critical code that will serve millions of users.

PR Title: {pr_data['title']}
PR Description: {pr_data['description']}
Author: {pr_data['author']}
Files Changed: {pr_data['files_changed']}
+{pr_data['additions']} -{pr_data['deletions']} lines

Diff:
```diff
{pr_data['diff'][:15000]}
```

Provide an elite-level code review in Markdown format with these sections:

## Summary
(2-3 sentences describing what changes were made, why, and the business/technical impact)

## Critical Issues (Must Fix Before Merge)
- Issue 1: Specific problem with severity and remediation
(Only list genuine blockers: security vulnerabilities, data loss risks, breaking changes)

## Identified Risks
- **[Category] Risk**: Specific description, likelihood, and potential impact
(Categories: Security, Performance, Correctness, Scalability, Maintainability)

## Improvement Suggestions
- **[Priority: High/Medium/Low]** Suggestion: Detailed explanation with code examples if relevant
(Prioritized, actionable improvements with clear business value)

## Strengths
- What the PR does exceptionally well
(Positive feedback on architecture, testing, documentation, etc.)

## Testing Assessment
- Coverage: Evaluate test quality and completeness
- Edge cases: Identify untested scenarios
- Recommendation: Specific tests to add

## Confidence Score
**Confidence: [Low/Medium/High]**

**Reasoning**: (Detailed explanation considering: code complexity, test coverage, documentation quality, potential production impact, team familiarity with codebase)

**Review Methodology**: I analyzed:
1. Security implications (authentication, authorization, input validation, data handling)
2. Performance characteristics (time complexity, memory usage, database queries, API calls)
3. Correctness (logic, edge cases, error handling, race conditions)
4. Maintainability (code clarity, documentation, architectural consistency)
5. Testing (coverage, quality, missing scenarios)

Be brutally honest about issues but constructive in tone. Think like a senior engineer who cares deeply about production quality and team velocity. Flag anything that could cause a 3am page or customer impact.

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return message.content[0].text

    def review_pr(self, pr_url: Optional[str] = None,
                  owner: Optional[str] = None,
                  repo: Optional[str] = None,
                  pr_number: Optional[int] = None) -> str:
        """Main review function"""

        # Parse input
        if pr_url:
            owner, repo, pr_number = self.parse_pr_url(pr_url)
        elif not (owner and repo and pr_number):
            raise ValueError("Either --pr URL or --repo + --pr-number required")

        print(f"🔍 Analyzing PR #{pr_number} in {owner}/{repo}...")

        # Fetch PR data
        pr_data = self.fetch_pr_diff(owner, repo, pr_number)
        print(f"✅ Fetched PR: {pr_data['title']}")
        print(f"   Files: {pr_data['files_changed']}, +{pr_data['additions']} -{pr_data['deletions']}")

        # Analyze with Claude
        print(f"🤖 Analyzing with Claude Sonnet 4...")
        review = self.analyze_pr(pr_data)

        return review


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Claude PR Review Agent - Analyze GitHub PRs with AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --repo owner/repo --pr-number 123

Environment Variables:
  GITHUB_TOKEN       GitHub personal access token
  ANTHROPIC_API_KEY  Anthropic API key for Claude
"""
    )

    parser.add_argument('--pr', type=str, help='GitHub PR URL')
    parser.add_argument('--repo', type=str, help='Repository (owner/repo)')
    parser.add_argument('--pr-number', type=int, help='PR number')
    parser.add_argument('--output', type=str, help='Output file (default: stdout)')
    parser.add_argument('--format', type=str, choices=['markdown', 'json'], default='markdown',
                       help='Output format: markdown or json')
    parser.add_argument('--focus', type=str, choices=['security', 'performance', 'all'], default='all',
                       help='Review focus area')

    args = parser.parse_args()

    if not args.pr and not (args.repo and args.pr_number):
        parser.print_help()
        sys.exit(1)

    try:
        agent = PRReviewAgent()
        review = agent.review_pr(
            pr_url=args.pr,
            owner=args.repo.split('/')[0] if args.repo else None,
            repo=args.repo.split('/')[1] if args.repo else None,
            pr_number=args.pr_number
        )

        # Output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(review)
            print(f"\n✅ Review saved to: {args.output}")
        else:
            print("\n" + "="*70)
            print("📋 PR REVIEW")
            print("="*70)
            print(review)
            print("="*70)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
