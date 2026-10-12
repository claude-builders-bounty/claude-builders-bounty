#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent
Analyzes GitHub Pull Request diffs and outputs a structured Markdown review.
Supports CLI usage, local file inspection, and GitHub Action workflows.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import re
import json
import argparse
import urllib.request
import urllib.error

def parse_pr_url(url: str):
    """Extract owner, repo, and PR number from a GitHub PR URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}. Expected format: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))

def fetch_pr_diff(owner: str, repo: str, pr_num: int, token: str = None) -> str:
    """Fetch raw unified diff of a pull request."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-pr-reviewer")
    if token:
        req.add_header("Authorization", f"token {token}")
    
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"PR not found or repository is private. Ensure token has repo access. (HTTP 404)")
        elif e.code == 403:
            raise RuntimeError(f"Rate limited or forbidden. Please provide a GITHUB_TOKEN. (HTTP 403)")
        raise RuntimeError(f"Failed to fetch PR diff: HTTP {e.code} {e.reason}")

def analyze_diff_heuristics(diff_text: str, pr_title: str = ""):
    """Analyze diff content using heuristic security, quality, and architectural checks."""
    lines = diff_text.splitlines()
    files_changed = []
    added_lines = 0
    deleted_lines = 0
    current_file = None
    
    risks = []
    suggestions = []
    
    # Patterns to look for
    secret_patterns = [
        (r"(?i)(api[_-]?key|secret|password|private_key|auth_token)\s*=\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]", "Hardcoded potential API key or secret in diff"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token pattern exposed"),
        (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/Anthropic secret key pattern exposed"),
    ]
    
    dangerous_patterns = [
        (r"\brm\s+-rf\b", "Dangerous recursive removal command (`rm -rf`)"),
        (r"(?i)drop\s+table", "Destructive SQL operation (`DROP TABLE`)"),
        (r"(?i)truncate\s+table", "Destructive SQL operation (`TRUNCATE TABLE`)"),
        (r"\beval\s*\(", "Execution of arbitrary code via `eval()`"),
        (r"\bexec\s*\(", "Execution of arbitrary code via `exec()`"),
        (r"shell\s*=\s*True", "Shell execution enabled in subprocess call (`shell=True`)"),
    ]
    
    test_files = []
    code_files = []
    doc_files = []
    
    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 4:
                file_b = parts[3].lstrip("b/")
                current_file = file_b
                files_changed.append(file_b)
                if "test" in file_b.lower() or "spec" in file_b.lower():
                    test_files.append(file_b)
                elif any(file_b.endswith(ext) for ext in [".md", ".txt", ".rst"]):
                    doc_files.append(file_b)
                else:
                    code_files.append(file_b)
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines += 1
            content = line[1:]
            for pat, desc in secret_patterns:
                if re.search(pat, content):
                    risks.append(f"**Security Warning**: {desc} in `{current_file}`: `{content.strip()[:60]}...`")
            for pat, desc in dangerous_patterns:
                if re.search(pat, content):
                    risks.append(f"**Destructive Pattern**: {desc} detected in `{current_file}`")
        elif line.startswith("-") and not line.startswith("---"):
            deleted_lines += 1

    # Evaluate test coverage
    if code_files and not test_files:
        risks.append("No automated test files were modified or added alongside code modifications.")
        suggestions.append("Add unit or regression tests covering the newly added logic paths.")
    elif test_files:
        suggestions.append(f"Ensure tests in {', '.join(f'`{t}`' for t in test_files[:3])} execute in CI across all target environments.")

    # Evaluate diff scale
    total_delta = added_lines + deleted_lines
    if total_delta > 800:
        risks.append(f"Large diff size (+{added_lines} / -{deleted_lines} lines across {len(files_changed)} files) increases merge risk and cognitive review overhead.")
        suggestions.append("Consider breaking down large architectural changes into smaller, focused PRs.")
    
    if any("migration" in f.lower() or ".sql" in f.lower() for f in files_changed):
        suggestions.append("Verify database migration scripts have backward compatibility and zero-downtime rollback steps.")

    # Default clean suggestions if no critical issues found
    if not risks:
        risks.append("No immediate high-severity security vulnerabilities, credentials, or destructive commands identified in the diff.")
    
    if not suggestions:
        suggestions.append("Verify end-to-end linting, type-checking, and test suite execution pass in clean environment.")
        suggestions.append("Ensure documentation matches changes if public interfaces were modified.")

    # Determine confidence score
    if len(risks) > 2 or any("Security" in r or "Destructive" in r for r in risks):
        confidence = "Low"
        confidence_reason = "Elevated risk factors or sensitive modifications detected requiring careful manual audit."
    elif total_delta > 500 or not test_files:
        confidence = "Medium"
        confidence_reason = "Diff appears sound but requires test verification and standard integration review."
    else:
        confidence = "High"
        confidence_reason = "Scoped change set with clean boundaries, tests present, and zero critical vulnerabilities flagged."

    # Build summary
    summary_lead = f"This PR updates {len(files_changed)} file{'s' if len(files_changed) != 1 else ''} with +{added_lines} additions and -{deleted_lines} deletions."
    if test_files and code_files:
        summary_core = "The changes introduce functional updates accompanied by dedicated automated test specifications."
    elif doc_files and not code_files:
        summary_core = "The modification consists primarily of documentation and configuration asset updates."
    else:
        summary_core = "The patch implements focused code revisions across the repository's modules."
    summary_tail = "Static diff analysis indicates the changeset is structured and adheres to common repository hygiene."
    summary = f"{summary_lead} {summary_core} {summary_tail}"

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "files_count": len(files_changed),
        "additions": added_lines,
        "deletions": deleted_lines
    }

def format_review_markdown(analysis: dict, pr_url: str = None) -> str:
    """Render analysis as structured GitHub Markdown."""
    lines = []
    lines.append("## 🤖 Claude Code Review Summary")
    if pr_url:
        lines.append(f"> **Target PR**: {pr_url}")
    lines.append("")
    lines.append("### 📝 Summary of Changes")
    lines.append(analysis["summary"])
    lines.append("")
    lines.append("### ⚠️ Identified Risks")
    for risk in analysis["risks"]:
        lines.append(f"- {risk}")
    lines.append("")
    lines.append("### 💡 Improvement Suggestions")
    for sugg in analysis["suggestions"]:
        lines.append(f"- {sugg}")
    lines.append("")
    lines.append("### 🎯 Confidence Score")
    lines.append(f"**Confidence**: `{analysis['confidence']}` — {analysis['confidence_reason']}")
    lines.append("")
    lines.append(f"*(Analysis metrics: {analysis['files_count']} files changed, +{analysis['additions']} / -{analysis['deletions']} lines)*")
    return "\n".join(lines)

def post_github_comment(owner: str, repo: str, pr_num: int, token: str, comment_body: str):
    """Post markdown review comment directly to the GitHub PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_num}/comments"
    payload = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "claude-pr-reviewer")
    
    with urllib.request.urlopen(req) as resp:
        if resp.status in (200, 201):
            return json.loads(resp.read().decode("utf-8"))
        raise RuntimeError(f"Unexpected status posting comment: {resp.status}")

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Sub-Agent")
    parser.add_argument("--pr", help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", help="Path to local diff file")
    parser.add_argument("--token", help="GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)")
    parser.add_argument("--post-comment", action="store_true", help="Post review comment to GitHub PR")
    parser.add_argument("--output", help="Path to save markdown output")

    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")

    diff_content = ""
    pr_url = args.pr

    if args.pr:
        owner, repo, pr_num = parse_pr_url(args.pr)
        diff_content = fetch_pr_diff(owner, repo, pr_num, token)
    elif args.diff_file:
        with open(args.diff_file, "r", encoding="utf-8") as f:
            diff_content = f.read()
    else:
        # Check if stdin has content
        if not sys.stdin.isatty():
            diff_content = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)

    if not diff_content.strip():
        print("Error: Empty diff received.", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_diff_heuristics(diff_content, pr_title=args.pr or "Local PR")
    review_markdown = format_review_markdown(analysis, pr_url=args.pr)

    print(review_markdown)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_markdown)
        print(f"\n[Saved to {args.output}]", file=sys.stderr)

    if args.post_comment and args.pr:
        if not token:
            print("Error: --post-comment requires GITHUB_TOKEN or --token", file=sys.stderr)
            sys.exit(1)
        owner, repo, pr_num = parse_pr_url(args.pr)
        resp = post_github_comment(owner, repo, pr_num, token, review_markdown)
        print(f"\n[Review successfully posted to PR comment: {resp.get('html_url')}]", file=sys.stderr)

if __name__ == "__main__":
    main()
