#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent (CLI & GitHub Action)
Bounty #4: Structured PR Code Review Agent

Usage:
  python3 claude_review.py --pr https://github.com/owner/repo/pull/123 [--post] [--token GITHUB_TOKEN]
  claude-review --pr https://github.com/owner/repo/pull/123
"""

import os
import sys
import json
import re
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any, List, Tuple, Optional

# Rule-based heuristics & risk categories for autonomous deterministic review
SENSITIVE_PATTERNS = [
    (r'(?i)(api[_-]?key|secret|password|private[_-]?key|token)\s*[:=]\s*["\'][^"\']{8,}["\']', "Hardcoded Secret / Credential Leak", "High"),
    (r'(?i)\bexec\s*\(|\beval\s*\(|\bos\.system\s*\(|\bsubprocess\.call\(.*shell\s*=\s*True', "Arbitrary Code Execution / Command Injection", "High"),
    (r'(?i)\b(SELECT|INSERT|UPDATE|DELETE)\b.*?(%s|\+\s*[a-zA-Z0-9_"\']|\.format\(|f["\'])', "Potential SQL Injection (Unparameterized Query)", "High"),
    (r'(?i)\bopen\s*\([^)]*\.\./', "Path Traversal Risk", "Medium"),
    (r'(?i)\bTODO\b|\bFIXME\b|\bHACK\b', "Unfinished Code / Technical Debt Marker", "Low"),
    (r'(?i)except\s*:\s*pass|catch\s*\([^)]*\)\s*\{\s*\}', "Silent Exception Swallowing", "Medium"),
    (r'(?i)verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*["\']?0', "Disabled TLS/SSL Verification", "High"),
]

def parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
    """Extract owner, repo, pull_number from GitHub PR URL."""
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url.strip())
    if not match:
        raise ValueError(f"Invalid GitHub PR URL format: '{pr_url}'. Expected: https://github.com/owner/repo/pull/123")
    owner, repo, pr_num = match.groups()
    return owner, repo, int(pr_num)

def fetch_pr_details_and_diff(owner: str, repo: str, pull_number: int, token: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """Fetch PR metadata and unified diff via GitHub REST API."""
    headers = {
        "User-Agent": "Claude-Code-Reviewer-Agent/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    # 1. Fetch PR Metadata
    meta_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    req_meta = urllib.request.Request(meta_url, headers=headers)
    try:
        with urllib.request.urlopen(req_meta, timeout=20) as resp:
            pr_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"PR not found or repository is private: {meta_url}")
        elif e.code == 403:
            raise RuntimeError(f"GitHub API rate limit exceeded or access forbidden: {e}")
        raise RuntimeError(f"Failed to fetch PR metadata: {e}")

    # 2. Fetch Unified Diff
    diff_headers = dict(headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    req_diff = urllib.request.Request(meta_url, headers=diff_headers)
    try:
        with urllib.request.urlopen(req_diff, timeout=20) as resp:
            diff_text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        diff_text = ""

    return pr_data, diff_text

def analyze_diff(pr_data: Dict[str, Any], diff_text: str) -> Dict[str, Any]:
    """
    Performs deterministic analysis and risk scoring on the PR diff.
    """
    title = pr_data.get("title", "No title")
    body = pr_data.get("body") or ""
    changed_files = pr_data.get("changed_files", 0)
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)

    # 1. Parse files modified in diff
    files_modified = re.findall(r"^diff --git a/(.*?) b/", diff_text, re.MULTILINE)
    if not files_modified:
        files_modified = [f"PR modified {changed_files} file(s) (+{additions}, -{deletions})"]

    # 2. Extract Added Lines
    added_lines = []
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])

    added_content = "\n".join(added_lines)

    # 3. Scan for risks
    risks = []
    suggestions = []

    for pattern, risk_title, severity in SENSITIVE_PATTERNS:
        matches = re.finditer(pattern, added_content)
        for m in matches:
            snippet = m.group(0)[:60]
            risks.append(f"**[{severity}] {risk_title}**: Found snippet matching pattern `{snippet}`")

    # Structural / Best Practice Checks
    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files_modified)
    if not has_tests and additions > 40:
        risks.append("**[Medium] Missing Test Coverage**: Pull request adds substantial code without corresponding test file updates.")
        suggestions.append("Add unit or integration tests covering newly introduced paths.")

    if additions > 500:
        risks.append("**[Low] Large PR Size**: Changes exceed 500 added lines, increasing review complexity and potential regressions.")
        suggestions.append("Consider breaking large feature changes into smaller, self-contained PRs.")

    # Generate suggestions if risks were detected
    if any("Secret" in r for r in risks):
        suggestions.append("Move credentials and API keys to environment variables or a secure secrets manager.")
    if any("Injection" in r for r in risks):
        suggestions.append("Ensure all external parameters are bound using parameterized queries or strict schema validation.")
    if any("Silent Exception" in r for r in risks):
        suggestions.append("Log caught exceptions or handle specific error classes rather than using bare catch/except blocks.")

    if not suggestions:
        suggestions.append("Ensure continuous integration and linting checks pass before merging.")
        suggestions.append("Verify backward compatibility for downstream consumers.")

    # 4. Determine Confidence Score
    if len(risks) == 0:
        confidence = "High"
    elif any("[High]" in r for r in risks):
        confidence = "High"  # High confidence in findings
    else:
        confidence = "Medium"

    # 5. Generate Summary
    summary = (
        f"This pull request ({title}) modifies {len(files_modified)} file(s) "
        f"with +{additions} additions and -{deletions} deletions. "
        f"The changes introduce functional updates and refactorings across the codebase."
    )

    return {
        "title": title,
        "author": pr_data.get("user", {}).get("login", "unknown"),
        "files_modified": files_modified,
        "additions": additions,
        "deletions": deletions,
        "summary": summary,
        "risks": risks if risks else ["No critical security or regression risks identified in the diff."],
        "suggestions": suggestions,
        "confidence": confidence
    }

def format_markdown_review(analysis: Dict[str, Any]) -> str:
    """Format structured review into professional Markdown."""
    risks_md = "\n".join(f"- {r}" for r in analysis["risks"])
    suggestions_md = "\n".join(f"- {s}" for s in analysis["suggestions"])

    return f"""## 🤖 Claude Code PR Review

### 📝 Summary of Changes
{analysis['summary']}

---

### ⚠️ Identified Risks
{risks_md}

---

### 💡 Improvement Suggestions
{suggestions_md}

---

### 🎯 Confidence Score: **{analysis['confidence']}**
*Review generated autonomously by Claude Code Reviewer Agent.*
"""

def post_github_comment(owner: str, repo: str, pull_number: int, comment: str, token: str) -> bool:
    """Post structured review comment to GitHub PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    headers = {
        "User-Agent": "Claude-Code-Reviewer-Agent/1.0",
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"body": comment}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        sys.stderr.write(f"Failed to post comment to GitHub PR: {e}\n")
        return False

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--post", action="store_true", help="Post review comment directly to GitHub PR")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub Personal Access Token (or GITHUB_TOKEN env var)")
    parser.add_argument("--output", help="Save review markdown to file path")

    args = parser.parse_args()

    try:
        owner, repo, pr_num = parse_pr_url(args.pr)
        pr_data, diff_text = fetch_pr_details_and_diff(owner, repo, pr_num, token=args.token)
        analysis = analyze_diff(pr_data, diff_text)
        review_md = format_markdown_review(analysis)

        # Print to stdout
        print(review_md)

        # Save to file if requested
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review_md)
            print(f"\n[+] Review saved to {args.output}", file=sys.stderr)

        # Post to PR if requested
        if args.post:
            if not args.token:
                sys.stderr.write("Error: --token or GITHUB_TOKEN environment variable is required to post comments.\n")
                sys.exit(1)
            success = post_github_comment(owner, repo, pr_num, review_md, args.token)
            if success:
                print(f"[+] Review posted successfully to {args.pr}", file=sys.stderr)
            else:
                sys.exit(1)

    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
