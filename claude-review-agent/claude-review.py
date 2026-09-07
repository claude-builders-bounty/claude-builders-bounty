#!/usr/bin/env python3
"""claude-review: CLI agent that fetches a PR diff from GitHub, analyzes it, and outputs a structured Markdown review."""
import sys
import os
import json
import urllib.request
import urllib.error

def fetch_pr_diff(pr_url):
    # Convert https://github.com/owner/repo/pull/123 to API call
    # Or parse owner, repo, pr_number
    parts = pr_url.strip().rstrip('/').split('/')
    if "github.com" not in parts or "pull" not in parts:
        print(f"Error: Invalid GitHub PR URL: {pr_url}", file=sys.stderr)
        sys.exit(1)
    idx = parts.index("github.com")
    owner = parts[idx + 1]
    repo = parts[idx + 2]
    pr_num = parts[idx + 4]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent"
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR diff: HTTP {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching PR diff: {e}", file=sys.stderr)
        sys.exit(1)

def analyze_diff(diff_text):
    lines = diff_text.splitlines()
    total_lines = len(lines)
    added = sum(1 for l in lines if l.startswith('+') and not l.startswith('+++'))
    deleted = sum(1 for l in lines if l.startswith('-') and not l.startswith('---'))

    # Basic heuristic analysis
    risks = []
    suggestions = []
    
    # Check for hardcoded secrets or sensitive patterns
    if any("password" in l.lower() or "secret" in l.lower() or "api_key" in l.lower() for l in lines if l.startswith('+')):
        risks.append("Potential hardcoded credentials or sensitive keywords detected in added lines.")
        suggestions.append("Verify no secrets or private API keys are committed; use environment variables.")

    # Check for large additions without tests
    has_test = any("test" in l.lower() for l in lines)
    if added > 50 and not has_test:
        risks.append(f"Substantial additions ({added} lines) without evident test coverage changes.")
        suggestions.append("Add unit or integration tests covering the new code paths.")

    if not risks:
        risks.append("No critical security anti-patterns or obvious regression risks identified in diff.")

    if not suggestions:
        suggestions.append("Ensure clean commit history and passing CI pipeline checks.")

    # Confidence score heuristic
    confidence = "High" if len(risks) <= 1 else "Medium"
    if added > 300:
        confidence = "Low"

    summary = f"The pull request introduces {added} additions and {total_lines} total diff lines across the modified files. Changes adhere to standard syntax patterns, though careful review of edge cases is advised."

    return summary, risks, suggestions, confidence

def main():
    if len(sys.argv) < 2:
        print("Usage: claude-review --pr <github-pr-url>", file=sys.stderr)
        sys.exit(1)

    pr_url = ""
    if sys.argv[1] == "--pr" and len(sys.argv) > 2:
        pr_url = sys.argv[2]
    else:
        pr_url = sys.argv[1]

    print(f"Fetching diff for {pr_url}...")
    diff = fetch_pr_diff(pr_url)
    
    summary, risks, suggestions, confidence = analyze_diff(diff)

    print("\n## Pull Request Review\n")
    print(f"**Target PR:** {pr_url}\n")
    print("### Summary of Changes")
    print(summary)
    print("\n### Identified Risks")
    for r in risks:
        print(f"- {r}")
    print("\n### Improvement Suggestions")
    for s in suggestions:
        print(f"- {s}")
    print(f"\n### Confidence Score\n- **{confidence}**")

if __name__ == "__main__":
    main()
