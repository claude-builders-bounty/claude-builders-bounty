#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent.

Takes a PR URL, fetches the diff via GitHub API, analyzes it,
and outputs a structured Markdown review.

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --post
"""

import argparse
import json
import os
import re
import subprocess
import sys


def curl_get(url: str, token: str = "") -> str:
    """HTTP GET via curl (avoids Python SSL cert issues)."""
    cmd = ["curl", "-s", "-H", "Accept: application/vnd.github.v3+json"]
    if token:
        cmd += ["-H", f"Authorization: token {token}"]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def curl_post(url: str, data: str, token: str) -> str:
    """HTTP POST via curl."""
    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", f"Authorization: token {token}",
        "-H", "Accept: application/vnd.github.v3+json",
        "-H", "Content-Type: application/json",
        "-d", data,
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def parse_pr_url(url: str) -> tuple:
    """Extract owner, repo, and PR number from a GitHub PR URL."""
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not match:
        print(f"Error: Invalid PR URL: {url}", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_info(owner: str, repo: str, pr_number: int, token: str = "") -> dict:
    """Fetch PR metadata and diff from GitHub API."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    raw = curl_get(api_url, token)
    if not raw:
        print(f"Error fetching PR: empty response", file=sys.stderr)
        sys.exit(1)
    data = json.loads(raw)

    # Fetch diff via API with Accept header (avoids github.com direct access)
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    diff_cmd = ["curl", "-s", "-H", "Accept: application/vnd.github.v3.diff"]
    if token:
        diff_cmd += ["-H", f"Authorization: token {token}"]
    diff_cmd.append(diff_url)
    diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
    diff = diff_result.stdout

    return {
        "title": data.get("title", ""),
        "body": data.get("body", ""),
        "user": data.get("user", {}).get("login", ""),
        "base": data.get("base", {}).get("ref", ""),
        "head": data.get("head", {}).get("ref", ""),
        "additions": data.get("additions", 0),
        "deletions": data.get("deletions", 0),
        "changed_files": data.get("changed_files", 0),
        "commits": data.get("commits", 0),
        "diff": diff,
    }


def analyze_diff(diff: str, pr_info: dict) -> dict:
    """Analyze the PR diff and produce structured review."""

    files = []
    current_file = None
    current_hunks = []

    for line in diff.split("\n"):
        if line.startswith("diff --git"):
            if current_file:
                files.append({"file": current_file, "hunks": current_hunks})
            current_file = line.split(" b/")[-1] if " b/" in line else ""
            current_hunks = []
        elif line.startswith("@@"):
            current_hunks.append({"header": line, "lines": []})
        elif current_hunks:
            current_hunks[-1]["lines"].append(line)

    if current_file:
        files.append({"file": current_file, "hunks": current_hunks})

    # Detect risks
    risks = []
    suggestions = []

    for f in files:
        fname = f["file"]
        all_lines = "\n".join(
            line for hunk in f["hunks"] for line in hunk["lines"]
        )

        # Security risks
        if re.search(r'\b(eval|exec)\s*\(', all_lines):
            risks.append(f"**{fname}**: Use of `eval`/`exec` — potential code injection risk")

        if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b.*\+\s*str\(', all_lines, re.IGNORECASE):
            risks.append(f"**{fname}**: Possible SQL injection — string concatenation in query")

        if re.search(r'(password|secret|api_key|token)\s*=\s*["\']', all_lines, re.IGNORECASE):
            risks.append(f"**{fname}**: Hardcoded credential detected")

        if re.search(r'\binnerHTML\b', all_lines):
            risks.append(f"**{fname}**: Use of `innerHTML` — potential XSS")

        # Code quality
        if re.search(r'console\.log|print\(', all_lines) and not fname.endswith(".test.py"):
            suggestions.append(f"**{fname}**: Remove debug statements (console.log/print)")

        if re.search(r'TODO|FIXME|HACK|XXX', all_lines):
            suggestions.append(f"**{fname}**: Contains TODO/FIXME — resolve before merge")

        if re.search(r'catch\s*\([^)]*\)\s*\{[^}]*\}', all_lines) or re.search(r'except\s*:\s*pass', all_lines):
            risks.append(f"**{fname}**: Empty or silent exception handler — errors will be hidden")

        # File-specific checks
        if fname.endswith(".py"):
            if not re.search(r'def |class ', all_lines) and len(all_lines) > 500:
                suggestions.append(f"**{fname}**: Large procedural block — consider extracting functions")
        elif fname.endswith((".tsx", ".jsx")):
            if re.search(r'useEffect\(\s*\(\)\s*=>\s*\{', all_lines) and not re.search(r'return\s*\(\)\s*=>', all_lines):
                suggestions.append(f"**{fname}**: useEffect missing cleanup function")
        elif fname.endswith((".sql",)):
            if re.search(r'\bDROP\s+(TABLE|DATABASE)\b', all_lines, re.IGNORECASE):
                risks.append(f"**{fname}**: DROP statement in migration — irreversible without rollback")

        # Large diff check
        added = sum(1 for hunk in f["hunks"] for l in hunk["lines"] if l.startswith("+") and not l.startswith("+++"))
        if added > 300:
            suggestions.append(f"**{fname}**: {added} lines added — consider splitting into smaller PRs")

    # Determine confidence
    total_additions = pr_info.get("additions", 0)
    total_deletions = pr_info.get("deletions", 0)
    total_changed = total_additions + total_deletions

    if total_changed < 50:
        confidence = "High"
    elif total_changed < 500:
        confidence = "Medium"
    else:
        confidence = "Low"

    if not risks:
        confidence = "High"

    # Build summary
    summary = (
        f"This PR {'adds' if total_additions > total_deletions else 'modifies'} "
        f"{pr_info.get('changed_files', 0)} file(s) "
        f"(+{total_additions}/-{total_deletions}) "
        f"across {pr_info.get('commits', 0)} commit(s). "
    )

    if pr_info.get("title"):
        summary += f"The changes: \"{pr_info['title']}\"."

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files_changed": len(files),
        "file_list": [f["file"] for f in files],
    }


def format_review(analysis: dict, pr_info: dict) -> str:
    """Format the analysis as a structured Markdown review."""
    md = []
    md.append(f"## PR Review: {pr_info.get('title', 'Untitled')}\n")
    md.append(f"**Author:** {pr_info.get('user', 'unknown')}  ")
    md.append(f"**Branch:** `{pr_info.get('base', '')}` ← `{pr_info.get('head', '')}`  ")
    md.append(f"**Files changed:** {analysis['files_changed']}  ")
    md.append(f"**+{pr_info.get('additions', 0)}/-{pr_info.get('deletions', 0)}**\n")

    md.append("### Summary\n")
    md.append(f"{analysis['summary']}\n")

    md.append("### Files Changed\n")
    for f in analysis["file_list"]:
        md.append(f"- `{f}`")
    md.append("")

    md.append("### Identified Risks\n")
    if analysis["risks"]:
        for r in analysis["risks"]:
            md.append(f"- {r}")
    else:
        md.append("- No significant risks detected.")
    md.append("")

    md.append("### Improvement Suggestions\n")
    if analysis["suggestions"]:
        for s in analysis["suggestions"]:
            md.append(f"- {s}")
    else:
        md.append("- No specific suggestions. Code looks clean.")
    md.append("")

    md.append("### Confidence Score\n")
    md.append(f"**{analysis['confidence']}**\n")

    if analysis["confidence"] == "Low":
        md.append("> Low confidence due to large diff size. Manual review recommended.\n")

    return "\n".join(md)


def post_comment(owner: str, repo: str, pr_number: int, body: str, token: str):
    """Post the review as a comment on the PR."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    data = json.dumps({"body": body})
    raw = curl_post(api_url, data, token)
    result = json.loads(raw)
    print(f"Review posted: {result.get('html_url', '')}")


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--post", action="store_true", help="Post review as PR comment")
    parser.add_argument("--output", default="", help="Write review to file")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")

    owner, repo, pr_number = parse_pr_url(args.pr)
    pr_info = fetch_pr_info(owner, repo, pr_number, token)

    if not pr_info["diff"]:
        print("Error: Could not fetch PR diff", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_diff(pr_info["diff"], pr_info)
    review = format_review(analysis, pr_info)

    print(review)

    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"\nReview written to {args.output}")

    if args.post:
        if not token:
            print("Error: GITHUB_TOKEN not set — cannot post comment", file=sys.stderr)
            sys.exit(1)
        post_comment(owner, repo, pr_number, review, token)


if __name__ == "__main__":
    main()
