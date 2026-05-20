#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent

A command-line tool that analyzes GitHub PRs and returns structured Markdown reviews.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr 123 --repo owner/repo
    claude-review --local path/to/diff.patch

Installation:
    pip install claude-reviewer
    or
    chmod +x claude-review.py && ./claude-review.py --pr ...
"""

import argparse
import subprocess
import json
import sys
import os
from typing import Optional, Dict, List
from datetime import datetime

# Try to import anthropic for Claude API
try:
    import anthropic
except ImportError:
    print("Warning: anthropic package not installed. Install with: pip install anthropic")
    anthropic = None

class PRReviewer:
    """Analyzes PRs and generates structured review comments."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = "claude-sonnet-4-20250514"
        
    def get_pr_diff(self, pr_url: str) -> str:
        """Fetch PR diff from GitHub."""
        # Parse PR URL
        parts = pr_url.replace("https://github.com/", "").split("/")
        if len(parts) < 4:
            raise ValueError(f"Invalid PR URL: {pr_url}")
        
        owner, repo = parts[0], parts[1]
        pr_number = parts[3].replace("pull/", "")
        
        # Use gh CLI or curl
        try:
            result = subprocess.run(
                ["gh", "api", f"/repos/{owner}/{repo}/pulls/{pr_number}"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                pr_data = json.loads(result.stdout)
                diff_url = pr_data.get("diff_url")
                
                # Fetch the diff
                diff_result = subprocess.run(
                    ["curl", "-s", diff_url],
                    capture_output=True, text=True, timeout=30
                )
                return diff_result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback to direct API call
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        result = subprocess.run(
            ["curl", "-s", api_url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            pr_data = json.loads(result.stdout)
            return self._fetch_diff(pr_data.get("diff_url", ""))
        
        raise RuntimeError(f"Failed to fetch PR data from {pr_url}")
    
    def _fetch_diff(self, diff_url: str) -> str:
        """Fetch diff from URL."""
        result = subprocess.run(
            ["curl", "-s", diff_url],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout
    
    def analyze_diff(self, diff: str) -> Dict:
        """Analyze diff and extract key information."""
        changes = {
            "files_changed": [],
            "additions": 0,
            "deletions": 0,
            "has_new_files": False,
            "has_deleted_files": False,
            "languages": set(),
        }
        
        current_file = None
        for line in diff.split("\n"):
            if line.startswith("diff --git"):
                # Extract file path
                parts = line.split()
                if len(parts) >= 4:
                    new_file = parts[3].replace("b/", "")
                    changes["files_changed"].append(new_file)
                    current_file = new_file
                    
                    # Detect language
                    if new_file.endswith(".py"):
                        changes["languages"].add("Python")
                    elif new_file.endswith(".js") or new_file.endswith(".ts"):
                        changes["languages"].add("JavaScript/TypeScript")
                    elif new_file.endswith(".go"):
                        changes["languages"].add("Go")
                    elif new_file.endswith(".rs"):
                        changes["languages"].add("Rust")
                    elif new_file.endswith(".java"):
                        changes["languages"].add("Java")
                        
            elif line.startswith("+++ /dev/null"):
                changes["has_deleted_files"] = True
            elif line.startswith("--- /dev/null"):
                changes["has_new_files"] = True
            elif line.startswith("+") and not line.startswith("+++"):
                changes["additions"] += 1
            elif line.startswith("-") and not line.startswith("---"):
                changes["deletions"] += 1
        
        changes["languages"] = list(changes["languages"])
        return changes
    
    def generate_review(self, diff: str, pr_metadata: Optional[Dict] = None) -> str:
        """Generate structured Markdown review using Claude API."""
        
        if not self.api_key or not anthropic:
            return self._generate_basic_review(diff)
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        # Analyze diff structure
        changes = self.analyze_diff(diff)
        
        prompt = f"""Analyze this GitHub pull request diff and generate a structured review in Markdown format.

Files changed: {len(changes['files_changed'])}
Languages: {', '.join(changes['languages']) or 'Various'}
Additions: {changes['additions']} lines
Deletions: {changes['deletions']} lines

Diff content:
```
{diff[:15000]}  # Limit to avoid token limits
```

Generate a review with this exact structure:

## Summary
[2-3 sentence summary of what this PR changes and why]

## Risks Identified
[List of potential risks or concerns, each as a bullet point]

## Suggestions for Improvement
[List of actionable suggestions, each as a bullet point]

## Confidence Score
[Low / Medium / High]

Be specific and actionable. Focus on:
- Code quality and patterns
- Potential bugs or edge cases
- Security considerations
- Performance implications
- Test coverage
"""

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
        except Exception as e:
            print(f"Warning: Claude API error: {e}")
            return self._generate_basic_review(diff)
    
    def _generate_basic_review(self, diff: str) -> str:
        """Generate basic review without Claude API."""
        changes = self.analyze_diff(diff)
        
        review = f"""## Summary

This PR modifies {len(changes['files_changed'])} files with {changes['additions']} additions and {changes['deletions']} deletions.
Changes primarily affect {', '.join(changes['languages']) or 'various'} code.

## Risks Identified

- Review changes carefully for potential edge cases
- Check for proper error handling in new code paths
- Verify that deleted code doesn't break existing functionality

## Suggestions for Improvement

- Add or update tests to cover the changes
- Ensure documentation is updated if behavior changes
- Review for code style consistency

## Confidence Score

Medium (Based on structural analysis only)
"""
        return review
    
    def post_comment(self, pr_url: str, review: str) -> bool:
        """Post review as a PR comment."""
        parts = pr_url.replace("https://github.com/", "").split("/")
        owner, repo = parts[0], parts[1]
        pr_number = parts[3].replace("pull/", "")
        
        try:
            result = subprocess.run(
                ["gh", "pr", "comment", pr_number, "--repo", f"{owner}/{repo}",
                 "--body", review],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("Note: gh CLI not available. Comment not posted.")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate structured PR reviews using Claude API"
    )
    parser.add_argument(
        "--pr", "-p",
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--repo", "-r",
        help="Repository in owner/repo format (used with --pr-number)"
    )
    parser.add_argument(
        "--pr-number", "-n",
        type=int,
        help="PR number (used with --repo)"
    )
    parser.add_argument(
        "--local", "-l",
        help="Path to local diff file"
    )
    parser.add_argument(
        "--post", "-P",
        action="store_true",
        help="Post review as a PR comment"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for review Markdown"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    reviewer = PRReviewer(api_key=args.api_key)
    
    # Determine PR URL or diff source
    pr_url = None
    diff = None
    
    if args.pr:
        pr_url = args.pr
    elif args.repo and args.pr_number:
        pr_url = f"https://github.com/{args.repo}/pull/{args.pr_number}"
    elif args.local:
        with open(args.local, 'r') as f:
            diff = f.read()
    else:
        parser.print_help()
        sys.exit(1)
    
    # Fetch diff
    if pr_url:
        print(f"Fetching PR: {pr_url}")
        try:
            diff = reviewer.get_pr_diff(pr_url)
        except Exception as e:
            print(f"Error fetching PR: {e}")
            sys.exit(1)
    
    if not diff:
        print("No diff content available")
        sys.exit(1)
    
    # Generate review
    print("Generating review...")
    review = reviewer.generate_review(diff)
    
    # Output review
    print("\n" + "="*60)
    print(review)
    print("="*60 + "\n")
    
    # Save to file
    if args.output:
        with open(args.output, 'w') as f:
            f.write(review)
        print(f"Review saved to: {args.output}")
    
    # Post as comment
    if args.post and pr_url:
        print("Posting review as PR comment...")
        if reviewer.post_comment(pr_url, review):
            print("✓ Review posted successfully")
        else:
            print("✗ Failed to post review")


if __name__ == "__main__":
    main()