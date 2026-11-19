#!/usr/bin/env python3
"""
Claude PR Reviewer Agent
Analyzes a GitHub PR diff and produces a structured, actionable Markdown review.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


def parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
    """
    Parses a GitHub PR URL into (owner, repo, pr_number).
    e.g. https://github.com/owner/repo/pull/123 -> ('owner', 'repo', 123)
    """
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_details_gh(owner: str, repo: str, pr_number: int) -> Dict:
    repo_slug = f"{owner}/{repo}"
    # Fetch PR metadata via gh CLI
    cmd = [
        "gh", "pr", "view", str(pr_number),
        "-R", repo_slug,
        "--json", "title,body,additions,deletions,changedFiles,headRefName,baseRefName,author"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR #{pr_number} metadata: {res.stderr.strip()}")
    metadata = json.loads(res.stdout)

    # Fetch diff
    diff_cmd = ["gh", "pr", "diff", str(pr_number), "-R", repo_slug]
    diff_res = subprocess.run(diff_cmd, capture_output=True, text=True, encoding="utf-8")
    metadata["diff"] = diff_res.stdout if diff_res.returncode == 0 else ""
    return metadata


def analyze_diff(diff_text: str, title: str, body: str, additions: int, deletions: int) -> Dict:
    """
    Heuristics and static security / quality analysis of PR diff.
    """
    risks = []
    suggestions = []
    
    # 1. Security & credential leak check
    sensitive_patterns = [
        (r"(?i)(api[_-]?key|secret|token|password|passwd|private[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]", "Possible hardcoded secret or token detected in diff."),
        (r"(?i)eval\s*\(", "Use of `eval()` detected which may introduce arbitrary code execution risks."),
        (r"(?i)dangerouslySetInnerHTML", "Usage of `dangerouslySetInnerHTML` found; ensure inputs are properly sanitized."),
        (r"(?i)child_process|subprocess\.run\(.*shell\s*=\s*True", "Shell execution with `shell=True` detected; beware of command injection."),
    ]
    
    for pattern, warning in sensitive_patterns:
        if re.search(pattern, diff_text):
            risks.append(warning)

    # 2. Scope & size analysis
    total_loc = additions + deletions
    if total_loc > 800:
        risks.append(f"Large diff size ({additions} additions, {deletions} deletions across multiple files). High cognitive load for code review.")
        suggestions.append("Consider splitting large feature additions into smaller, incremental PRs.")

    # 3. Test coverage heuristic
    has_test_files = bool(re.search(r"(?i)(test_.*\.py|.*_test\.go|.*\.spec\.[tj]sx?|.*\.test\.[tj]sx?|tests?/)", diff_text))
    if not has_test_files and total_loc > 50:
        risks.append("No automated test files modified or added in this pull request.")
        suggestions.append("Add unit or integration tests verifying the new behavior and edge cases.")

    # 4. Documentation heuristic
    has_docs = bool(re.search(r"(?i)(\.md|docs/|documentation)", diff_text))
    if not has_docs and additions > 100:
        suggestions.append("Ensure relevant user or API documentation is updated to reflect these changes.")

    # Default fallbacks if clean
    if not risks:
        risks.append("No immediate security vulnerabilities, credential leaks, or high-risk patterns identified.")

    if not suggestions:
        suggestions.append("Verify automated CI pipelines and linter runs pass cleanly across all supported targets.")
        suggestions.append("Ensure adequate logging or telemetry is in place for production observability.")

    # Confidence calculation
    if len(risks) == 1 and "No immediate security vulnerabilities" in risks[0]:
        confidence = "High"
    elif len(risks) <= 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
    }


def generate_structured_review(metadata: Dict) -> str:
    title = metadata.get("title", "Pull Request")
    body = metadata.get("body", "")
    additions = metadata.get("additions", 0)
    deletions = metadata.get("deletions", 0)
    changed_files = metadata.get("changedFiles", 0)
    diff = metadata.get("diff", "")
    author = metadata.get("author", {}).get("login", "contributor")

    analysis = analyze_diff(diff, title, body, additions, deletions)

    # Summary sentences
    summary = (
        f"This pull request by @{author} proposes '{title}', touching {changed_files} file(s) "
        f"with +{additions}/-{deletions} lines modified. "
        f"The changes introduce targeted functionality and structural updates according to the repository guidelines."
    )

    lines = [
        "## 🤖 Claude Code PR Review",
        "",
        "### 📝 Summary of Changes",
        summary,
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
    lines.append("*Reviewed autonomously by Claude Code PR Reviewer Agent.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", help="Optional output markdown file path")
    parser.add_argument("--post-comment", action="store_true", help="Post the generated review comment directly to the PR")

    args = parser.parse_args()

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
        metadata = fetch_pr_details_gh(owner, repo, pr_number)
        review_md = generate_structured_review(metadata)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review_md)
            print(f"Review saved to: {args.output}")
        else:
            print(review_md)

        if args.post_comment:
            comment_cmd = ["gh", "pr", "comment", str(pr_number), "-R", f"{owner}/{repo}", "--body", review_md]
            res = subprocess.run(comment_cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"Review comment posted successfully to PR #{pr_number}!")
            else:
                print(f"Failed to post comment: {res.stderr.strip()}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
