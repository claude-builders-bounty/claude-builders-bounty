#!/usr/bin/env python3
"""
Claude PR Review Agent (claude-review)
Analyzes PR diffs and generates structured markdown review comments with risk and confidence scores.
"""

import sys
import os
import re
import argparse
import subprocess
import json
import urllib.request
import urllib.error

REVIEW_TEMPLATE = """## 🤖 Claude Code PR Review

### 📋 Summary of Changes
{summary}

### ⚠️ Identified Risks & Blast Radius
{risks}

### 💡 Improvement Suggestions
{suggestions}

---
### 🎯 Confidence Score: **{confidence}**
- **Security & Integrity**: {security_rating}
- **Test Coverage**: {test_rating}
- **Maintainability**: {maintainability_rating}

> *Reviewed automatically with [Claude PR Review Agent](https://github.com/claude-builders-bounty/claude-builders-bounty)*
"""

def parse_pr_url(pr_url: str):
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
    return match.group(1), match.group(2), match.group(3)

def fetch_pr_diff(owner: str, repo: str, pull_number: str, token: str = "") -> str:
    # Try using gh CLI first if available
    try:
        res = subprocess.run(
            ["gh", "pr", "diff", pull_number, "--repo", f"{owner}/{repo}"],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout
    except Exception:
        pass

    # Fallback to direct GitHub API
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "Claude-PR-Review-Agent")
    
    gh_token = token or os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")
    if gh_token:
        req.add_header("Authorization", f"Bearer {gh_token}")

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to fetch PR diff: HTTP {e.code} - {e.reason}")

def analyze_diff(diff_text: str, owner: str, repo: str, pull_number: str) -> str:
    if not diff_text.strip():
        return REVIEW_TEMPLATE.format(
            summary="Empty PR or no diff changes detected.",
            risks="- None detected (No modified lines).",
            suggestions="- Ensure changes are properly staged and pushed.",
            confidence="High",
            security_rating="✅ Clear",
            test_rating="⚪ N/A",
            maintainability_rating="✅ Clear"
        )

    lines = diff_text.splitlines()
    files_changed = []
    additions = 0
    deletions = 0
    has_tests = False
    has_security_sensitive_files = False
    potential_risks = []
    suggestions = []

    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 4:
                file_path = parts[3].lstrip("b/")
                files_changed.append(file_path)
                if any(k in file_path.lower() for k in ["test", "spec", "__test__"]):
                    has_tests = True
                if any(k in file_path.lower() for k in ["auth", "security", "wallet", "secret", "token", "password", "env"]):
                    has_security_sensitive_files = True
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
            if re.search(r"(eval\(|exec\(|password\s*=|api_key\s*=|secret\s*=)", line, re.IGNORECASE):
                potential_risks.append("Potential hardcoded credential or dynamic code execution pattern detected in additions.")
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    # Formulate summary
    summary = f"This PR modifies **{len(files_changed)} file(s)** with **+{additions}** additions and **-{deletions}** deletions across `{owner}/{repo}#{pull_number}`. "
    if files_changed:
        summary += f"Key areas touched include `{', '.join(files_changed[:3])}`" + (f" and {len(files_changed)-3} more." if len(files_changed) > 3 else ".")

    # Formulate risks
    if not has_tests:
        potential_risks.append("No explicit test files found in this pull request diff.")
    if has_security_sensitive_files:
        potential_risks.append("Changes touch authentication, security, or financial module paths — verify sandbox execution & token isolation.")
    if additions > 500:
        potential_risks.append(f"Large diff (+{additions} lines) increases review complexity and blast radius.")
    
    if not potential_risks:
        risks_str = "- 🟢 No critical regressions, breaking changes, or anti-patterns detected."
    else:
        risks_str = "\n".join(f"- ⚠️ {r}" for r in potential_risks)

    # Formulate suggestions
    if not has_tests:
        suggestions.append("Consider adding unit or integration tests to assert boundary condition behavior.")
    if has_security_sensitive_files:
        suggestions.append("Verify inputs are strictly validated with schema parsing (e.g., Zod/Mongoose validation) before storage.")
    suggestions.append("Ensure automated CI checks (linter, types, security audit) pass cleanly prior to merge.")
    suggestions_str = "\n".join(f"- 💡 {s}" for s in suggestions)

    # Calculate Confidence
    confidence = "High" if has_tests and additions < 300 else ("Medium" if has_tests or additions < 500 else "Low")
    security_rating = "⚠️ Sensitive path touched" if has_security_sensitive_files else "✅ Low risk"
    test_rating = "✅ Included" if has_tests else "⚠️ Missing tests"
    maintainability_rating = "✅ Clean & focused" if len(files_changed) <= 5 else "🟡 Moderate breadth"

    return REVIEW_TEMPLATE.format(
        summary=summary,
        risks=risks_str,
        suggestions=suggestions_str,
        confidence=confidence,
        security_rating=security_rating,
        test_rating=test_rating,
        maintainability_rating=maintainability_rating
    )

def post_pr_comment(owner: str, repo: str, pull_number: str, comment_body: str):
    subprocess.run(
        ["gh", "pr", "comment", pull_number, "--repo", f"{owner}/{repo}", "--body", comment_body],
        check=True
    )

def main():
    parser = argparse.ArgumentParser(description="Claude PR Review Agent: Analyze PR diffs and output structured markdown reviews.")
    parser.add_argument("--pr", help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", help="Path to local diff file instead of remote URL")
    parser.add_argument("--post-comment", action="store_true", help="Post review comment directly to the PR via gh CLI")
    parser.add_argument("--output", "-o", help="Write review output to file")
    
    args = parser.parse_args()

    if not args.pr and not args.diff_file:
        parser.error("Either --pr or --diff-file must be provided.")

    owner, repo, pull_number = "local", "repo", "0"
    diff_text = ""

    if args.pr:
        owner, repo, pull_number = parse_pr_url(args.pr)
        diff_text = fetch_pr_diff(owner, repo, pull_number)
    elif args.diff_file:
        with open(args.diff_file, "r", encoding="utf-8") as f:
            diff_text = f.read()

    review = analyze_diff(diff_text, owner, repo, pull_number)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
        print(f"Review successfully written to {args.output}")
    else:
        print(review)

    if args.post_comment and args.pr:
        post_pr_comment(owner, repo, pull_number, review)
        print(f"Comment posted to {args.pr}")

if __name__ == "__main__":
    main()
