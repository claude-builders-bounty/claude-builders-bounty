#!/usr/bin/env python3
"""Claude Code PR Review Agent - Analyzes GitHub PRs and generates structured reviews."""

import argparse
import os
import sys
from typing import Optional
import anthropic
from github import Github
from github.Auth import Token


class PRReviewAgent:
    """Claude-powered PR review agent."""

    def __init__(self, github_token: Optional[str] = None, anthropic_key: Optional[str] = None):
        """Initialize the PR review agent."""
        self.github_token = github_token or os.getenv("GITHUB_API_KEY")
        self.anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.github_token:
            raise ValueError("GITHUB_API_KEY not set")
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.gh = Github(auth=Token(self.github_token))
        self.client = anthropic.Anthropic(api_key=self.anthropic_key)

    def get_pr_info(self, pr_url: str) -> dict:
        """
        Fetch PR details and diff from GitHub.

        Args:
            pr_url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)

        Returns:
            Dict with PR info and diff
        """
        # Parse URL
        parts = pr_url.replace("https://github.com/", "").split("/pull/")
        if len(parts) != 2:
            raise ValueError(f"Invalid PR URL: {pr_url}")

        repo_name = parts[0]
        pr_num = int(parts[1])

        # Fetch PR
        repo = self.gh.get_repo(repo_name)
        pr = repo.get_pull(pr_num)

        # Get diff
        diff = ""
        for file in pr.get_files():
            diff += f"\n=== {file.filename} ===\n"
            diff += file.patch or "(Binary or no changes)\n"

        return {
            "title": pr.title,
            "description": pr.body or "(No description)",
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "changed_files": len(list(pr.get_files())),
            "additions": pr.additions,
            "deletions": pr.deletions,
            "diff": diff[:8000],  # Limit diff size for analysis
        }

    def analyze_pr(self, pr_url: str) -> str:
        """
        Analyze PR and generate structured review.

        Args:
            pr_url: GitHub PR URL

        Returns:
            Structured Markdown review
        """
        print(f"📋 Fetching PR from {pr_url}...", file=sys.stderr)
        pr_info = self.get_pr_info(pr_url)

        print(f"🔍 Analyzing with Claude...", file=sys.stderr)

        prompt = f"""You are an expert code reviewer. Analyze this GitHub PR and provide a structured review.

## PR Details
**Title:** {pr_info['title']}
**Author:** {pr_info['author']}
**Changes:** {pr_info['additions']} additions, {pr_info['deletions']} deletions across {pr_info['changed_files']} files

**Description:**
{pr_info['description']}

## Code Changes
```diff
{pr_info['diff']}
```

## Your Task
Provide a **structured Markdown review** with EXACTLY these sections:

### 📝 Summary
2-3 sentences summarizing what this PR does and its impact.

### ⚠️ Identified Risks
- List specific risks or concerns
- Include code quality issues, potential bugs, or edge cases
- Empty list if no risks found

### 💡 Improvement Suggestions
- List actionable suggestions for improvement
- Be specific with file names and line references where possible
- Empty list if no suggestions

### 🎯 Confidence Score
State your confidence: **Low** / **Medium** / **High**
Explain why briefly.

---

Be concise, practical, and constructive. Focus on what matters: correctness, performance, security, and maintainability."""

        response = self.client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def run(self, pr_url: str) -> None:
        """Run the PR review and print result."""
        review = self.analyze_pr(pr_url)
        print(review)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent",
        epilog="Example: claude-review --pr https://github.com/owner/repo/pull/123",
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)",
    )

    args = parser.parse_args()

    try:
        agent = PRReviewAgent()
        agent.run(args.pr)
    except KeyboardInterrupt:
        print("\n❌ Interrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()