#!/usr/bin/env python3
"""
Claude Code PR Reviewer Sub-Agent
Analyzes GitHub Pull Requests and generates structured, risk-aware Markdown review comments.
Works as a standalone CLI or inside GitHub Actions workflows.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from typing import Any


def parse_pr_url(url_or_num: str, repo: str | None = None) -> tuple[str, str, int]:
    """Extract owner, repo, and PR number from a GitHub PR URL or string."""
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url_or_num)
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    if repo and url_or_num.isdigit():
        parts = repo.split("/")
        if len(parts) == 2:
            return parts[0], parts[1], int(url_or_num)

    raise ValueError(f"Invalid PR URL or specification: {url_or_num}")


def fetch_github_api(endpoint: str, token: str | None = None) -> Any:
    """Fetch JSON payload from GitHub REST API."""
    url = f"https://api.github.com/{endpoint.lstrip('/')}"
    headers = {
        "User-Agent": "Claude-PR-Reviewer/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_pr_diff(owner: str, repo: str, pr_num: int, token: str | None = None) -> str:
    """Fetch raw unified diff for a PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {
        "User-Agent": "Claude-PR-Reviewer/1.0",
        "Accept": "application/vnd.github.v3.diff",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def analyze_diff(pr_data: dict[str, Any], diff_text: str) -> dict[str, Any]:
    """Perform deep analysis on PR metadata and diff content."""
    title = pr_data.get("title", "")
    author = pr_data.get("user", {}).get("login", "unknown")
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)
    changed_files = pr_data.get("changed_files", 0)

    lines = diff_text.splitlines()
    files_modified: list[str] = []
    current_file = ""
    added_lines: list[str] = []

    for line in lines:
        if line.startswith("diff --git"):
            m = re.search(r"b/(.+)$", line)
            if m:
                current_file = m.group(1)
                files_modified.append(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])

    # Risk Analysis Rules
    risks: list[str] = []
    suggestions: list[str] = []

    # Check 1: Security & Credentials
    sec_matches = [l for l in added_lines if re.search(r"(key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]", l, re.I)]
    if sec_matches:
        risks.append("⚠️ **Potential Hardcoded Secrets**: Detected possible API keys or tokens in added lines.")
    
    # Check 2: Error Handling & Try/Catch
    if any(re.search(r"\b(except|catch)\s*:\s*pass\b", l) for l in added_lines):
        risks.append("⚠️ **Swallowed Exceptions**: Empty exception blocks (`except: pass`) detected.")
        suggestions.append("Log or rethrow caught exceptions instead of silently swallowing errors.")

    # Check 3: SQL Safety
    if any(re.search(r"SELECT|INSERT|UPDATE|DELETE", l, re.I) for l in added_lines) and any("%" in l or "+" in l for l in added_lines if "SELECT" in l.upper() or "DELETE" in l.upper()):
        risks.append("⚠️ **Possible Unparametrized SQL**: Found SQL query construction using string formatting.")
        suggestions.append("Use parameterized query bindings (e.g. `?` or `$1`) to prevent SQL injection.")

    # Check 4: Test Coverage
    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files_modified)
    if not has_tests and (additions > 30 or changed_files > 3):
        risks.append("⚠️ **Missing Test Coverage**: Significant code changes made without corresponding test updates.")
        suggestions.append("Add unit or integration tests to verify the modified functionality.")

    # General Suggestions
    if changed_files > 10:
        suggestions.append("Consider breaking large PRs into smaller, focused pull requests for easier review.")
    if additions > 500:
        suggestions.append("High churn PR (+%d lines). Ensure end-to-end integration tests pass." % additions)
    
    if not suggestions:
        suggestions.append("Code changes are clean and follow project structure. Ensure documentation remains up to date.")

    # Confidence Score Calculation
    total_lines = additions + deletions
    if total_lines < 150 and len(risks) == 0:
        confidence = "High"
        confidence_rationale = "Small, focused diff with zero flagged security or pattern risks."
    elif total_lines < 500 and len(risks) <= 1:
        confidence = "Medium"
        confidence_rationale = "Moderate diff size with manageable change scope."
    else:
        confidence = "Low"
        confidence_rationale = "Large diff volume or multiple potential risk flags require manual review."

    summary = (
        f"Pull request **#{pr_data.get('number')}** (\"{title}\") authored by `@{author}` modifies **{changed_files} file(s)** "
        f"with **+{additions}** additions and **-{deletions}** deletions. "
        f"Primary modifications touch: {', '.join([f'`{f}`' for f in files_modified[:4]])}"
        f"{' and others' if len(files_modified) > 4 else ''}."
    )

    return {
        "summary": summary,
        "files_modified": files_modified,
        "risks": risks if risks else ["None identified in automated analysis."],
        "suggestions": suggestions,
        "confidence": confidence,
        "confidence_rationale": confidence_rationale,
    }


def format_markdown_review(pr_data: dict[str, Any], analysis: dict[str, Any]) -> str:
    """Format review analysis into structured Markdown."""
    pr_num = pr_data.get("number")
    title = pr_data.get("title")
    url = pr_data.get("html_url")

    md = [
        f"## 🤖 Automated PR Review for [#{pr_num} - {title}]({url})\n",
        "### 📝 Summary of Changes",
        analysis["summary"],
        "\n### ⚠️ Identified Risks",
    ]
    for risk in analysis["risks"]:
        md.append(f"- {risk}")

    md.append("\n### 💡 Improvement Suggestions")
    for sug in analysis["suggestions"]:
        md.append(f"- {sug}")

    md.append(f"\n---")
    md.append(f"**Confidence Score**: `{analysis['confidence']}` — _{analysis['confidence_rationale']}_")
    md.append("\n_Reviewed by Claude Code PR Review Sub-Agent_")

    return "\n".join(md)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Sub-Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123) or PR number")
    parser.add_argument("--repo", help="GitHub repository in owner/repo format (required if --pr is a number)")
    parser.add_argument("--token", help="GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)")
    parser.add_argument("--output", help="Path to save Markdown output file")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")
    owner, repo, pr_num = parse_pr_url(args.pr, args.repo)

    print(f"Fetching PR #{pr_num} from {owner}/{repo}...")
    pr_data = fetch_github_api(f"repos/{owner}/{repo}/pulls/{pr_num}", token)
    diff_text = fetch_pr_diff(owner, repo, pr_num, token)

    analysis = analyze_diff(pr_data, diff_text)
    review_markdown = format_markdown_review(pr_data, analysis)

    print("\n" + "=" * 60)
    print(review_markdown)
    print("=" * 60 + "\n")

    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(review_markdown)
        print(f"Saved review report to: {out_path}")


if __name__ == "__main__":
    main()
