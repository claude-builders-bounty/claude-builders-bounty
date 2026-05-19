#!/usr/bin/env python3
"""claude-review - AI-powered PR review agent.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff /path/to/diff.txt

Outputs structured Markdown review.
"""
import argparse
import subprocess
import sys
import json
import os
import tempfile
from typing import Optional

def fetch_pr_diff(pr_url: str) -> str:
    """Fetch PR diff from GitHub API."""
    # Parse owner/repo/pull/number
    parts = pr_url.rstrip('/').split('/')
    try:
        pull_idx = parts.index('pull') if 'pull' in parts else parts.index('pulls')
        pr_number = parts[pull_idx + 1]
        repo = '/'.join(parts[-4:-2])
    except (ValueError, IndexError):
        raise ValueError(f"Invalid PR URL: {pr_url}. Expected: https://github.com/owner/repo/pull/123")

    import urllib.request
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0"
    })
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req, timeout=30) as resp:
        diff = resp.read().decode('utf-8')
    return diff

def read_diff_file(path: str) -> str:
    """Read diff from a local file."""
    with open(path, 'r') as f:
        return f.read()

def analyze_with_llm(diff: str) -> str:
    """Send diff to local LLM (Claude CLI or fallback to rules-based analysis)."""
    if len(diff) > 50000:
        diff = diff[:50000] + "\n... [truncated]"

    # Try Claude CLI first
    try:
        result = subprocess.run(
            ["claude", "-p", f"Review this PR diff and output a structured Markdown review with: Summary of changes (2-3 sentences), Identified risks (list), Improvement suggestions (list), Confidence score (Low/Medium/High).\n\nDIFF:\n```diff\n{diff}\n```"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: rules-based analysis
    return rules_based_review(diff)

def rules_based_review(diff: str) -> str:
    """Generate a structured review using rule-based analysis."""
    lines = diff.split('\n')
    added = [l for l in lines if l.startswith('+') and not l.startswith('+++')]
    removed = [l for l in lines if l.startswith('-') and not l.startswith('---')]
    changed_files = [l for l in lines if l.startswith('diff --git')]

    # Find file paths
    files = []
    for l in changed_files:
        parts = l.split()
        if len(parts) >= 4:
            fname = parts[3].replace('b/', '', 1)
            files.append(fname)

    # Simple risk detection
    risks = []
    for line in added:
        ll = line.strip().lower()
        if 'password' in ll or 'secret' in ll or 'token' in ll or 'apikey' in ll:
            risks.append("🚨 Possible secret/key leak detected")
        if 'eval(' in ll or 'exec(' in ll:
            risks.append("⚠️ Use of eval()/exec() - potential security risk")
        if 'print(' in ll and not ll.lstrip('+').startswith('#'):
            risks.append("📝 Debug print statement left in code")
        if 'todo' in ll or 'fixme' in ll:
            risks.append("📝 TODO/FIXME comment found")

    if not risks and len(added) < 5:
        risks.append("✅ No obvious risks detected in this small change")

    # Suggestions
    suggestions = []
    if len(diff) > 10000:
        suggestions.append("Consider splitting this large diff into smaller PRs for easier review")
    if not risks:
        suggestions.append("Code looks clean - consider adding tests if not already present")

    # Summary
    summary_parts = []
    summary_parts.append(f"This PR modifies {len(files)} file(s): {', '.join(files[:5])}")
    if len(files) > 5:
        summary_parts[-1] += f" and {len(files)-5} more"
    summary_parts.append(f"Total changes: +{len(added)} lines added, -{len(removed)} lines removed")
    summary = '\n'.join(summary_parts)

    # Confidence
    if risks or len(added) > 50:
        confidence = "Medium"
    elif len(added) < 10:
        confidence = "High"
    else:
        confidence = "Medium"

    review = f"""## 🔍 PR Review Report

### Summary
{summary}

### Identified Risks
"""
    for r in (risks or ["✅ No risks identified"]):
        review += f"- {r}\n"

    review += f"""
### Improvement Suggestions
"""
    for s in (suggestions or ["No suggestions at this time."]):
        review += f"- {s}\n"

    review += f"""
### Confidence Score
**{confidence}**
"""
    return review.strip()

def main():
    parser = argparse.ArgumentParser(description="AI-powered PR review agent")
    parser.add_argument("--pr", help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff", help="Path to local diff file")
    args = parser.parse_args()

    if not args.pr and not args.diff:
        parser.print_help()
        sys.exit(1)

    try:
        if args.pr:
            print(f"🔄 Fetching diff from {args.pr}...", file=sys.stderr)
            diff = fetch_pr_diff(args.pr)
        else:
            diff = read_diff_file(args.diff)

        print(f"🔄 Analyzing {len(diff)} bytes of diff...", file=sys.stderr)
        review = analyze_with_llm(diff)
        print(review)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
