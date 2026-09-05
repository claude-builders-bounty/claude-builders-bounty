#!/usr/bin/env python3
"""
Claude Code PR Review Agent
Reviews GitHub PRs and posts structured Markdown comments.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path


def get_github_token():
    """Get GitHub token from environment or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: No GitHub token found. Set GITHUB_TOKEN or run 'gh auth login'.", file=sys.stderr)
        sys.exit(1)


def parse_pr_url(pr_url):
    """Parse owner/repo/pull/number from a PR URL."""
    patterns = [
        r"github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        r"^([^/]+)/([^/]+)/(\d+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, pr_url)
        if match:
            return match.group(1), match.group(2), int(match.group(3))
    print(f"Error: Invalid PR URL: {pr_url}", file=sys.stderr)
    sys.exit(1)


def fetch_pr_info(owner, repo, pr_number, token):
    """Fetch PR metadata and diff from GitHub API."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Fetch PR metadata
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(pr_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            pr_data = json.loads(response.read())
    except urllib.error.URLError as e:
        print(f"Error fetching PR: {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch PR diff
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(diff_url, headers={**headers, "Accept": "application/vnd.github.v3.diff"})
    try:
        with urllib.request.urlopen(req) as response:
            diff = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"Error fetching diff: {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch PR files
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    req = urllib.request.Request(files_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            files = json.loads(response.read())
    except urllib.error.URLError as e:
        print(f"Error fetching files: {e}", file=sys.stderr)
        sys.exit(1)

    return pr_data, diff, files


def analyze_pr(pr_data, diff, files):
    """Analyze PR and generate structured review."""
    title = pr_data.get("title", "Unknown")
    body = pr_data.get("body", "") or ""
    author = pr_data.get("user", {}).get("login", "Unknown")
    changed_files = len(files)
    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)
    file_names = [f.get("filename", "") for f in files]

    # Generate summary
    summary = f"PR by @{author}: {title}. "
    summary += f"Changes {changed_files} file(s) with +{additions}/-{deletions} lines. "
    if body:
        summary += f"Description: {body[:200]}{'...' if len(body) > 200 else ''}"

    # Identify risks
    risks = []
    if additions > 500:
        risks.append(f"Large PR with {additions} additions — consider splitting")
    if deletions > 200:
        risks.append(f"Significant deletions ({deletions} lines) — verify no critical code removed")
    if any("test" not in f.lower() for f in file_names) and not any("test" in f.lower() for f in file_names):
        risks.append("No test files modified — consider adding tests")
    if any(f.endswith(".env") or f.endswith(".env.local") for f in file_names):
        risks.append("Environment files modified — ensure no secrets committed")
    if any("security" in f.lower() or "auth" in f.lower() for f in file_names):
        risks.append("Security-related files modified — thorough review recommended")
    if any(f.endswith((".yml", ".yaml")) for f in file_names):
        risks.append("CI/CD configuration changed — verify pipeline compatibility")
    if not risks:
        risks.append("No major risks identified")

    # Generate suggestions
    suggestions = []
    if additions > 200:
        suggestions.append("Consider breaking this PR into smaller, focused PRs")
    if not any("test" in f.lower() for f in file_names):
        suggestions.append("Add unit tests for new functionality")
    if "TODO" in diff or "FIXME" in diff or "HACK" in diff:
        suggestions.append("Address TODO/FIXME comments before merging")
    if any(f.endswith(".md") for f in file_names):
        suggestions.append("Verify documentation is accurate and complete")
    if "import" in diff and "unused" in diff.lower():
        suggestions.append("Remove unused imports")
    if not suggestions:
        suggestions.append("Code looks good — ready for review")

    # Confidence score
    risk_count = len([r for r in risks if "risk" not in r.lower()])
    if risk_count == 0 and additions < 100:
        confidence = "High"
    elif risk_count <= 2 and additions < 300:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "stats": {
            "files_changed": changed_files,
            "additions": additions,
            "deletions": deletions,
        },
    }


def format_review(review):
    """Format review as structured Markdown."""
    lines = [
        "## 🤖 AI Code Review",
        "",
        "### Summary",
        review["summary"],
        "",
        "### Identified Risks",
    ]
    for risk in review["risks"]:
        lines.append(f"- ⚠️ {risk}")
    lines.append("")
    lines.append("### Improvement Suggestions")
    for suggestion in review["suggestions"]:
        lines.append(f"- 💡 {suggestion}")
    lines.append("")
    lines.append(f"### Confidence Score: **{review['confidence']}**")
    lines.append("")
    lines.append("---")
    lines.append(f"*Files: {review['stats']['files_changed']} | +{review['stats']['additions']}/-{review['stats']['deletions']}*")
    return "\n".join(lines)


def post_comment(owner, repo, pr_number, comment_body, token):
    """Post a comment on the PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    data = json.dumps({"body": comment_body}).encode("utf-8")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            print(f"Comment posted: {result.get('html_url', 'Success')}")
            return result
    except urllib.error.URLError as e:
        print(f"Error posting comment: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Agent")
    parser.add_argument("pr_url", help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--dry-run", action="store_true", help="Print review without posting")
    parser.add_argument("--output", type=str, help="Save review to file")
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr_url)
    token = get_github_token()

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...")
    pr_data, diff, files = fetch_pr_info(owner, repo, pr_number, token)

    print("Analyzing PR...")
    review = analyze_pr(pr_data, diff, files)

    comment = format_review(review)

    if args.output:
        Path(args.output).write_text(comment, encoding="utf-8")
        print(f"Review saved to {args.output}")

    if args.dry_run:
        print("\n--- Review (dry run) ---\n")
        sys.stdout.buffer.write(comment.encode("utf-8"))
        print()
    else:
        print("Posting comment...")
        post_comment(owner, repo, pr_number, comment, token)

    print("Done!")


if __name__ == "__main__":
    main()
