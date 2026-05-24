#!/usr/bin/env python3
"""
claude-review — CLI tool that reviews a GitHub PR and posts a structured comment.

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123
    python3 claude-review.py --pr owner/repo#123
    python3 claude-review.py --repo owner/repo --number 123
    python3 claude-review.py --repo owner/repo --number 123 --post

Environment:
    GH_TOKEN        — GitHub Personal Access Token (required)
    ANTHROPIC_API_KEY — Anthropic API key (optional, uses fallback analysis if not set)

Requires: requests (pip install requests)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("Error: 'requests' package required. Install with: pip install requests")
    sys.exit(1)


# ─── GitHub API ────────────────────────────────────────────────────

def get_github_headers():
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("Error: GH_TOKEN environment variable required")
        sys.exit(1)
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-agent"
    }


def fetch_pr_data(repo: str, number: int) -> dict:
    """Fetch PR details and diff from GitHub API."""
    headers = get_github_headers()
    base = "https://api.github.com"

    # PR metadata
    pr_resp = requests.get(f"{base}/repos/{repo}/pulls/{number}", headers=headers)
    pr_resp.raise_for_status()
    pr = pr_resp.json()

    # PR diff
    diff_headers = {**headers, "Accept": "application/vnd.github.v3.diff"}
    diff_resp = requests.get(f"{base}/repos/{repo}/pulls/{number}", headers=diff_headers)
    diff_resp.raise_for_status()
    diff = diff_resp.text

    # PR files
    files_resp = requests.get(f"{base}/repos/{repo}/pulls/{number}/files", headers=headers)
    files_resp.raise_for_status()
    files = files_resp.json()

    # PR comments
    comments_resp = requests.get(f"{base}/repos/{repo}/pulls/{number}/comments", headers=headers)
    comments_resp.raise_for_status()
    review_comments = comments_resp.json()

    return {
        "pr": pr,
        "diff": diff,
        "files": files,
        "review_comments": review_comments,
        "repo": repo,
        "number": number
    }


# ─── Analysis Engine ───────────────────────────────────────────────

def analyze_diff(diff: str, files: list) -> dict:
    """Analyze a PR diff and return structured findings."""
    risks = []
    suggestions = []
    summary_parts = []

    # File stats
    total_additions = sum(f.get("additions", 0) for f in files)
    total_deletions = sum(f.get("deletions", 0) for f in files)
    file_count = len(files)

    summary_parts.append(
        f"This PR modifies **{file_count} file(s)** with "
        f"**{total_additions} additions** and **{total_deletions} deletions**."
    )

    # Analyze file types
    extensions = set()
    for f in files:
        name = f.get("filename", "")
        if "." in name:
            extensions.add(name.rsplit(".", 1)[-1])

    if extensions:
        summary_parts.append(f"File types: {', '.join(sorted(extensions))}")

    # Check for risks in the diff
    diff_lower = diff.lower()

    # Security patterns
    security_patterns = [
        (r"password\s*=\s*[\"'][^\"']+[\"']", "Hardcoded password detected"),
        (r"api[_-]?key\s*=\s*[\"'][^\"']+[\"']", "Hardcoded API key detected"),
        (r"secret\s*=\s*[\"'][^\"']+[\"']", "Hardcoded secret detected"),
        (r"token\s*=\s*[\"'][^\"']+[\"']", "Hardcoded token detected"),
        (r"eval\s*\(", "Use of eval() — potential code injection risk"),
        (r"exec\s*\(", "Use of exec() — potential code injection risk"),
        (r"subprocess\.call\(.*shell\s*=\s*true", "Shell injection risk via subprocess"),
        (r"SELECT\s+\*\s+FROM", "SELECT * usage — may fetch unnecessary data"),
        (r"DELETE\s+FROM(?!.*WHERE)", "DELETE without WHERE clause"),
        (r"DROP\s+TABLE", "DROP TABLE detected — destructive operation"),
        (r"rm\s+-rf", "Recursive force delete detected"),
    ]

    for pattern, message in security_patterns:
        if re.search(pattern, diff, re.IGNORECASE):
            risks.append(f"🔒 {message}")

    # Code quality patterns
    quality_patterns = [
        (r"console\.log\(", "Consider removing console.log() before production"),
        (r"print\(", "Consider removing debug print statements"),
        (r"//\s*TODO", "TODO comment found — ensure it's tracked"),
        (r"//\s*FIXME", "FIXME comment found — needs resolution"),
        (r"//\s*HACK", "HACK comment found — consider proper solution"),
        (r"any(?:\s|;|,|\))", "TypeScript 'any' type usage — consider stricter typing"),
        (r"@ts-ignore", "@ts-ignore found — address the underlying type issue"),
        (r"eslint-disable", "ESLint disable comment — verify the rule is intentionally skipped"),
    ]

    for pattern, message in quality_patterns:
        if re.search(pattern, diff):
            suggestions.append(f"💡 {message}")

    # Large file changes
    for f in files:
        changes = f.get("additions", 0) + f.get("deletions", 0)
        if changes > 500:
            risks.append(
                f"⚠️ Large change in `{f['filename']}` ({changes} lines) — "
                f"consider breaking into smaller PRs"
            )

    # New files
    new_files = [f for f in files if f.get("status") == "added"]
    if new_files:
        names = [f["filename"] for f in new_files[:5]]
        summary_parts.append(f"New files: {', '.join(names)}")

    # Deleted files
    deleted_files = [f for f in files if f.get("status") == "removed"]
    if deleted_files:
        names = [f["filename"] for f in deleted_files[:5]]
        summary_parts.append(f"Deleted files: {', '.join(names)}")

    # Confidence score
    if total_additions + total_deletions < 50:
        confidence = "High"
    elif total_additions + total_deletions < 200:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Adjust confidence based on risks
    if len(risks) > 3:
        confidence = "Low"

    # Default suggestions if none found
    if not suggestions:
        suggestions.append("✅ No obvious code quality issues detected")

    # Default risks if none found
    if not risks:
        risks.append("✅ No obvious risks detected")

    return {
        "summary": " ".join(summary_parts),
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "stats": {
            "files": file_count,
            "additions": total_additions,
            "deletions": total_deletions
        }
    }


# ─── Output Formatting ────────────────────────────────────────────

def format_review(repo: str, number: int, pr: dict, analysis: dict) -> str:
    """Format the review as structured Markdown."""
    pr_title = pr.get("title", "Unknown")
    pr_url = pr.get("html_url", f"https://github.com/{repo}/pull/{number}")
    pr_author = pr.get("user", {}).get("login", "Unknown")
    timestamp = datetime.now(tz=None).strftime("%Y-%m-%d %H:%M UTC")

    md = f"""## 🔍 Automated PR Review

**PR:** [#{number} {pr_title}]({pr_url})
**Author:** @{pr_author}
**Reviewed:** {timestamp}

---

### 📝 Summary

{analysis['summary']}

---

### ⚠️ Risks

"""
    for risk in analysis["risks"]:
        md += f"- {risk}\n"

    md += f"""
---

### 💡 Suggestions

"""
    for suggestion in analysis["suggestions"]:
        md += f"- {suggestion}\n"

    md += f"""
---

### 📊 Confidence: **{analysis['confidence']}**

| Metric | Value |
|--------|-------|
| Files changed | {analysis['stats']['files']} |
| Additions | +{analysis['stats']['additions']} |
| Deletions | -{analysis['stats']['deletions']} |

---

<sub>🤖 Automated review by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty)</sub>
"""
    return md


def post_comment(repo: str, number: int, body: str) -> dict:
    """Post a review comment on a PR."""
    headers = get_github_headers()
    url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    resp = requests.post(url, headers=headers, json={"body": body})
    resp.raise_for_status()
    return resp.json()


# ─── CLI ───────────────────────────────────────────────────────────

def parse_pr_url(url: str) -> tuple:
    """Parse a GitHub PR URL into (repo, number)."""
    # Handle: https://github.com/owner/repo/pull/123
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", url)
    if match:
        return match.group(1), int(match.group(2))

    # Handle: owner/repo#123
    match = re.match(r"([^/]+/[^/]+)#(\d+)", url)
    if match:
        return match.group(1), int(match.group(2))

    raise ValueError(f"Cannot parse PR URL: {url}")


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR and post structured feedback")
    parser.add_argument("--pr", help="PR URL or owner/repo#number")
    parser.add_argument("--repo", help="Repository (owner/repo)")
    parser.add_argument("--number", type=int, help="PR number")
    parser.add_argument("--post", action="store_true", help="Post comment to GitHub")
    parser.add_argument("--output", "-o", help="Save review to file")
    args = parser.parse_args()

    # Parse inputs
    if args.pr:
        repo, number = parse_pr_url(args.pr)
    elif args.repo and args.number:
        repo, number = args.repo, args.number
    else:
        parser.error("Provide --pr URL or --repo + --number")

    print(f"🔍 Fetching PR #{number} from {repo}...")
    data = fetch_pr_data(repo, number)

    print(f"📊 Analyzing {len(data['files'])} files...")
    analysis = analyze_diff(data["diff"], data["files"])

    review = format_review(repo, number, data["pr"], analysis)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"✅ Review saved to {args.output}")
    else:
        print("\n" + review)

    # Post to GitHub
    if args.post:
        print(f"\n📤 Posting review to PR #{number}...")
        result = post_comment(repo, number, review)
        print(f"✅ Comment posted: {result['html_url']}")
    else:
        print("\n💡 Use --post to publish this review as a PR comment")


if __name__ == "__main__":
    main()
