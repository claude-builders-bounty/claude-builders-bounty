#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent
Analyzes Pull Request diffs and outputs structured Markdown code reviews including:
- Summary of Changes (2-3 sentences)
- Identified Risks
- Improvement Suggestions
- Confidence Score (Low / Medium / High)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parses owner, repo, and PR number from a GitHub PR URL."""
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url.strip())
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}. Expected format: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))

def fetch_pr_data(owner: str, repo: str, pr_number: int, token: str | None = None) -> tuple[dict, str]:
    """Fetches PR metadata and unified diff from GitHub API."""
    headers = {
        "User-Agent": "Claude-Code-PR-Reviewer/1.0",
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 1. Fetch PR metadata
    meta_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(meta_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            pr_meta = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to fetch PR metadata from {meta_url} ({e.code}): {e.reason}")

    # 2. Fetch diff
    diff_headers = headers.copy()
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    diff_req = urllib.request.Request(meta_url, headers=diff_headers)
    try:
        with urllib.request.urlopen(diff_req) as resp:
            diff_text = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to fetch PR diff from {meta_url} ({e.code}): {e.reason}")

    return pr_meta, diff_text

def analyze_diff(pr_meta: dict, diff_text: str) -> dict:
    """
    Performs static analysis on the diff to identify changes, potential risks,
    and constructive improvement suggestions.
    """
    title = pr_meta.get("title", "")
    body = pr_meta.get("body", "") or ""
    changed_files = pr_meta.get("changed_files", 0)
    additions = pr_meta.get("additions", 0)
    deletions = pr_meta.get("deletions", 0)

    # Risk signals
    risks = []
    suggestions = []

    # Check for destructive or sensitive keywords in added lines
    added_lines = [line[1:] for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed_lines = [line[1:] for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---")]

    added_content = "\n".join(added_lines)

    # 1. Check for hardcoded secrets
    if re.search(r'(api_key|secret|password|token|bearer)\s*[:=]\s*["\'][a-zA-Z0-9_\-\.]{12,}["\']', added_content, re.IGNORECASE):
        risks.append("Potential hardcoded credential or API secret detected in diff additions.")
        suggestions.append("Move sensitive keys to environment variables (`process.env` / `os.environ`).")

    # 2. Check for missing error handling in async / promise / HTTP calls
    if re.search(r'\bawait\b', added_content) and not re.search(r'\btry\s*\{|\.catch\(', added_content):
        risks.append("Asynchronous operations introduced without local error handling (`try/catch` or `.catch()`).")
        suggestions.append("Wrap asynchronous calls with error handling or ensure rejection is handled upstream.")

    # 3. Check for SQL Injection risks
    if re.search(r'(execute|query)\s*\(\s*f["\']|`[^`]*\$\{[^}]+\}[^`]*`', added_content, re.IGNORECASE) and re.search(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', added_content, re.IGNORECASE):
        risks.append("Potential raw SQL string interpolation detected. Risks SQL injection.")
        suggestions.append("Use parameterized queries or ORM query builder abstractions instead of string concatenation.")

    # 4. Check for test coverage
    has_tests = any("test" in line.lower() or "spec" in line.lower() for line in diff_text.splitlines() if line.startswith("diff --git"))
    if not has_tests and (additions > 30):
        risks.append("Significant logic additions without corresponding unit or integration test updates.")
        suggestions.append("Add unit test coverage for new business logic paths.")

    # 5. Check for large diff size
    if changed_files > 15 or (additions + deletions > 500):
        risks.append(f"Large changeset ({changed_files} files, +{additions}/-{deletions} lines). Increases regression surface area.")
        suggestions.append("Consider breaking large feature changes into smaller, incremental PRs.")

    # General suggestions if none triggered
    if not suggestions:
        suggestions.append("Ensure type definitions and exported API signatures are fully documented.")
        suggestions.append("Verify CI build and lint passes cleanly on all target platforms.")

    if not risks:
        risks.append("No critical security or architectural blockers identified in this diff.")

    # Confidence calculation
    if len(risks) <= 1 and (has_tests or additions < 50):
        confidence = "High"
    elif len(risks) <= 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    # 2-3 sentence summary
    summary = (
        f"This pull request ({title}) modifies {changed_files} file(s) with +{additions} additions and -{deletions} deletions. "
        f"The changes focus on {title.lower().replace('fix:', '').replace('feat:', '').strip()}. "
        f"Overall code structure appears {'clean and well-targeted' if confidence == 'High' else 'functional but requires attention to identified risks'}."
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "pr_title": title,
        "pr_number": pr_meta.get("number"),
        "author": pr_meta.get("user", {}).get("login", "author")
    }

def format_review_markdown(analysis: dict) -> str:
    """Renders the analysis into clean, structured GitHub Markdown."""
    risks_md = "\n".join(f"- ⚠️ {r}" if "No critical" not in r else f"- ✅ {r}" for r in analysis["risks"])
    suggestions_md = "\n".join(f"- 💡 {s}" for s in analysis["suggestions"])

    badge_color = "brightgreen" if analysis["confidence"] == "High" else ("yellow" if analysis["confidence"] == "Medium" else "red")

    markdown = f"""## 🤖 Claude Code PR Review

### 📝 Summary of Changes
{analysis["summary"]}

---

### 🔍 Identified Risks
{risks_md}

---

### 💡 Improvement Suggestions
{suggestions_md}

---

### 📊 Review Metadata
- **Confidence Score**: **{analysis["confidence"]}**
- **Reviewer**: `claude-code-pr-reviewer`
"""
    return markdown.strip() + "\n"

def post_github_comment(owner: str, repo: str, pr_number: int, comment_body: str, token: str):
    """Posts the formatted review as a comment on the PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Claude-Code-PR-Reviewer/1.0",
        "Content-Type": "application/json"
    }
    data = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Successfully posted review comment on PR #{pr_number} (Status: {resp.status})")
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to post comment ({e.code}): {e.reason}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--post-comment", action="store_true", help="Post review directly as a comment on GitHub")
    parser.add_argument("--token", help="GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)")
    parser.add_argument("--output", help="Path to save output Markdown file")

    args = parser.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
        pr_meta, diff_text = fetch_pr_data(owner, repo, pr_number, token)
        analysis = analyze_diff(pr_meta, diff_text)
        review_md = format_review_markdown(analysis)

        print(review_md)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review_md)
            print(f"📁 Review saved to {args.output}")

        if args.post_comment:
            if not token:
                print("❌ Cannot post comment without GitHub token (--token or GITHUB_TOKEN).", file=sys.stderr)
                sys.exit(1)
            post_github_comment(owner, repo, pr_number, review_md, token)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
