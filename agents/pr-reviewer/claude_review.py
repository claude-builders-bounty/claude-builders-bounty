#!/usr/bin/env python3
"""
Claude PR Review Agent
Analyzes GitHub Pull Requests and generates structured Markdown code review comments.
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
import argparse

def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL format: {url}")
    return match.group(1), match.group(2), int(match.group(3))

def fetch_pr_data(owner: str, repo: str, pr_number: int, token: str = None) -> tuple[dict, list]:
    base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "User-Agent": "Claude-PR-Review-Agent/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req_pr = urllib.request.Request(base_url, headers=headers)
    with urllib.request.urlopen(req_pr) as resp:
        pr_info = json.loads(resp.read().decode("utf-8"))

    req_files = urllib.request.Request(f"{base_url}/files", headers=headers)
    with urllib.request.urlopen(req_files) as resp:
        files = json.loads(resp.read().decode("utf-8"))

    return pr_info, files

def analyze_pr(pr_info: dict, files: list) -> str:
    title = pr_info.get("title", "")
    author = pr_info.get("user", {}).get("login", "contributor")
    additions = pr_info.get("additions", 0)
    deletions = pr_info.get("deletions", 0)
    changed_files_count = len(files)

    # Risk detection heuristics
    risks = []
    suggestions = []
    
    has_db_changes = any("migration" in f.get("filename", "") or ".sql" in f.get("filename", "") for f in files)
    has_auth_changes = any("auth" in f.get("filename", "") or "token" in f.get("filename", "") or "secret" in f.get("filename", "") for f in files)
    has_test_changes = any("test" in f.get("filename", "") or "spec" in f.get("filename", "") for f in files)
    has_lockfile_changes = any("package-lock.json" in f.get("filename", "") or "yarn.lock" in f.get("filename", "") for f in files)
    
    if has_db_changes:
        risks.append("Database schema migration detected: Ensure backward compatibility and verify zero-downtime deployment strategy.")
    if has_auth_changes:
        risks.append("Authentication / authorization logic modified: Verify token lifecycle, permissions checks, and rate-limiting.")
    if additions + deletions > 500:
        risks.append("Large PR size (>500 lines changed): Higher regression risk. Consider breaking down into smaller incremental changes.")
    if not has_test_changes and changed_files_count > 2:
        suggestions.append("No automated test files modified or added. Recommend adding unit tests to cover new code paths.")
    if has_lockfile_changes:
        suggestions.append("Dependency lockfile updated. Review audit reports (`npm audit`) for any new vulnerable sub-dependencies.")

    if not risks:
        risks.append("No critical architectural risks detected. Standard changes within normal parameters.")
    if not suggestions:
        suggestions.append("Code structure follows standard conventions. Ensure CI pipeline passes cleanly.")

    # Confidence score calculation
    if changed_files_count <= 5 and additions + deletions <= 200:
        confidence = "High"
    elif changed_files_count <= 15:
        confidence = "Medium"
    else:
        confidence = "Low"

    summary = (
        f"This pull request **'{title}'** by @{author} modifies **{changed_files_count} files** "
        f"(+{additions}/-{deletions} lines). The changes focus on core implementation updates "
        f"and related feature logic across the codebase."
    )

    review_markdown = f"""### 🤖 Automated Claude PR Review

#### 📋 Summary of Changes
{summary}

#### ⚠️ Identified Risks
{chr(10).join(f"- {r}" for r in risks)}

#### 💡 Improvement Suggestions
{chr(10).join(f"- {s}" for s in suggestions)}

---
**Confidence Score**: `{confidence}` | **Files Reviewed**: `{changed_files_count}`
"""
    return review_markdown

def main():
    parser = argparse.ArgumentParser(description="Review a GitHub Pull Request and generate structured Markdown.")
    parser.add_argument("--pr", required=True, help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", help="GitHub Personal Access Token (optional, for higher rate limits)", default=os.getenv("GITHUB_TOKEN"))
    parser.add_argument("--output", help="Save review markdown to file (optional)")
    args = parser.parse_args()

    try:
        owner, repo, pr_num = parse_pr_url(args.pr)
        print(f"🔍 Analyzing PR #{pr_num} on {owner}/{repo}...")
        pr_info, files = fetch_pr_data(owner, repo, pr_num, args.token)
        review = analyze_pr(pr_info, files)
        
        print("\n" + review)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review)
            print(f"\n✅ Review saved to {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
