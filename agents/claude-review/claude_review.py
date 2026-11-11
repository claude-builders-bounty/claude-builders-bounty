#!/usr/bin/env python3
"""
Claude Code Sub-Agent: Automated Pull Request Reviewer
Fetches diffs from GitHub PRs, analyzes code changes for security, logic, and style risks,
and produces a structured Markdown review comment.
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.error

def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid GitHub PR URL format: {url}")
    return m.group(1), m.group(2), int(m.group(3))

def fetch_pr_data(owner: str, repo: str, pull_number: int, token: str = None) -> tuple[dict, str]:
    headers = {"User-Agent": "Claude-Review-Agent/1.0", "Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    req = urllib.request.Request(pr_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        pr_json = json.loads(resp.read().decode("utf-8"))

    # Fetch raw diff
    diff_headers = dict(headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    req_diff = urllib.request.Request(pr_url, headers=diff_headers)
    with urllib.request.urlopen(req_diff) as resp:
        diff_text = resp.read().decode("utf-8", errors="replace")

    return pr_json, diff_text

def analyze_diff(pr_data: dict, diff_text: str) -> dict:
    title = pr_data.get("title", "")
    body = pr_data.get("body", "") or ""
    files_changed = pr_data.get("changed_files", 0)
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)

    risks = []
    suggestions = []

    # Heuristic & static analysis rules
    if re.search(r"\b(eval|exec|Function)\s*\(", diff_text):
        risks.append("Potential arbitrary code execution risk detected (`eval`/`exec`).")
    if re.search(r"\b(password|secret|api_key|token)\s*=\s*['"][^'"]{8,}['"]", diff_text, re.IGNORECASE):
        risks.append("Possible hardcoded secret or credential token in diff.")
    if re.search(r"SELECT\s+.*\s+FROM\s+.*\+.*", diff_text, re.IGNORECASE):
        risks.append("Possible SQL string concatenation (SQL injection vulnerability).")
    if additions > 800 and not any(k in diff_text for k in ["test", "spec", "fixture"]):
        risks.append("Large pull request (+800 lines) without dedicated test coverage modifications.")

    if not risks:
        risks.append("No critical security or runtime defects detected.")

    if additions > 500:
        suggestions.append("Consider decomposing this change into smaller, focused pull requests to facilitate review.")
    if "TODO" in diff_text or "FIXME" in diff_text:
        suggestions.append("Unresolved `TODO` / `FIXME` comments identified; verify before merging.")
    suggestions.append("Ensure full test suite passes cleanly across all supported runtime targets.")

    # Determine confidence score
    if additions < 300 and risks[0].startswith("No critical"):
        confidence = "High"
    elif additions < 800:
        confidence = "Medium"
    else:
        confidence = "Low"

    summary = (
        f"This pull request modifies {files_changed} file(s) with {additions} addition(s) and {deletions} deletion(s). "
        f"The primary focus is '{title}'. The implementation introduces structured changes to the codebase."
    )

    return {
        "title": title,
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence
    }

def format_markdown_review(review: dict) -> str:
    lines = [
        "## 🤖 Claude Code Review Summary",
        "",
        review["summary"],
        "",
        "### ⚠️ Identified Risks",
    ]
    for r in review["risks"]:
        lines.append(f"- {r}")

    lines.extend([
        "",
        "### 💡 Improvement Suggestions",
    ])
    for s in review["suggestions"]:
        lines.append(f"- {s}")

    lines.extend([
        "",
        f"**Confidence Score:** `{review['confidence']}`"
    ])
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Sub-Agent")
    parser.add_argument("--pr", required=True, help="GitHub Pull Request URL (https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", help="GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)")
    parser.add_argument("--output", help="Optional path to write review markdown")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")

    owner, repo, pr_number = parse_pr_url(args.pr)
    pr_data, diff_text = fetch_pr_data(owner, repo, pr_number, token)
    analysis = analyze_diff(pr_data, diff_text)
    md_output = format_markdown_review(analysis)

    print(md_output)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md_output)

if __name__ == "__main__":
    main()
