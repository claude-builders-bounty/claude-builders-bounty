#!/usr/bin/env python3
"""Claude Code PR Reviewer Agent — analyzes PR diffs and returns structured reviews.

Usage:
    python claude-pr-reviewer.py --pr https://github.com/owner/repo/pull/123
    python claude-pr-reviewer.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def parse_pr_url(url: str) -> tuple[str, str, str]:
    """Parse a GitHub PR URL into owner, repo, pr_number."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 4 or path_parts[2] != "pull":
        raise ValueError(f"Invalid PR URL: {url}. Expected format: https://github.com/owner/repo/pull/123")
    return path_parts[0], path_parts[1], path_parts[3]


def api_get(url: str, token: str) -> dict | list:
    """Make an authenticated GitHub API request."""
    req = Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-pr-reviewer/1.0")
    with urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_pr_data(owner: str, repo: str, pr_number: str, token: str) -> dict:
    """Fetch PR metadata, diff, and files changed."""
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    
    # PR metadata (JSON)
    pr_req = Request(f"{base_url}/pulls/{pr_number}")
    pr_req.add_header("Authorization", f"token {token}")
    pr_req.add_header("Accept", "application/vnd.github+json")
    pr_req.add_header("User-Agent", "claude-pr-reviewer/1.0")
    with urlopen(pr_req) as resp:
        pr_data = json.loads(resp.read().decode())

    # PR diff (text)
    diff_text = api_get(f"{base_url}/pulls/{pr_number}", token)

    # PR files (JSON)
    files_req = Request(f"{base_url}/pulls/{pr_number}/files?per_page=100")
    files_req.add_header("Authorization", f"token {token}")
    files_req.add_header("Accept", "application/vnd.github+json")
    files_req.add_header("User-Agent", "claude-pr-reviewer/1.0")
    with urlopen(files_req) as resp:
        files_data = json.loads(resp.read().decode())

    return {
        "pr": pr_data,
        "diff": diff_text,
        "files": files_data,
    }


def analyze_diff(diff_text: str, files: list, pr_data: dict) -> dict:
    """Analyze the PR diff and return structured findings."""
    findings = {
        "risks": [],
        "suggestions": [],
    }

    # Check for hardcoded secrets
    secret_patterns = {
        "API key": r'["\']?(?:api[_-]?key|apikey|API_KEY)["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']',
        "Token (ghp_)": r'ghp_[A-Za-z0-9]{36}',
        "Token (gho_)": r'gho_[A-Za-z0-9]{36}',
        "Token (github_pat_)": r'github_pat_[A-Za-z0-9_]{40,}',
        "AWS key": r'AKIA[0-9A-Z]{16}',
        "Private key header": r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
        "Password in code": r'(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\'\s]{4,}["\']',
    }
    for name, pattern in secret_patterns.items():
        matches = re.findall(pattern, diff_text, re.IGNORECASE)
        if matches:
            findings["risks"].append({
                "severity": "HIGH",
                "category": "Security",
                "title": f"Potential hardcoded {name} found",
                "detail": f"Found {len(matches)} match(es) for {name}. Use environment variables or a secrets manager instead.",
            })

    # Check for missing test files
    changed_files = [f["filename"] for f in files]
    src_files = [f for f in changed_files if f.endswith((".py", ".ts", ".tsx", ".js", ".go", ".rs")) and "test" not in f.lower()]
    test_files = [f for f in changed_files if "test" in f.lower() or f.endswith((".test.ts", ".test.tsx", ".spec.ts", "_test.py", "_test.go"))]
    if src_files and not test_files:
        findings["risks"].append({
            "severity": "MEDIUM",
            "category": "Testing",
            "title": "No test files found in this PR",
            "detail": f"{len(src_files)} source file(s) changed without corresponding tests. Consider adding tests for new or modified functionality.",
        })

    # Check for large PR
    total_additions = sum(f.get("additions", 0) for f in files)
    total_deletions = sum(f.get("deletions", 0) for f in files)
    total_files = len(files)
    if total_additions + total_deletions > 500:
        findings["suggestions"].append({
            "category": "Size",
            "title": "Large PR — consider splitting",
            "detail": f"Total changes: +{total_additions}/-{total_deletions} across {total_files} files. "
                      f"Consider splitting into smaller, focused PRs for easier review.",
        })

    # Check for dependency changes without lockfile
    dep_files = {"package.json", "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml", "Gemfile"}
    lock_files = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "go.sum", "Cargo.lock", "Gemfile.lock", "uv.lock"}
    has_dep_change = any(f in dep_files for f in changed_files)
    has_lock_change = any(f in lock_files for f in changed_files)
    if has_dep_change and not has_lock_change:
        findings["risks"].append({
            "severity": "HIGH",
            "category": "Dependencies",
            "title": "Dependency file changed without lockfile update",
            "detail": "The dependency manifest changed but no lockfile was updated. This can lead to unreproducible builds.",
        })

    # Check for TODO/FIXME without tracking
    todo_matches = re.findall(r'(TODO|FIXME|HACK|XXX)[: ]?(.*)', diff_text)
    if todo_matches:
        findings["suggestions"].append({
            "category": "Code Quality",
            "title": "Tracker comments found",
            "detail": f"{len(todo_matches)} TODO/FIXME/HACK comments found. Consider linking them to issues if they represent known technical debt.",
        })

    return {
        "stats": {
            "files_changed": total_files,
            "additions": total_additions,
            "deletions": total_deletions,
        },
        "risks": findings["risks"],
        "suggestions": findings["suggestions"],
    }


def calculate_confidence(findings: dict) -> str:
    """Calculate confidence score based on analysis depth."""
    total_checks = 6  # secrets, tests, size, deps, todos, files
    checks_run = total_checks
    risk_count = len(findings["risks"])
    suggestion_count = len(findings["suggestions"])
    
    # High risk count or limited diff = lower confidence
    if risk_count >= 3:
        return "High"  # Many issues found = high confidence in findings
    elif risk_count >= 1:
        return "Medium"
    return "Medium"  # Automated analysis is always at most Medium without human review


def format_markdown(pr_data: dict, findings: dict, confidence: str) -> str:
    """Format the analysis into structured Markdown."""
    pr_title = pr_data.get("title", "Unknown PR")
    pr_url = pr_data.get("html_url", "")
    pr_author = pr_data.get("user", {}).get("login", "unknown")
    pr_body = pr_data.get("body", "") or ""

    lines = [
        f"# PR Review: {pr_title}",
        f"",
        f"**PR:** [{pr_url}]({pr_url})  ",
        f"**Author:** @{pr_author}  ",
        f"**Analyzed:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Confidence:** {confidence}  ",
        f"",
        f"## Summary",
        f"",
        f"This PR changes **{findings['stats']['files_changed']} file(s)** "
        f"(+{findings['stats']['additions']}/-{findings['stats']['deletions']}).",
        f"",
    ]

    # Extract summary from PR body
    if pr_body:
        first_para = pr_body.split("\n\n")[0].strip()
        if len(first_para) > 500:
            first_para = first_para[:497] + "..."
        lines.append(f"{first_para}")
        lines.append("")

    if findings["risks"]:
        lines.append("## ⚠️ Identified Risks")
        lines.append("")
        for risk in findings["risks"]:
            lines.append(f"### {risk['severity']}: {risk['title']}")
            lines.append(f"")
            lines.append(f"**Category:** {risk['category']}")
            lines.append(f"")
            lines.append(risk['detail'])
            lines.append("")

    if findings["suggestions"]:
        lines.append("## 💡 Improvement Suggestions")
        lines.append("")
        for sug in findings["suggestions"]:
            lines.append(f"### {sug['title']}")
            lines.append(f"")
            lines.append(f"**Category:** {sug['category']}")
            lines.append(f"")
            lines.append(sug['detail'])
            lines.append("")

    if not findings["risks"] and not findings.get("suggestions"):
        lines.append("## ✅ No Issues Found")
        lines.append("")
        lines.append("No significant risks or suggestions detected in this PR. "
                     "This automated review can't catch logic errors — manual review still recommended.")
        lines.append("")

    lines.append("---")
    lines.append("*This review was generated automatically by claude-pr-reviewer. "
                 "It is not a substitute for human code review.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GitHub token required. Set GITHUB_TOKEN env var or pass --token.", file=sys.stderr)
        return 1

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Analyzing {owner}/{repo}#{pr_number}...", file=sys.stderr)

    try:
        data = fetch_pr_data(owner, repo, pr_number, token)
    except Exception as e:
        print(f"Error fetching PR data: {e}", file=sys.stderr)
        return 1

    findings = analyze_diff(data["diff"], data["files"], data["pr"])
    confidence = calculate_confidence(findings)
    report = format_markdown(data["pr"], findings, confidence)

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
