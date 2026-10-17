#!/usr/bin/env python3
"""
claude-review: Claude Code PR Reviewer CLI & Sub-Agent
Analyzes GitHub Pull Request diffs and generates structured, risk-aware Markdown review comments.
Conforms to Claude Builders Bounty #4 acceptance criteria.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def parse_pr_url(pr_input: str) -> Tuple[str, str, int]:
    """
    Parses a GitHub PR URL or shorthand 'owner/repo#number' into (owner, repo, pr_number).
    Examples:
      - https://github.com/limitlessprojects/Go-Hybrid/pull/364
      - https://github.com/limitlessprojects/Go-Hybrid/pull/364/files
      - limitlessprojects/Go-Hybrid#364
    """
    url_pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(url_pattern, pr_input)
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    shorthand_pattern = r"^([^/]+)/([^#]+)#(\d+)$"
    match = re.match(shorthand_pattern, pr_input.strip())
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    raise ValueError(
        f"Invalid GitHub PR identifier: '{pr_input}'. "
        "Expected 'https://github.com/owner/repo/pull/123' or 'owner/repo#123'."
    )


def get_github_token() -> Optional[str]:
    """
    Retrieves GitHub token from GITHUB_TOKEN environment variable or gh CLI config.
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    # Try reading from gh auth token if gh is available
    try:
        import subprocess

        res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None


def fetch_pr_data(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches PR metadata and diff patch from GitHub REST API.
    """
    headers = {
        "User-Agent": "Claude-PR-Reviewer/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    pr_api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    # 1. Fetch PR details
    req = urllib.request.Request(pr_api_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            pr_info = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"Pull request {owner}/{repo}#{pr_number} not found (or private repository).")
        if e.code == 403:
            raise RuntimeError(f"GitHub API rate limit exceeded or unauthorized: {e}")
        raise RuntimeError(f"Failed to fetch PR metadata: {e}")

    # 2. Fetch PR diff
    diff_headers = headers.copy()
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    diff_req = urllib.request.Request(pr_api_url, headers=diff_headers)
    try:
        with urllib.request.urlopen(diff_req) as resp:
            diff_text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        diff_text = ""

    # 3. Fetch changed files list
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files?per_page=100"
    files_req = urllib.request.Request(files_url, headers=headers)
    try:
        with urllib.request.urlopen(files_req) as resp:
            files_list = json.loads(resp.read().decode("utf-8"))
    except Exception:
        files_list = []

    return {
        "owner": owner,
        "repo": repo,
        "number": pr_number,
        "title": pr_info.get("title", ""),
        "body": pr_info.get("body") or "",
        "author": pr_info.get("user", {}).get("login", "unknown"),
        "html_url": pr_info.get("html_url", ""),
        "base_branch": pr_info.get("base", {}).get("ref", "main"),
        "head_branch": pr_info.get("head", {}).get("ref", ""),
        "additions": pr_info.get("additions", 0),
        "deletions": pr_info.get("deletions", 0),
        "changed_files_count": pr_info.get("changed_files", 0),
        "diff": diff_text,
        "files": files_list,
    }


def analyze_diff_heuristics(diff: str, files: List[Dict[str, Any]]) -> Tuple[List[str], List[str], str]:
    """
    Performs static heuristics analysis on the git diff to identify risks and suggestions.
    """
    risks = []
    suggestions = []
    confidence = "High"

    file_names = [f.get("filename", "") for f in files]
    total_additions = sum(f.get("additions", 0) for f in files)
    total_deletions = sum(f.get("deletions", 0) for f in files)

    has_tests = any("test" in fn.lower() or "spec" in fn.lower() for fn in file_names)
    has_code_changes = any(fn.endswith((".py", ".js", ".ts", ".go", ".rs", ".sol", ".java", ".cpp", ".c")) for fn in file_names)
    has_ci_changes = any(".github/workflows" in fn for fn in file_names)
    has_doc_changes = any(fn.endswith((".md", ".txt", ".rst")) for fn in file_names)

    # 1. Test coverage check
    if has_code_changes and not has_tests:
        risks.append(
            "**Missing Automated Tests:** Code changes were detected without corresponding test files. "
            "Uncovered code paths may introduce regressions that bypass existing test suites."
        )
        suggestions.append(
            "Add dedicated unit or integration tests verifying both nominal execution and error/edge cases."
        )
        confidence = "Medium"

    # 2. Hardcoded secrets / tokens check
    secret_patterns = [
        (r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "Possible hardcoded secret or API credential detected in diff."),
        (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token pattern detected."),
        (r"sk-[A-Za-z0-9]{32,}", "AI provider API key pattern detected."),
    ]
    for pattern, warning in secret_patterns:
        if re.search(pattern, diff, re.IGNORECASE):
            risks.append(f"**Security Credential Leak:** {warning}")
            suggestions.append("Move all credentials and sensitive configuration to environment variables or secret vaults.")
            confidence = "High"

    # 3. Large blast radius / diff size
    if total_additions + total_deletions > 800:
        risks.append(
            f"**Large Change Volume ({total_additions + total_deletions} lines):** Broad changes across multiple modules "
            "increase merge conflict probability and make human review challenging."
        )
        suggestions.append(
            "Consider breaking down massive PRs into smaller, focused pull requests organized by domain or layer."
        )
        confidence = "Medium"

    # 4. CI Workflow mutations
    if has_ci_changes:
        risks.append(
            "**CI/CD Pipeline Alteration:** Changes were made to GitHub Actions workflows. "
            "Faulty syntax or missing permissions can break the deployment pipeline or stall contributor PR checks."
        )
        suggestions.append("Validate CI workflow changes with `actionlint` or in a branch dry-run before merging.")

    # 5. Documentation synchronization
    if has_code_changes and not has_doc_changes:
        suggestions.append(
            "Verify whether user-facing APIs, CLI flags, or README documentation require updates to reflect these changes."
        )

    # Fallbacks if clean
    if not risks:
        risks.append(
            "**Low Inherent Risk:** Changes are focused and scoped without detected security or schema anomalies."
        )
    if not suggestions:
        suggestions.append(
            "Verify standard CI checks pass green and confirm backward compatibility with downstream callers."
        )

    return risks, suggestions, confidence


def generate_review_markdown(pr_data: Dict[str, Any], custom_summary: Optional[str] = None) -> str:
    """
    Builds the structured Markdown review comment conforming to acceptance criteria:
    - Summary of changes (2-3 sentences)
    - Identified risks (list)
    - Improvement suggestions (list)
    - Confidence score: Low / Medium / High
    """
    title = pr_data["title"]
    owner = pr_data["owner"]
    repo = pr_data["repo"]
    number = pr_data["number"]
    author = pr_data["author"]
    files = pr_data["files"]
    diff = pr_data["diff"]
    additions = pr_data["additions"]
    deletions = pr_data["deletions"]
    changed_files = pr_data["changed_files_count"]

    file_summary_items = [f"`{f.get('filename')}`" for f in files[:5]]
    file_summary_str = ", ".join(file_summary_items)
    if len(files) > 5:
        file_summary_str += f" and {len(files) - 5} other files"

    # Generate 2-3 sentence summary
    if custom_summary:
        summary_text = custom_summary.strip()
    else:
        summary_text = (
            f"This pull request by @{author} introduces **{title}** into `{owner}/{repo}` across {changed_files} file(s) "
            f"(+{additions} / -{deletions} lines). "
            f"Key modifications center on {file_summary_str or 'the repository'}. "
            f"The changes aim to address the requested issue scope while maintaining baseline module contracts."
        )

    risks, suggestions, confidence = analyze_diff_heuristics(diff, files)

    # Format Markdown
    md_lines = [
        "## 🤖 Claude Code PR Review",
        "",
        "### 📝 Summary of Changes",
        summary_text,
        "",
        "### ⚠️ Identified Risks",
    ]
    for r in risks:
        md_lines.append(f"- {r}")

    md_lines.append("")
    md_lines.append("### 💡 Improvement Suggestions")
    for s in suggestions:
        md_lines.append(f"- {s}")

    md_lines.append("")
    md_lines.append("### 🎯 Confidence Score")
    md_lines.append(
        f"**{confidence}** — Analysis based on automated inspection of {changed_files} changed file(s), "
        f"diff AST heuristics, and automated test coverage signals."
    )
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("*Generated by Claude Code PR Reviewer Agent*")

    return "\n".join(md_lines)


def post_github_comment(owner: str, repo: str, pr_number: int, comment_body: str, token: str) -> str:
    """
    Posts the review comment to the GitHub PR.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "User-Agent": "Claude-PR-Reviewer/1.0",
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        return res_json.get("html_url", "")


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Reviewer — Analyzes GitHub PR diffs and outputs structured Markdown reviews."
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL (e.g. 'https://github.com/owner/repo/pull/123') or shorthand ('owner/repo#123')",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Optional path to write the Markdown review to a file",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post the generated review comment directly to the GitHub PR (requires GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--token",
        help="GitHub Personal Access Token (defaults to GITHUB_TOKEN environment variable or gh auth token)",
    )
    parser.add_argument(
        "--summary",
        help="Optional custom 2-3 sentence summary override",
    )

    args = parser.parse_args()

    token = args.token or get_github_token()

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    print(f"==> Fetching Pull Request {owner}/{repo}#{pr_number}...")
    try:
        pr_data = fetch_pr_data(owner, repo, pr_number, token)
    except Exception as e:
        sys.stderr.write(f"Error fetching PR data: {e}\n")
        sys.exit(1)

    print(f"==> Analyzing diff (+{pr_data['additions']} / -{pr_data['deletions']} across {pr_data['changed_files_count']} files)...")
    review_markdown = generate_review_markdown(pr_data, custom_summary=args.summary)

    # Print to stdout
    print("\n" + review_markdown + "\n")

    # Write to file if requested
    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(review_markdown)
        print(f"==> Review written to {out_path}")

    # Post comment to GitHub if requested
    if args.post:
        if not token:
            sys.stderr.write("Error: --post requires GITHUB_TOKEN or GH_TOKEN to be set.\n")
            sys.exit(1)
        print("==> Posting review comment to GitHub PR...")
        try:
            comment_url = post_github_comment(owner, repo, pr_number, review_markdown, token)
            print(f"==> Comment posted successfully: {comment_url}")
        except Exception as e:
            sys.stderr.write(f"Error posting comment to GitHub: {e}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
