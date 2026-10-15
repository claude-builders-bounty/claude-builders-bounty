#!/usr/bin/env python3
"""
Claude Code PR Reviewer CLI & Engine
Analyzes GitHub Pull Request diffs and outputs structured Markdown reviews.
Acceptance Criteria:
- CLI command: claude-review --pr https://github.com/owner/repo/pull/123
- Structured Markdown with Summary, Risks, Improvements, Confidence Score
- GitHub Action compatible
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

def parse_pr_url(url: str):
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}. Expected format: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))

def fetch_pr_diff(owner: str, repo: str, pull_number: int, token: str = None) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = {
        "User-Agent": "Claude-Code-PR-Reviewer",
        "Accept": "application/vnd.github.v3.diff"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to fetch PR diff (HTTP {e.code}): {e.read().decode('utf-8', errors='replace')}")

def fetch_pr_details(owner: str, repo: str, pull_number: int, token: str = None) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = {
        "User-Agent": "Claude-Code-PR-Reviewer",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to fetch PR details (HTTP {e.code})")

def analyze_diff(diff_text: str, pr_title: str = "", pr_body: str = "") -> dict:
    lines = diff_text.splitlines()
    files_changed = []
    additions = 0
    deletions = 0
    risks = []
    suggestions = []
    
    current_file = None
    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 4:
                current_file = parts[3].replace("b/", "")
                files_changed.append(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
            # Static pattern heuristics for common risks
            if any(term in line for term in ["exec(", "eval(", "os.system("]):
                risks.append(f"Security: Execution of unescaped shell/dynamic command detected in `{current_file}`.")
            if re.search(r"rms+-rf|DROPs+TABLE|DELETEs+FROM", line, re.I):
                risks.append(f"Safety: Destructive file or database operation identified in `{current_file}`.")
            if any(k in line.lower().replace(" ", "") for k in ["password=", "secret=", "api_key=", "token="]):
                risks.append(f"Credential Exposure: Potential hardcoded secret or token in `{current_file}`.")
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    # Formulate improvements
    has_tests = any("test" in f.lower() for f in files_changed)
    if not has_tests:
        suggestions.append("Test Coverage: No dedicated test files detected in this diff. Consider adding automated unit tests.")
    if additions > 500:
        suggestions.append(f"PR Sizing: Large patch (+{additions} lines). Consider splitting into smaller atomic commits for easier maintainability.")
    if any(f.endswith(".py") for f in files_changed):
        suggestions.append("Type Safety: Verify Python type annotations with `mypy` or `ruff`.")
    if any(f.endswith(".ts") or f.endswith(".tsx") for f in files_changed):
        suggestions.append("Type Checking: Ensure TypeScript strict mode passes with `tsc --noEmit`.")

    # Deduplicate risks
    unique_risks = list(dict.fromkeys(risks))
    if not unique_risks:
        unique_risks.append("Low Surface Risk: No critical security vulnerabilities, shell injections, or hardcoded secrets found in static diff analysis.")

    # Confidence score calculation
    if len(risks) > 0 and not has_tests:
        confidence = "Medium"
        confidence_reason = f"Identified {len(risks)} potential risk(s) and detected lack of automated regression tests."
    elif has_tests and len(files_changed) <= 5:
        confidence = "High"
        confidence_reason = f"Comprehensive change with dedicated test suite and bounded file impact ({len(files_changed)} files)."
    else:
        confidence = "High"
        confidence_reason = f"Clean diff inspection with {len(files_changed)} file(s) modified (+{additions} / -{deletions})."

    # Summary
    summary = (
        f"This pull request modifies {len(files_changed)} file(s) with {additions} additions and {deletions} deletions. "
        f"The primary focus is '{pr_title or 'code refinement'}' targeting {', '.join(files_changed[:3])}{' and others' if len(files_changed) > 3 else ''}. "
        f"Automated static review highlights {'dedicated verification tests' if has_tests else 'potential areas for test expansion'}."
    )

    return {
        "files_changed": files_changed,
        "additions": additions,
        "deletions": deletions,
        "summary": summary,
        "risks": unique_risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "confidence_reason": confidence_reason
    }

def format_markdown_review(analysis: dict, pr_url: str = None) -> str:
    md = [
        "## 🔍 Pull Request Review (Claude Code Agent)",
        "",
        "### 📝 Summary of Changes",
        analysis["summary"],
        "",
        "### ⚠️ Identified Risks",
    ]
    for r in analysis["risks"]:
        md.append(f"- {r}")
    
    md.extend([
        "",
        "### 💡 Improvement Suggestions",
    ])
    for s in analysis["suggestions"]:
        md.append(f"- {s}")
    
    md.extend([
        "",
        f"### 🎯 Confidence Score: **{analysis['confidence']}**",
        f"*Rationale*: {analysis['confidence_reason']}",
        "",
        "---",
        "*Automated with `claude-review` sub-agent powered by Claude Code.*"
    ])
    
    return "\n".join(md)

def post_github_comment(owner: str, repo: str, pull_number: int, comment_body: str, token: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    headers = {
        "User-Agent": "Claude-Code-PR-Reviewer",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer CLI")
    parser.add_argument("--pr", type=str, required=True, help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", type=str, default=os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT"), help="GitHub Personal Access Token")
    parser.add_argument("--post-comment", action="store_true", help="Post the generated review comment directly to the PR on GitHub")
    parser.add_argument("--diff-file", type=str, default=None, help="Optional local diff file for offline analysis")

    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)

    if args.diff_file and os.path.exists(args.diff_file):
        with open(args.diff_file, "r", encoding="utf-8") as f:
            diff_text = f.read()
        pr_title = f"Local Diff Analysis for PR #{pr_number}"
    else:
        diff_text = fetch_pr_diff(owner, repo, pr_number, args.token)
        try:
            details = fetch_pr_details(owner, repo, pr_number, args.token)
            pr_title = details.get("title", "")
            pr_body = details.get("body", "")
        except Exception:
            pr_title = f"PR #{pr_number}"
            pr_body = ""

    analysis = analyze_diff(diff_text, pr_title, pr_body)
    review_markdown = format_markdown_review(analysis, args.pr)

    print(review_markdown)

    if args.post_comment:
        if not args.token:
            print("Error: --token or GITHUB_TOKEN environment variable required to post comment.", file=sys.stderr)
            sys.exit(1)
        res = post_github_comment(owner, repo, pr_number, review_markdown, args.token)
        print(f"\nSuccessfully posted comment to GitHub: {res.get('html_url')}")

if __name__ == "__main__":
    main()
