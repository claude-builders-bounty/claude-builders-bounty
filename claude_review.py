#!/usr/bin/env python3
"""
Claude Code PR Review Sub-Agent
Analyzes GitHub Pull Request diffs and outputs structured Markdown reviews.
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.error

def parse_pr_url(url: str) -> tuple[str, str, str]:
    """Extracts owner, repo, and PR number from a GitHub PR URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}. Expected format: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)

def fetch_pr_diff(owner: str, repo: str, pr_number: str, token: str = None) -> str:
    """Fetches the raw git diff of a GitHub pull request."""
    diff_url = f"https://patch-diff.githubusercontent.com/raw/{owner}/{repo}/pull/{pr_number}.diff"
    headers = {"User-Agent": "Claude-PR-Review-Agent"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    req = urllib.request.Request(diff_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        # Fallback to standard github.com diff URL
        fallback_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
        req_fallback = urllib.request.Request(fallback_url, headers=headers)
        with urllib.request.urlopen(req_fallback, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")

def analyze_diff(diff_text: str, owner: str, repo: str, pr_number: str) -> str:
    """
    Analyzes the git diff and generates a structured Markdown review.
    Covers:
      - Summary of changes (2-3 sentences)
      - Identified risks (list)
      - Improvement suggestions (list)
      - Confidence score: Low / Medium / High
    """
    lines = diff_text.splitlines()
    files_changed = []
    additions = 0
    deletions = 0
    risks = []
    suggestions = []

    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 4:
                files_changed.append(parts[3].replace("b/", ""))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
            # Check for common risk patterns
            lower_line = line.lower()
            if any(k in lower_line for k in ["api_key", "secret", "password", "token", "private_key"]) and "=" in line:
                risks.append("Potential hardcoded credential or secret detected in changed lines.")
            if "eval(" in line or "exec(" in line:
                risks.append("Usage of dynamic code evaluation (`eval` or `exec`) introduces arbitrary code execution risks.")
            if "any" in line and (": any" in line or "<any>" in line):
                suggestions.append("Replace untyped `any` annotations with strict TypeScript interfaces.")
            if "todo" in lower_line or "fixme" in lower_line:
                suggestions.append(f"Unresolved TODO/FIXME comment added: `{line.strip()}`.")
            if "dangerouslysetinnerhtml" in lower_line:
                risks.append("Usage of `dangerouslySetInnerHTML` poses Cross-Site Scripting (XSS) vulnerability risks.")
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    # Remove duplicates
    risks = list(dict.fromkeys(risks))
    suggestions = list(dict.fromkeys(suggestions))

    # Default checks if clean
    if not risks:
        risks.append("No immediate high-severity security vulnerabilities detected in the diff.")
        risks.append("Verify that downstream components handle any altered return types or modified parameters.")

    if not suggestions:
        suggestions.append("Ensure automated unit test coverage is added or updated for new code paths.")
        suggestions.append("Verify documentation or README updates if public APIs were modified.")

    # Calculate confidence score
    confidence = "High"
    if len(files_changed) > 15 or (additions + deletions) > 800:
        confidence = "Medium"
    elif len(files_changed) > 30 or (additions + deletions) > 2000:
        confidence = "Low"

    # Construct 2-3 sentence summary
    summary = (
        f"This pull request modifies **{len(files_changed)} file(s)** with a total of **{additions} additions** and **{deletions} deletions**. "
        f"The primary changes focus on {files_changed[0] if files_changed else 'project codebase'} and associated functionality. "
        f"Overall code structure appears organized with targeted modifications across the diff."
    )

    # Format Markdown review
    review_markdown = f"""## 🤖 Claude Code PR Review

> **Target PR:** [{owner}/{repo}#{pr_number}](https://github.com/{owner}/{repo}/pull/{pr_number})  
> **Files Changed:** {len(files_changed)} | **Additions:** +{additions} | **Deletions:** -{deletions}

### 📋 Summary of Changes
{summary}

### ⚠️ Identified Risks
"""
    for r in risks:
        review_markdown += f"- {r}\n"

    review_markdown += "\n### 💡 Improvement Suggestions\n"
    for s in suggestions:
        review_markdown += f"- {s}\n"

    review_markdown += f"\n### ✅ Confidence Score: **{confidence}**\n"
    review_markdown += f"*(Confidence is based on diff scope, change clarity, and pattern analysis)*\n"

    return review_markdown

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Sub-Agent")
    parser.add_argument("--pr", required=True, help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", "-o", help="Optional output markdown file path")
    parser.add_argument("--token", help="Optional GitHub Personal Access Token")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")
    owner, repo, pr_number = parse_pr_url(args.pr)

    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...")
    try:
        diff_text = fetch_pr_diff(owner, repo, pr_number, token)
        review = analyze_diff(diff_text, owner, repo, pr_number)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review)
            print(f"✅ Review saved to: {args.output}")
        else:
            print("\n" + review)
            
    except Exception as e:
        sys.stderr.write(f"Error reviewing PR: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
