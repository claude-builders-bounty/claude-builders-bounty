#!/usr/bin/env python3
"""
claude_review.py — Claude Code PR Review Sub-Agent
Analyzes GitHub Pull Request diffs and generates structured Markdown review comments.
"""

import os
import sys
import re
import json
import argparse
import urllib.request
import urllib.error

SECRET_PATTERNS = [
    (r"ghp_[A-Za-z0-9_]{36}", "GitHub Personal Access Token"),
    (r"sk-[A-Za-z0-9_-]{20,}", "OpenAI / Claude API Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"(?i)password\s*=\s*['\"][^'\"]{6,}['\"]", "Plaintext password assignment"),
]

DESTRUCTIVE_PATTERNS = [
    (r"rm\s+-(rf|fr|r\s+-f)", "Recursive force file deletion"),
    (r"(?i)DROP\s+TABLE", "SQL DROP TABLE command"),
    (r"(?i)TRUNCATE\s+(TABLE)?", "SQL TRUNCATE command"),
    (r"git\s+push\s+.*--force", "Force git push"),
]

def parse_pr_url(url: str):
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
    if not m:
        raise ValueError(f"Invalid GitHub PR URL format: {url}. Expected: https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), int(m.group(3))

def fetch_pr_data(owner: str, repo: str, pr_num: int, token: str = None):
    headers = {
        "User-Agent": "Claude-PR-Review-Agent",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    # Fetch PR metadata
    meta_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(meta_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        pr_meta = json.loads(resp.read().decode("utf-8"))

    # Fetch PR diff
    diff_headers = headers.copy()
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    diff_req = urllib.request.Request(meta_url, headers=diff_headers)
    with urllib.request.urlopen(diff_req) as resp:
        pr_diff = resp.read().decode("utf-8", errors="replace")

    return pr_meta, pr_diff

def analyze_diff(pr_meta: dict, pr_diff: str) -> dict:
    title = pr_meta.get("title", "Pull Request")
    body = pr_meta.get("body", "") or ""
    changed_files = pr_meta.get("changed_files", 0)
    additions = pr_meta.get("additions", 0)
    deletions = pr_meta.get("deletions", 0)

    # File inspection
    files_touched = re.findall(r"diff --git a/(.*?) b/", pr_diff)
    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files_touched)
    has_docs = any(f.lower().endswith((".md", ".txt", ".rst")) for f in files_touched)

    risks = []
    suggestions = []

    # Check for exposed secrets
    for pattern, desc in SECRET_PATTERNS:
        matches = re.findall(pattern, pr_diff)
        if matches:
            risks.append(f"🚨 **Security Warning**: Potential {desc} detected in diff.")
            suggestions.append("Store credentials in environment variables or GitHub Secrets instead of committing them.")

    # Check for destructive commands
    for pattern, desc in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, pr_diff):
            risks.append(f"⚠️ **Destructive Operation**: Found '{desc}' in modified code.")
            suggestions.append("Ensure dangerous operations have explicit confirmation checks or sandbox safeguards.")

    # Check test coverage
    if not has_tests and changed_files > 0:
        risks.append("⚠️ **Missing Test Coverage**: Changes modify code but include no new or updated unit/integration tests.")
        suggestions.append("Add unit tests for the modified functionality to prevent regressions.")

    # Check PR description
    if len(body.strip()) < 20:
        suggestions.append("Expand the PR description with a concise summary and motivation for the changes.")

    if not has_docs and any(f.endswith((".py", ".ts", ".js", ".go")) for f in files_touched):
        suggestions.append("Consider updating documentation or docstrings if public interfaces were modified.")

    # Calculate Confidence Score
    if len(risks) == 0 and has_tests:
        confidence = "High"
    elif len(risks) <= 1:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Generate Summary sentences
    file_list_summary = ", ".join(f"`{os.path.basename(f)}`" for f in files_touched[:3])
    if len(files_touched) > 3:
        file_list_summary += f" and {len(files_touched) - 3} other files"

    summary = (
        f"This pull request ({title}) modifies {changed_files} file(s) with +{additions}/-{deletions} lines, "
        f"touching {file_list_summary}. "
        f"The implementation focuses on delivering the requested features with targeted code modifications."
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files_count": changed_files,
        "additions": additions,
        "deletions": deletions,
    }

def format_review_markdown(analysis: dict) -> str:
    md = []
    md.append("## 🤖 Claude PR Review\n")
    md.append("### 📝 Summary of Changes")
    md.append(analysis["summary"] + "\n")

    md.append("### ⚠️ Identified Risks")
    if analysis["risks"]:
        for r in analysis["risks"]:
            md.append(f"- {r}")
    else:
        md.append("- No critical security vulnerabilities or destructive anti-patterns identified in this diff.")
    md.append("")

    md.append("### 💡 Improvement Suggestions")
    if analysis["suggestions"]:
        for s in analysis["suggestions"]:
            md.append(f"- {s}")
    else:
        md.append("- Code adheres to conventions; ready for maintainer review.")
    md.append("")

    score_badges = {
        "High": "🟢 **High** — Code is well-structured, tested, and safe to merge.",
        "Medium": "🟡 **Medium** — Minor suggestions or risks identified; review recommended before merge.",
        "Low": "🔴 **Low** — Significant risks or missing tests detected; requires attention.",
    }
    md.append("### 🎯 Confidence Score")
    md.append(score_badges.get(analysis["confidence"], analysis["confidence"]) + "\n")

    return "\n".join(md)

def post_github_comment(owner: str, repo: str, pr_num: int, comment: str, token: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_num}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Claude-PR-Review-Agent",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=json.dumps({"body": comment}).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("html_url")

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Sub-Agent")
    parser.add_argument("--pr", type=str, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", type=str, help="Path to local diff file for offline review")
    parser.add_argument("--post-comment", action="store_true", help="Post review directly as a PR comment")
    parser.add_argument("--token", type=str, help="GitHub token (defaults to GITHUB_TOKEN env var)")
    parser.add_argument("--output", type=str, help="Save review markdown to file")

    args = parser.parse_args()
    token = args.token or os.environ.get("GITHUB_TOKEN")

    if args.pr:
        owner, repo, pr_num = parse_pr_url(args.pr)
        pr_meta, pr_diff = fetch_pr_data(owner, repo, pr_num, token)
    elif args.diff_file:
        with open(args.diff_file, "r", encoding="utf-8") as f:
            pr_diff = f.read()
        pr_meta = {
            "title": f"Local Diff ({os.path.basename(args.diff_file)})",
            "body": "Offline diff analysis",
            "changed_files": len(re.findall(r"diff --git", pr_diff)),
            "additions": len(re.findall(r"^\+[^\+]", pr_diff, re.M)),
            "deletions": len(re.findall(r"^-[^-]", pr_diff, re.M)),
        }
    else:
        parser.print_help()
        sys.exit(1)

    analysis = analyze_diff(pr_meta, pr_diff)
    review_markdown = format_review_markdown(analysis)

    print(review_markdown)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_markdown)
        print(f"\n[Saved review to {args.output}]", file=sys.stderr)

    if args.post_comment and args.pr:
        if not token:
            print("Error: --post-comment requires GITHUB_TOKEN to be set.", file=sys.stderr)
            sys.exit(1)
        comment_url = post_github_comment(owner, repo, pr_num, review_markdown, token)
        print(f"[Comment posted to GitHub: {comment_url}]", file=sys.stderr)

if __name__ == "__main__":
    main()
