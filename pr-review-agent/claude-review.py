#!/usr/bin/env python3
"""
claude-review — PR Review Agent CLI

Fetches a GitHub PR diff, analyzes it, and outputs a structured Markdown review.
Works standalone (rule-based analysis) or with Claude API for deeper insights.

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123
    python3 claude-review.py --pr owner/repo/pull/123
    python3 claude-review.py --pr 123 --repo owner/repo
    python3 claude-review.py --pr 123 --repo owner/repo --format json
    python3 claude-review.py --pr 123 --repo owner/repo --post

Environment:
    GITHUB_TOKEN     — GitHub PAT (required for private repos, recommended for rate limits)
    ANTHROPIC_API_KEY — Claude API key (optional; enables AI-powered analysis)
"""

import argparse
import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ─── GitHub API ──────────────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"


def github_get(path: str, token: Optional[str] = None) -> dict:
    """GET request to GitHub API."""
    url = f"{GITHUB_API}{path}" if path.startswith("/") else path
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        if e.code == 404:
            print(f"Error: PR not found — {url}", file=sys.stderr)
        elif e.code == 403:
            print("Error: Rate limited. Set GITHUB_TOKEN to increase limits.", file=sys.stderr)
        else:
            print(f"Error: GitHub API returned {e.code}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: Network issue — {e.reason}", file=sys.stderr)
        sys.exit(1)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    # Full URL: https://github.com/owner/repo/pull/123
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    # Short: owner/repo/pull/123
    m = re.match(r"([^/]+)/([^/]+)/pull/(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    # Just number (needs --repo)
    m = re.match(r"(\d+)", url)
    if m:
        return "", "", int(m.group(1))
    print(f"Error: Cannot parse PR URL: {url}", file=sys.stderr)
    sys.exit(1)


# ─── PR Data Fetching ───────────────────────────────────────────────────────

@dataclass
class PRData:
    number: int
    title: str
    body: str
    author: str
    repo: str
    url: str
    state: str
    additions: int
    deletions: int
    changed_files: int
    diff_text: str
    files: list = field(default_factory=list)
    created_at: str = ""


def fetch_pr(owner: str, repo: str, number: int, token: Optional[str] = None) -> PRData:
    """Fetch PR metadata and diff from GitHub."""
    pr = github_get(f"/repos/{owner}/{repo}/pulls/{number}", token)
    diff_headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        diff_headers["Authorization"] = f"token {token}"
    diff_url = pr["url"]
    diff_req = Request(diff_url, headers=diff_headers)
    with urlopen(diff_req, timeout=30) as resp:
        diff_text = resp.read().decode("utf-8", errors="replace")

    files = github_get(f"/repos/{owner}/{repo}/pulls/{number}/files", token)

    return PRData(
        number=number,
        title=pr["title"],
        body=(pr.get("body") or "")[:2000],
        author=pr["user"]["login"],
        repo=f"{owner}/{repo}",
        url=pr["html_url"],
        state=pr["state"],
        additions=pr["additions"],
        deletions=pr["deletions"],
        changed_files=pr["changed_files"],
        diff_text=diff_text[:50000],  # cap at 50K chars
        files=[{
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "patch": f.get("patch", "")[:5000],
        } for f in files],
        created_at=pr["created_at"],
    )


# ─── Rule-Based Analysis ────────────────────────────────────────────────────

RISK_PATTERNS = [
    (r"\beval\s*\(", "Use of eval() — potential code injection risk"),
    (r"\bexec\s*\(", "Use of exec() — potential code injection risk"),
    (r"subprocess\.(?:call|run|Popen)\s*\(.*shell\s*=\s*True", "Shell=True in subprocess — command injection risk"),
    (r"os\.system\s*\(", "os.system() usage — prefer subprocess"),
    (r"(?:password|secret|token|api_key)\s*=\s*['\"]", "Hardcoded credentials detected"),
    (r"TODO|FIXME|HACK|XXX", "Unresolved TODO/FIXME comments"),
    (r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b.*\b(?:FROM|INTO|SET)\b", "Raw SQL — consider parameterized queries"),
    (r"except\s*:", "Bare except clause — may hide errors"),
    (r"print\s*\(", "Debug print statement (remove before production)"),
    (r"console\.log\s*\(", "Debug console.log (remove before production)"),
    (r"disable.*(?:eslint|lint|pylint|mypy)", "Linter suppression detected"),
    (r"pragma:\s*no\s*cover", "Test coverage exclusion"),
    (r"nosec|# nosec", "Security scan suppression"),
    (r"(?:rm\s+-rf|DROP\s+TABLE|DELETE\s+FROM)", "Destructive command in code"),
]

SUGGESTION_PATTERNS = [
    (r"except\s+Exception\s*:", "Consider catching more specific exceptions"),
    (r"open\s*\([^)]*\)\s*[^:]", "Consider using context manager (with statement) for file I/O"),
    (r"def\s+\w+\s*\([^)]*\)\s*->\s*None\s*:", "Function returns None explicitly — check if return value needed"),
    (r"(?:len\([^)]+\)\s*[=!]=\s*0|len\([^)]+\)\s*>\s*0)", "Consider using truthiness check instead of len() comparison"),
    (r"time\.sleep\s*\(", "Hardcoded sleep — consider polling or event-driven approach"),
    (r"(?:127\.0\.0\.1|localhost)", "Hardcoded localhost — consider making configurable"),
]


def analyze_rules(pr: PRData) -> dict:
    """Rule-based analysis of PR diff."""
    risks = []
    suggestions = []
    diff = pr.diff_text

    for pattern, message in RISK_PATTERNS:
        if re.search(pattern, diff, re.IGNORECASE):
            risks.append(message)

    for pattern, message in SUGGESTION_PATTERNS:
        if re.search(pattern, diff, re.IGNORECASE):
            suggestions.append(message)

    # Determine confidence based on size
    if pr.changed_files <= 3 and pr.additions + pr.deletions <= 100:
        confidence = "High"
    elif pr.changed_files <= 10 and pr.additions + pr.deletions <= 500:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Generate summary
    file_types = set()
    for f in pr.files:
        ext = os.path.splitext(f["filename"])[1]
        if ext:
            file_types.add(ext)

    summary_parts = []
    summary_parts.append(
        f"This PR modifies {pr.changed_files} file(s) with "
        f"+{pr.additions}/-{pr.deletions} lines."
    )
    if file_types:
        summary_parts.append(f"Changes span: {', '.join(sorted(file_types))}.")
    if pr.body:
        summary_parts.append(f"Purpose: {pr.body[:200].split(chr(10))[0]}")

    return {
        "summary": " ".join(summary_parts),
        "risks": risks if risks else ["No significant risks detected."],
        "suggestions": suggestions if suggestions else ["Code looks clean. No suggestions."],
        "confidence": confidence,
    }


# ─── Claude API Analysis ────────────────────────────────────────────────────

def analyze_with_claude(pr: PRData, api_key: str) -> Optional[dict]:
    """Use Claude API for deeper analysis. Returns None on failure."""
    prompt = f"""You are a senior code reviewer. Analyze this PR and respond in JSON.

PR: #{pr.number} — {pr.title}
Author: {pr.author}
Files changed: {pr.changed_files}, +{pr.additions}/-{pr.deletions}

Diff (truncated):
{pr.diff_text[:30000]}

Respond with ONLY valid JSON:
{{
  "summary": "2-3 sentence summary of changes",
  "risks": ["risk1", "risk2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "confidence": "Low|Medium|High"
}}"""

    try:
        data = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = Request("https://api.anthropic.com/v1/messages", data=data, headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        })
        with urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            text = result["content"][0]["text"]
            # Extract JSON from response
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group())
    except Exception as e:
        print(f"Note: Claude API analysis failed ({e}), using rule-based analysis.",
              file=sys.stderr)
    return None


# ─── Output Formatting ──────────────────────────────────────────────────────

def format_markdown(pr: PRData, analysis: dict, ai_powered: bool = False) -> str:
    """Format the review as structured Markdown."""
    method = "🤖 AI-powered (Claude)" if ai_powered else "⚙️ Rule-based"
    risks_md = "\n".join(f"- {r}" for r in analysis["risks"])
    suggestions_md = "\n".join(f"- {s}" for s in analysis["suggestions"])

    return f"""## 🔍 PR Review: #{pr.number} — {pr.title}

**Reviewer:** claude-review ({method})
**Date:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

### 📋 Summary of Changes

{analysis["summary"]}

### ⚠️ Identified Risks

{risks_md}

### 💡 Improvement Suggestions

{suggestions_md}

### 📊 Confidence Score: **{analysis["confidence"]}**

| Metric | Value |
|--------|-------|
| Files changed | {pr.changed_files} |
| Lines added | +{pr.additions} |
| Lines removed | -{pr.deletions} |
| Author | @{pr.author} |
| State | {pr.state} |

---

<sub>Generated by <a href="https://github.com/claude-builders-bounty/claude-builders-bounty">claude-review</a></sub>
"""


def format_json(pr: PRData, analysis: dict, ai_powered: bool = False) -> str:
    """Format as JSON."""
    return json.dumps({
        "pr_number": pr.number,
        "pr_title": pr.title,
        "pr_url": pr.url,
        "review": analysis,
        "method": "claude-api" if ai_powered else "rule-based",
        "timestamp": datetime.utcnow().isoformat(),
    }, indent=2)


# ─── GitHub Comment Posting ─────────────────────────────────────────────────

def post_comment(owner: str, repo: str, number: int, body: str, token: str) -> bool:
    """Post a review comment on a GitHub PR."""
    data = json.dumps({"body": body}).encode()
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments"
    req = Request(url, data=data, headers={
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
    })
    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            print(f"✅ Comment posted: {result.get('html_url', 'OK')}", file=sys.stderr)
            return True
    except HTTPError as e:
        print(f"Error posting comment: {e.code}", file=sys.stderr)
        return False


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PR Review Agent — analyze GitHub PRs and output structured reviews"
    )
    parser.add_argument("--pr", required=True, help="PR URL or number")
    parser.add_argument("--repo", help="owner/repo (required if --pr is a number)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                        help="Output format (default: markdown)")
    parser.add_argument("--post", action="store_true",
                        help="Post the review as a comment on the PR")
    parser.add_argument("--no-ai", action="store_true",
                        help="Skip Claude API, use rule-based analysis only")
    args = parser.parse_args()

    # Parse PR info
    owner, repo, number = parse_pr_url(args.pr)
    if not owner and args.repo:
        parts = args.repo.split("/")
        owner, repo = parts[0], parts[1]
    if not owner or not repo:
        print("Error: Cannot determine owner/repo. Use full URL or --repo flag.", file=sys.stderr)
        sys.exit(1)

    token = os.environ.get("GITHUB_TOKEN")
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    # Fetch PR
    print(f"Fetching PR #{number} from {owner}/{repo}...", file=sys.stderr)
    pr = fetch_pr(owner, repo, number, token)

    # Analyze
    ai_powered = False
    if api_key and not args.no_ai:
        print("Analyzing with Claude API...", file=sys.stderr)
        ai_result = analyze_with_claude(pr, api_key)
        if ai_result:
            analysis = ai_result
            ai_powered = True
        else:
            analysis = analyze_rules(pr)
    else:
        analysis = analyze_rules(pr)

    # Format output
    if args.format == "json":
        output = format_json(pr, analysis, ai_powered)
    else:
        output = format_markdown(pr, analysis, ai_powered)

    print(output)

    # Optionally post as comment
    if args.post:
        if not token:
            print("Error: GITHUB_TOKEN required to post comments.", file=sys.stderr)
            sys.exit(1)
        post_comment(owner, repo, number, output, token)


if __name__ == "__main__":
    main()
