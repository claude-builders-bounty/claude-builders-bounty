#!/usr/bin/env python3
"""
Claude Code PR Review Sub-Agent
Analyzes Pull Request diffs and generates structured, high-signal engineering reviews.
"""

import os
import sys
import json
import re
import argparse
import urllib.request
import subprocess

def parse_pr_url(url: str) -> tuple[str, str, str]:
    """Extracts owner, repo, and pr_number from GitHub URL."""
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid GitHub PR URL format: {url}")
    return m.group(1), m.group(2), m.group(3)

def fetch_pr_diff(pr_url: str, token: str = "") -> tuple[dict, str]:
    """Fetches PR metadata and raw git diff from GitHub API."""
    owner, repo, pr_num = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    
    headers = {
        "User-Agent": "Claude-PR-Reviewer/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"
        
    # 1. Fetch metadata
    req = urllib.request.Request(api_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        metadata = json.loads(r.read().decode("utf-8"))
        
    # 2. Fetch diff
    headers["Accept"] = "application/vnd.github.v3.diff"
    req_diff = urllib.request.Request(api_url, headers=headers)
    with urllib.request.urlopen(req_diff, timeout=20) as r:
        diff_text = r.read().decode("utf-8")
        
    return metadata, diff_text

def analyze_diff(diff_text: str, metadata: dict = None) -> dict:
    """
    Performs deterministic and heuristic static inspection of diff changes.
    Generates structured review sections: summary, risks, suggestions, confidence.
    """
    lines = diff_text.split("\n")
    files_changed = []
    added_lines = 0
    deleted_lines = 0
    security_flags = []
    performance_flags = []
    test_changes = False
    
    current_file = ""
    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 4:
                current_file = parts[3].lstrip("b/")
                files_changed.append(current_file)
                if "test" in current_file.lower():
                    test_changes = True
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines += 1
            l_strip = line[1:].strip()
            # Security patterns
            if any(k in l_strip for k in ["apiKey", "secret", "password", "token"]) and "=" in l_strip:
                if not any(k in current_file.lower() for k in ["test", "mock", "fixture"]):
                    security_flags.append(f"Potential hardcoded credential or secret assignment in `{current_file}`: `{l_strip[:40]}...`")
            if "dangerouslySetInnerHTML" in l_strip:
                security_flags.append(f"Direct raw HTML injection via `dangerouslySetInnerHTML` in `{current_file}`.")
            if "eval(" in l_strip or "exec(" in l_strip:
                security_flags.append(f"Dynamic code execution (`eval`/`exec`) in `{current_file}`.")
            if "SELECT " in l_strip.upper() and (" + " in l_strip or f"'{{" in l_strip):
                security_flags.append(f"Possible unparameterized SQL concatenation in `{current_file}`.")
            # Performance patterns
            if "SELECT *" in l_strip.upper():
                performance_flags.append(f"Unbounded `SELECT *` query in `{current_file}`.")
            if "useEffect(" in l_strip and "fetch(" in l_strip:
                performance_flags.append(f"Client-side `useEffect` data fetching in `{current_file}` (prefer Server Component or TanStack Query).")
        elif line.startswith("-") and not line.startswith("---"):
            deleted_lines += 1

    # 1. Summary
    title = metadata.get("title", "Pull Request Changes") if metadata else "Code Changes"
    pr_num = metadata.get("number", "") if metadata else ""
    summary = (
        f"This pull request ({f'#{pr_num} ' if pr_num else ''}`{title}`) modifies **{len(files_changed)} file(s)** "
        f"with **+{added_lines}** additions and **-{deleted_lines}** deletions. "
        f"{'Comprehensive test modifications were included.' if test_changes else 'No test files were touched in this change set.'}"
    )

    # 2. Identified Risks
    risks = []
    for f in security_flags:
        risks.append(f"🚨 **Security**: {f}")
    if not test_changes and (added_lines > 30):
        risks.append("⚠️ **Testing**: Significant business logic added without accompanying unit or integration tests.")
    if len(files_changed) > 15:
        risks.append("⚠️ **Blast Radius**: Large PR spanning >15 files increases regression and merge conflict probability.")
    for p in performance_flags:
        risks.append(f"⚡ **Performance**: {p}")
        
    if not risks:
        risks.append("✅ **Clean**: No critical security vulnerabilities or architectural regressions detected.")

    # 3. Improvement Suggestions
    suggestions = []
    if not test_changes:
        suggestions.append("Add unit tests to verify edge cases and happy path for modified functions.")
    if performance_flags:
        suggestions.append("Consider replacing client-side data fetches with Server Components or React Cache.")
    suggestions.append("Ensure automated CI lint, typecheck, and formatting passes cleanly before merge.")
    if len(files_changed) > 20:
        suggestions.append("Consider breaking large cross-cutting refactors into smaller, independently reviewable PRs.")

    # 4. Confidence Score
    if len(security_flags) > 0:
        confidence = "Low"
    elif not test_changes and added_lines > 50:
        confidence = "Medium"
    else:
        confidence = "High"

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files_changed": files_changed,
        "additions": added_lines,
        "deletions": deleted_lines
    }

def format_markdown_review(analysis: dict) -> str:
    md = []
    md.append("## 🔍 Claude Code Automated Pull Request Review\n\n")
    md.append("### 📝 Summary of Changes\n")
    md.append(f"{analysis['summary']}\n\n")
    
    md.append("### ⚠️ Identified Risks\n")
    for r in analysis["risks"]:
        md.append(f"- {r}\n")
    md.append("\n")
    
    md.append("### 💡 Improvement Suggestions\n")
    for s in analysis["suggestions"]:
        md.append(f"- {s}\n")
    md.append("\n")
    
    md.append(f"### 🎯 Confidence Score: **`{analysis['confidence']}`**\n\n")
    md.append("---\n*Review generated autonomously by Claude Code PR Review Sub-Agent.*")
    return "".join(md)

def post_github_comment(pr_url: str, comment_body: str, token: str):
    owner, repo, pr_num = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_num}/comments"
    headers = {
        "User-Agent": "Claude-PR-Reviewer/1.0",
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Sub-Agent")
    parser.add_argument("--pr", type=str, help="GitHub Pull Request URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", type=str, help="Local git diff file for offline review")
    parser.add_argument("--post", action="store_true", help="Post review directly as a GitHub PR comment")
    parser.add_argument("--output", type=str, help="Save review markdown to file")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")

    if args.pr:
        print(f"[*] Fetching PR diff from: {args.pr}...")
        meta, diff_text = fetch_pr_diff(args.pr, token=token)
        analysis = analyze_diff(diff_text, meta)
    elif args.diff_file:
        with open(args.diff_file, "r", encoding="utf-8") as f:
            diff_text = f.read()
        analysis = analyze_diff(diff_text)
    else:
        # Read diff from stdin
        if not sys.stdin.isatty():
            diff_text = sys.stdin.read()
            analysis = analyze_diff(diff_text)
        else:
            parser.print_help()
            sys.exit(1)

    review_md = format_markdown_review(analysis)
    print("\n" + review_md + "\n")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_md)
        print(f"[+] Review saved to {args.output}")

    if args.post and args.pr:
        if not token:
            print("[-] GITHUB_TOKEN environment variable required to post comment.", file=sys.stderr)
            sys.exit(1)
        res = post_github_comment(args.pr, review_md, token)
        print(f"[+] Successfully posted review comment: {res.get('html_url')}")

if __name__ == "__main__":
    main()
