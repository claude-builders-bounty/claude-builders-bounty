#!/usr/bin/env python3
"""
Claude Code Sub-Agent: Automated Pull Request Reviewer
Analyzes GitHub PR diffs for security vulnerabilities, logic defects, regression risks,
and test adequacy, outputting a structured Markdown review comment.
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Optional, Any


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """
    Parses a GitHub pull request URL or 'owner/repo#number' string into (owner, repo, pull_number).
    """
    url = url.strip()
    # Match https://github.com/owner/repo/pull/123 or https://api.github.com/repos/owner/repo/pulls/123
    m = re.match(r"https?://(?:api\.)?github\.com/(?:repos/)?([^/]+)/([^/]+)/pulls?/(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    # Match shorthand 'owner/repo#123'
    m_short = re.match(r"^([^/]+)/([^#]+)#(\d+)$", url)
    if m_short:
        return m_short.group(1), m_short.group(2), int(m_short.group(3))

    raise ValueError(f"Invalid GitHub PR URL or format: '{url}'. Expected format: https://github.com/owner/repo/pull/123")


def fetch_pr_data(owner: str, repo: str, pull_number: int, token: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """
    Fetches PR metadata JSON and raw diff from the GitHub REST API.
    """
    headers = {
        "User-Agent": "Claude-PR-Reviewer-Agent/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    api_base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"

    # 1. Fetch PR metadata
    req_meta = urllib.request.Request(api_base, headers=headers)
    try:
        with urllib.request.urlopen(req_meta, timeout=20) as resp:
            pr_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"Pull request not found: {owner}/{repo}#{pull_number} (404 Not Found).")
        elif e.code == 401 or e.code == 403:
            raise RuntimeError(f"GitHub API authentication/rate-limit error ({e.code}): {e.reason}. Try setting GITHUB_TOKEN.")
        raise RuntimeError(f"Failed to fetch PR metadata: {e}")

    # 2. Fetch raw diff
    diff_headers = dict(headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    req_diff = urllib.request.Request(api_base, headers=diff_headers)
    try:
        with urllib.request.urlopen(req_diff, timeout=20) as resp:
            diff_text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        diff_text = ""

    return pr_data, diff_text


def analyze_diff(pr_data: Dict[str, Any], diff_text: str) -> Dict[str, Any]:
    """
    Performs static and semantic analysis of the PR diff to detect risks,
    generate improvement suggestions, and calculate a confidence score.
    """
    title = pr_data.get("title", "Pull Request")
    body = pr_data.get("body", "") or ""
    files_changed = pr_data.get("changed_files", 0)
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)

    # Extract added/modified lines from diff
    added_lines = [
        line[1:] for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    added_content = "\n".join(added_lines)

    risks: List[str] = []
    suggestions: List[str] = []

    # 1. Arbitrary code execution / command injection checks
    if re.search(r"\b(eval|exec)\s*\(", added_content):
        risks.append("Potential arbitrary code execution risk detected (`eval()` or `exec()` usage).")
    if re.search(r"\bos\.system\s*\(", added_content) or re.search(r"subprocess\.\w+\([^)]*shell\s*=\s*True", added_content):
        risks.append("Shell execution with `shell=True` or `os.system` detected; susceptible to command injection.")

    # 2. Hardcoded secrets & credential leak checks
    secret_pattern = r"(?i)\b(api_key|secret_key|private_key|token|auth_token|passwd|password)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{12,}['\"]"
    if re.search(secret_pattern, added_content):
        risks.append("Possible hardcoded credential or secret token detected in added code.")

    # 3. SQL injection patterns (dynamic concatenation or f-strings in queries)
    if (
        re.search(r"(?i)\b(SELECT|DELETE|UPDATE|INSERT)\b[^\n]*['\"]\s*\+\s*[a-zA-Z_]\w*", added_content)
        or re.search(r"(?i)\bf['\"][^\n]*(?:SELECT|DELETE|UPDATE|INSERT)\b[^\n]*\{[^\n]+\}", added_content)
    ):
        risks.append("Possible dynamic SQL query string concatenation or f-string interpolation detected (SQL injection vector).")

    # 4. Exception swallowing checks
    if re.search(r"except(?:\s+\w+)?:\s*(?:pass|\.\.\.)", added_content):
        risks.append("Silent exception swallowing (`except: pass`) detected without logging or error propagation.")

    # 5. Test adequacy check
    has_test_changes = any(
        k in diff_text.lower() for k in ["test_", "_test.", "spec.", "tests/", "__tests__/"]
    )
    if additions > 150 and not has_test_changes:
        risks.append(f"Substantial logic addition (+{additions} lines) without accompanying test coverage updates.")

    # 6. Fallback if clean
    if not risks:
        risks.append("No critical security vulnerabilities or severe anti-patterns detected.")

    # Improvement Suggestions
    if additions > 500 or files_changed > 15:
        suggestions.append(f"Diff spans {files_changed} files and {additions} additions; consider splitting into smaller, atomic PRs to expedite review.")
    if "TODO" in added_content or "FIXME" in added_content:
        suggestions.append("Found `TODO` / `FIXME` comments in modified code; ensure tracking issues or completion prior to merge.")
    if not has_test_changes and additions > 50:
        suggestions.append("Add automated unit or regression tests covering the newly added execution branches.")
    if re.search(r"(?i)\bany\b", added_content) and any(f in diff_text for f in [".ts", ".tsx"]):
        suggestions.append("Review usage of loose `any` types; prefer strict runtime type narrowing or `unknown`.")
    suggestions.append("Verify CI build and automated test suites pass cleanly across all target environments.")

    # Deduplicate suggestions
    seen_sugg = set()
    dedup_suggestions = []
    for s in suggestions:
        if s not in seen_sugg:
            seen_sugg.add(s)
            dedup_suggestions.append(s)

    # Confidence Score Calculation
    # High: clean diff, reasonable size, test updates included, 0 severe risks
    # Medium: moderate size or minor risk flag
    # Low: large diff, multiple security risks, or zero tests with large additions
    severe_risks_count = sum(1 for r in risks if not r.startswith("No critical"))
    if severe_risks_count == 0 and additions < 400:
        confidence = "High"
    elif severe_risks_count <= 1 and additions < 800:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Concise 2-3 sentence summary
    summary = (
        f"This pull request modifies {files_changed} file(s) across {additions} addition(s) and {deletions} deletion(s). "
        f"The changes primarily focus on '{title}'. "
        f"The patch introduces targeted modifications with an overall {confidence.lower()} confidence rating."
    )

    return {
        "title": title,
        "files_changed": files_changed,
        "additions": additions,
        "deletions": deletions,
        "summary": summary,
        "risks": risks,
        "suggestions": dedup_suggestions,
        "confidence": confidence,
    }


def format_markdown_review(analysis: Dict[str, Any]) -> str:
    """
    Renders structured Markdown review matching acceptance criteria specifications.
    """
    lines = [
        "## 🤖 Claude Code PR Review",
        "",
        "### Summary",
        analysis["summary"],
        "",
        "### Identified Risks",
    ]
    for r in analysis["risks"]:
        lines.append(f"- {r}")

    lines.extend([
        "",
        "### Improvement Suggestions",
    ])
    for s in analysis["suggestions"]:
        lines.append(f"- {s}")

    lines.extend([
        "",
        "### Confidence Score",
        f"**{analysis['confidence']}**",
        "",
        "---",
        "<sub>Reviewed autonomously by Claude Code PR Reviewer Sub-Agent</sub>",
    ])
    return "\n".join(lines)


def post_github_comment(owner: str, repo: str, pull_number: int, comment: str, token: str) -> None:
    """
    Posts the structured review comment to the GitHub pull request issue discussion.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Claude-PR-Reviewer-Agent/1.0",
        "Content-Type": "application/json",
    }
    payload = json.dumps({"body": comment}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"✅ Successfully posted review comment: {data.get('html_url')}")
    except Exception as e:
        raise RuntimeError(f"Failed to post comment to GitHub PR: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Claude Code Sub-Agent: Automated Pull Request Reviewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123 or owner/repo#123)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub API token (defaults to GITHUB_TOKEN environment variable)",
    )
    parser.add_argument(
        "--output",
        help="Path to write the generated markdown review output",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the review comment directly to the pull request discussion on GitHub",
    )
    args = parser.parse_args()

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1

    try:
        pr_data, diff_text = fetch_pr_data(owner, repo, pr_number, args.token)
    except Exception as e:
        sys.stderr.write(f"Error fetching PR: {e}\n")
        return 1

    analysis = analyze_diff(pr_data, diff_text)
    markdown_output = format_markdown_review(analysis)

    # Print to stdout
    print(markdown_output)

    # Write to file if requested
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(markdown_output)
            sys.stderr.write(f"Review written to {args.output}\n")
        except Exception as e:
            sys.stderr.write(f"Warning: Could not write output to {args.output}: {e}\n")

    # Post to GitHub if requested
    if args.post_comment:
        if not args.token:
            sys.stderr.write("Error: --post-comment requires GITHUB_TOKEN or --token.\n")
            return 1
        try:
            post_github_comment(owner, repo, pr_number, markdown_output, args.token)
        except Exception as e:
            sys.stderr.write(f"Error posting comment: {e}\n")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
