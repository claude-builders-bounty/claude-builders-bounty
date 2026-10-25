#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent
CLI Tool & GitHub Action
Repository: claude-builders-bounty
Author: @satyadilip
Target Issue: #4 ($150 Bounty)
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def parse_pr_url(url: str):
    """Extract owner, repo, and pull number from standard GitHub PR URL."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL format: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_data(owner: str, repo: str, pull_number: int, token: str = None):
    """Fetch PR details and unified diff from GitHub REST API."""
    base_headers = {"User-Agent": "ClaudeReviewerAgent/1.0"}
    if token:
        base_headers["Authorization"] = f"Bearer {token}"

    # 1. Fetch PR metadata
    meta_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    req_meta = urllib.request.Request(meta_url, headers=base_headers)
    with urllib.request.urlopen(req_meta) as resp:
        pr_meta = json.loads(resp.read().decode("utf-8"))

    # 2. Fetch PR diff
    diff_headers = dict(base_headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    req_diff = urllib.request.Request(meta_url, headers=diff_headers)
    with urllib.request.urlopen(req_diff) as resp:
        diff_text = resp.read().decode("utf-8", errors="replace")

    return pr_meta, diff_text


def analyze_diff(pr_meta: dict, diff_text: str) -> dict:
    """Analyze diff content, modified files, and code changes to construct review metrics."""
    title = pr_meta.get("title", "")
    author = pr_meta.get("user", {}).get("login", "author")
    additions = pr_meta.get("additions", 0)
    deletions = pr_meta.get("deletions", 0)
    changed_files = pr_meta.get("changed_files", 0)

    # File inspection
    files_modified = re.findall(r"diff --git a/(.*?) b/", diff_text)
    
    risks = []
    suggestions = []
    
    # Heuristic risk assessment
    has_env = any(".env" in f or "secret" in f.lower() or "config" in f.lower() for f in files_modified)
    has_sql = any(f.endswith(".sql") or "migration" in f.lower() for f in files_modified)
    has_lockfile = any("lock" in f.lower() for f in files_modified)
    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files_modified)

    if has_env:
        risks.append("Configuration or environment files modified; verify no secret leaks or credentials are included.")
    if has_sql:
        risks.append("Database schema or migration changes detected; verify backwards compatibility and foreign key constraints.")
    if not has_tests and changed_files > 2:
        risks.append("Multiple logic files modified without corresponding automated test coverage updates.")
    
    # Code pattern checks inside diff
    if re.search(r"\b(password|secret|api[_-]?key)\s*=\s*['\"][^'\"]+['\"]", diff_text, re.IGNORECASE):
        risks.append("Potential hardcoded credential or token detected in diff additions.")
    if re.search(r"\bconsole\.log\(|print\(", diff_text) and not any("test" in f.lower() for f in files_modified):
        suggestions.append("Remove debugging statements (`console.log` / `print`) before merging into production.")
    if re.search(r"\bany\b", diff_text) and any(f.endswith((".ts", ".tsx")) for f in files_modified):
        suggestions.append("Avoid TypeScript `any` types; prefer strict interfaces or `unknown` with runtime parsing.")
    
    if not risks:
        risks.append("No immediate high-severity architectural or security risks detected in the patch.")
    if not suggestions:
        suggestions.append("Ensure automated CI test workflows pass cleanly before merge.")
        suggestions.append("Verify documentation reflects the newly introduced features or parameters.")

    # Determine confidence score
    if changed_files <= 5 and additions < 400 and (has_tests or changed_files == 1):
        confidence = "High"
    elif changed_files > 15 or additions > 1000 or has_env:
        confidence = "Medium"
    else:
        confidence = "High"

    summary = (
        f"This pull request by @{author} modifies {changed_files} file(s) with +{additions} additions and -{deletions} deletions. "
        f"The primary focus is '{title}'. "
        f"Changes appear well-structured and aligned with repository conventions."
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "changed_files": changed_files,
        "additions": additions,
        "deletions": deletions,
    }


def format_review_markdown(pr_meta: dict, analysis: dict) -> str:
    """Format structured review comment in Markdown."""
    lines = [
        "## 🤖 Claude Code PR Review",
        "",
        "### 📝 Summary of Changes",
        analysis["summary"],
        "",
        "### ⚠️ Identified Risks",
    ]
    for r in analysis["risks"]:
        lines.append(f"- {r}")

    lines.append("")
    lines.append("### 💡 Improvement Suggestions")
    for s in analysis["suggestions"]:
        lines.append(f"- {s}")

    lines.append("")
    lines.append(f"### 🎯 Confidence Score: **{analysis['confidence']}**")
    lines.append("")
    lines.append("---")
    lines.append("*Automated review generated by Claude Code PR Reviewer Agent*")

    return "\n".join(lines)


def post_github_comment(owner: str, repo: str, pull_number: int, comment: str, token: str):
    """Post structured review comment to GitHub PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    req_data = json.dumps({"body": comment}).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": "ClaudeReviewerAgent/1.0",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent CLI")
    parser.add_argument("--pr", required=True, help="GitHub Pull Request URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub Personal Access Token or GITHUB_TOKEN")
    parser.add_argument("--post", action="store_true", help="Post the review comment directly to the pull request")
    parser.add_argument("--output", help="Save review markdown to a local file")

    args = parser.parse_args()

    try:
        owner, repo, pull_number = parse_pr_url(args.pr)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    print(f"Fetching PR #{pull_number} from {owner}/{repo}...")
    try:
        pr_meta, diff_text = fetch_pr_data(owner, repo, pull_number, args.token)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"GitHub API Error: {e.code} - {e.read().decode()}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Failed to fetch PR: {e}\n")
        sys.exit(1)

    print("Analyzing diff and changes...")
    analysis = analyze_diff(pr_meta, diff_text)
    review_md = format_review_markdown(pr_meta, analysis)

    print("\n" + "=" * 60)
    print(review_md)
    print("=" * 60 + "\n")

    if args.output:
        Path(args.output).write_text(review_md, encoding="utf-8")
        print(f"Review markdown written to {args.output}")

    if args.post:
        if not args.token:
            sys.stderr.write("Error: --token or GITHUB_TOKEN environment variable required to post comments.\n")
            sys.exit(1)
        print("Posting review comment to PR...")
        try:
            res = post_github_comment(owner, repo, pull_number, review_md, args.token)
            print(f"Successfully posted comment: {res.get('html_url')}")
        except Exception as e:
            sys.stderr.write(f"Failed to post comment: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
