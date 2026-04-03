#!/usr/bin/env python3
"""
Claude Code sub-agent that reviews a PR and posts a structured comment.
Usage: python review.py <pr-url> [--token GITHUB_TOKEN] [--post]
"""

import json
import os
import re
import subprocess
import sys
from typing import Optional


def run_cmd(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def parse_pr_url(url: str) -> tuple:
    """Parse PR URL into (owner, repo, pr_number)."""
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        print(f"Invalid PR URL: {url}", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2), int(match.group(3))


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    return run_cmd(f"gh pr diff {pr_number} --repo {owner}/{repo}")


def get_pr_info(owner: str, repo: str, pr_number: int) -> dict:
    output = run_cmd(f"gh pr view {pr_number} --repo {owner}/{repo} --json title,body,author,additions,deletions,changedFiles")
    return json.loads(output)


def analyze_diff(diff: str) -> dict:
    categories = {
        "bugs": [],
        "security": [],
        "performance": [],
        "style": [],
        "edge_cases": [],
        "positive": [],
    }

    lines = diff.split("\n")
    current_file = ""
    line_num = 0

    for line in lines:
        if line.startswith("+++ b/"):
            current_file = line[6:]
            line_num = 0
        elif line.startswith("+") and not line.startswith("+++"):
            line_num += 1
            content = line[1:].strip()

            # Security checks
            if re.search(r"(password|secret|api_key|token)\s*=\s*[\"']", content, re.I):
                categories["security"].append(f"L{line_num} {current_file}: Hardcoded secret detected")
            if re.search(r"eval\s*\(", content):
                categories["security"].append(f"L{line_num} {current_file}: eval() usage — potential code injection")
            if re.search(r"subprocess\.(call|run|Popen)\(.*shell=True", content):
                categories["security"].append(f"L{line_num} {current_file}: shell=True — potential command injection")
            if re.search(r"SELECT.*\+.*FROM|f\"SELECT.*{", content, re.I):
                categories["security"].append(f"L{line_num} {current_file}: Potential SQL injection")

            # Bug checks
            if re.search(r"except\s*:", content) and "Exception" not in content:
                categories["bugs"].append(f"L{line_num} {current_file}: Bare except — may catch SystemExit/KeyboardInterrupt")
            if re.search(r"=\s*==\s*", content):
                pass  # assignment in comparison is valid Python sometimes
            if content == "pass" and line_num > 1:
                categories["bugs"].append(f"L{line_num} {current_file}: Empty except/with block (pass)")

            # Performance
            if re.search(r"\.keys\(\)", content) and "redis" in content.lower():
                categories["performance"].append(f"L{line_num} {current_file}: Redis keys() — use scan_iter() for production")
            if re.search(r"for.*in.*\.all\(\)", content):
                categories["performance"].append(f"L{line_num} {current_file}: .all() in loop — consider batching")

            # Style
            if len(content) > 200:
                categories["style"].append(f"L{line_num} {current_file}: Line too long ({len(content)} chars)")
            if re.search(r"print\(", content) and "debug" not in content.lower():
                categories["style"].append(f"L{line_num} {current_file}: Use logging instead of print()")

            # Positive
            if re.search(r"@pytest|def test_", content):
                categories["positive"].append(f"L{line_num} {current_file}: Test coverage added")
            if re.search(r"logger\.(debug|info|warning|error)", content):
                categories["positive"].append(f"L{line_num} {current_file}: Proper logging")

    return categories


def format_review(pr_info: dict, findings: dict) -> str:
    total_issues = sum(len(v) for k, v in findings.items() if k != "positive")
    severity = "🔴 Critical" if findings["security"] or findings["bugs"] else "🟢 Looks Good"

    lines = [
        f"## 🤖 Automated Code Review\n",
        f"**PR:** {pr_info.get('title', 'N/A')}",
        f"**Files changed:** {pr_info.get('changedFiles', '?')}",
        f"**+{pr_info.get('additions', 0)}/-{pr_info.get('deletions', 0)}**\n",
        f"### Verdict: {severity} ({total_issues} issues found)\n",
    ]

    for category in ["security", "bugs", "performance", "style", "edge_cases"]:
        items = findings.get(category, [])
        if items:
            emoji = {"security": "🔒", "bugs": "🐛", "performance": "⚡", "style": "🎨", "edge_cases": "⚠️"}[category]
            lines.append(f"### {emoji} {category.replace('_', ' ').title()}\n")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    positives = findings.get("positive", [])
    if positives:
        lines.append(f"### ✅ Positive ({len(positives)})\n")
        for p in positives[:10]:
            lines.append(f"- {p}")
        lines.append("")

    return "\n".join(lines)


def post_comment(owner: str, repo: str, pr_number: int, body: str, token: Optional[str] = None):
    env = os.environ.copy()
    if token:
        env["GH_TOKEN"] = token
    result = subprocess.run(
        ["gh", "pr", "comment", str(pr_number), "--repo", f"{owner}/{repo}", "--body", body],
        env=env, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Failed to post comment: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"Review posted on {owner}/{repo}#{pr_number}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python review.py <pr-url> [--token TOKEN] [--post]", file=sys.stderr)
        sys.exit(1)

    pr_url = sys.argv[1]
    token = None
    should_post = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--token":
            token = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--post":
            should_post = True
            i += 1
        else:
            i += 1

    owner, repo, pr_number = parse_pr_url(pr_url)
    print(f"Reviewing {owner}/{repo}#{pr_number}...", file=sys.stderr)

    diff = get_pr_diff(owner, repo, pr_number)
    pr_info = get_pr_info(owner, repo, pr_number)
    findings = analyze_diff(diff)
    review = format_review(pr_info, findings)

    print(review)

    if should_post:
        post_comment(owner, repo, pr_number, review, token)


if __name__ == "__main__":
    main()
