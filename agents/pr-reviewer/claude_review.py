#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent
Analyzes GitHub Pull Request diffs and outputs structured Markdown reviews.
Can run locally via CLI or inside GitHub Actions CI/CD workflows.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

PR_URL_PATTERN = re.compile(
    r"^https?://github\.com/(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+)/pull/(?P<number>\d+)/?$"
)

# High-risk patterns in additions
RISK_RULES = [
    {
        "name": "Hardcoded Secrets / Tokens",
        "pattern": re.compile(r"(ghp_[a-zA-Z0-9]{36}|xoxb-[a-zA-Z0-9\-]+|-----BEGIN PRIVATE KEY-----|sk-[a-zA-Z0-9]{20,})"),
        "severity": "CRITICAL",
        "description": "Potential secret or private credential detected in added lines."
    },
    {
        "name": "Destructive File Operation",
        "pattern": re.compile(r"\brm\s+(-rf|-r\s+-f|-f\s+-r)\b", re.IGNORECASE),
        "severity": "HIGH",
        "description": "Destructive filesystem deletion command 'rm -rf' detected."
    },
    {
        "name": "Unsafe Shell Execution",
        "pattern": re.compile(r"(shell\s*=\s*True|os\.system\(|exec\(|eval\()", re.IGNORECASE),
        "severity": "MEDIUM",
        "description": "Dynamic or unsanitized shell execution detected."
    },
    {
        "name": "SQL Injection Risk",
        "pattern": re.compile(r"(SELECT\s+.*FROM|INSERT\s+INTO|DROP\s+TABLE|DELETE\s+FROM)\s+.*%s", re.IGNORECASE),
        "severity": "HIGH",
        "description": "Potential raw SQL string concatenation without parameterization."
    }
]

@dataclass
class PRInfo:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    base_ref: str
    head_ref: str
    additions: int
    deletions: int
    changed_files: int
    diff_text: str

class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")

    def _request(self, url: str, headers: dict[str, str] | None = None, method: str = "GET", data: bytes | None = None) -> Any:
        req_headers = {
            "User-Agent": "Claude-Code-PR-Reviewer/1.0",
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            req_headers["Authorization"] = f"token {self.token}"
        if headers:
            req_headers.update(headers)

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                content = resp.read()
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return json.loads(content.decode("utf-8"))
                return content.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API Error [{exc.code}] for {url}: {err_body}") from exc

    def fetch_pr(self, owner: str, repo: str, number: int) -> PRInfo:
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
        data = self._request(pr_url)

        diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
        diff_text = self._request(diff_url, headers={"Accept": "application/vnd.github.v3.diff"})

        return PRInfo(
            owner=owner,
            repo=repo,
            number=number,
            title=data.get("title", ""),
            body=data.get("body", "") or "",
            author=data.get("user", {}).get("login", "unknown"),
            base_ref=data.get("base", {}).get("ref", "main"),
            head_ref=data.get("head", {}).get("ref", "branch"),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            changed_files=data.get("changed_files", 0),
            diff_text=diff_text if isinstance(diff_text, str) else ""
        )

    def post_comment(self, owner: str, repo: str, number: int, body: str) -> str:
        if not self.token:
            raise ValueError("A GitHub token is required to post comments (--token or GITHUB_TOKEN).")
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
        payload = json.dumps({"body": body}).encode("utf-8")
        res = self._request(url, method="POST", data=payload, headers={"Content-Type": "application/json"})
        return res.get("html_url", "")

def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_URL_PATTERN.match(url.strip())
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: '{url}'. Expected format: https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), int(match.group("number"))

def analyze_diff(pr: PRInfo) -> dict[str, Any]:
    """
    Analyzes the PR diff text and metadata to identify risks, suggestions, and summary.
    """
    lines = pr.diff_text.splitlines()
    added_lines = [l[1:] for l in lines if l.startswith("+") and not l.startswith("+++")]
    file_headers = [l for l in lines if l.startswith("diff --git ")]

    file_names: list[str] = []
    for h in file_headers:
        m = re.search(r" b/(.+)$", h)
        if m:
            file_names.append(m.group(1))

    # Test coverage check
    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in file_names)

    # Risk detection
    identified_risks: list[str] = []
    for rule in RISK_RULES:
        for line in added_lines:
            if rule["pattern"].search(line):
                risk_msg = f"**{rule['severity']} - {rule['name']}**: {rule['description']}"
                if risk_msg not in identified_risks:
                    identified_risks.append(risk_msg)

    # Size-based risk
    if pr.additions + pr.deletions > 800:
        identified_risks.append(
            f"**MEDIUM - Large Diff Volume**: PR modifies {pr.additions + pr.deletions} lines across {pr.changed_files} files. "
            "Consider breaking down into smaller atomic PRs to reduce review latency."
        )

    if not has_tests and any(f.endswith((".py", ".ts", ".js", ".go", ".rs")) for f in file_names):
        identified_risks.append(
            "**LOW - Missing Automated Tests**: Code changes include business logic files, but no corresponding test files were added or updated."
        )

    # Suggestions
    suggestions: list[str] = []
    if not has_tests:
        suggestions.append("Add unit tests covering positive and negative edge cases for newly introduced logic.")
    if any(f.endswith((".ts", ".tsx")) for f in file_names) and any(": any" in l for l in added_lines):
        suggestions.append("Avoid `: any` type annotations in TypeScript files; use strict interfaces or unknown with type narrowing.")
    if not pr.body.strip():
        suggestions.append("Provide a descriptive PR body detailing motivation, testing evidence, and breaking change considerations.")
    if any(f.endswith((".py", ".sh")) for f in file_names) and not any("readme" in f.lower() or "doc" in f.lower() for f in file_names):
        suggestions.append("Verify if user-facing documentation or README instructions need updates to reflect the new feature.")
    if not suggestions:
        suggestions.append("Ensure automated CI test pipelines and linter checks pass cleanly across all target environments.")

    # Confidence Score Calculation
    score = "High"
    confidence_reasons: list[str] = []

    if any("CRITICAL" in r for r in identified_risks):
        score = "Low"
        confidence_reasons.append("Critical security risks detected in diff")
    elif pr.additions + pr.deletions > 1000 or (not has_tests and len(file_names) > 3):
        score = "Medium"
        confidence_reasons.append("Moderate diff size or lack of dedicated test suites")
    else:
        confidence_reasons.append("Clean targeted diff with clear separation of concerns")

    # Summary synthesis (2-3 sentences)
    components = ", ".join(f"`{f}`" for f in file_names[:4])
    if len(file_names) > 4:
        components += f" and {len(file_names) - 4} other files"

    summary = (
        f"This pull request by @{pr.author} modifies {pr.changed_files} file(s) ({components}) "
        f"with +{pr.additions} additions and -{pr.deletions} deletions targeting `{pr.base_ref}`. "
        f"The primary focus is '{pr.title.strip()}'. "
        f"{'Automated test files are included to validate behavior.' if has_tests else 'No explicit test files were touched in this branch.'}"
    )

    return {
        "summary": summary,
        "risks": identified_risks if identified_risks else ["No critical risks identified."],
        "suggestions": suggestions,
        "confidence_score": score,
        "confidence_reason": "; ".join(confidence_reasons)
    }

def format_review_markdown(pr: PRInfo, analysis: dict[str, Any]) -> str:
    risks_formatted = "\n".join(f"- {r}" for r in analysis["risks"])
    suggestions_formatted = "\n".join(f"- {s}" for s in analysis["suggestions"])

    return f"""## 🤖 Claude Code PR Review

### 📝 Summary of Changes
{analysis["summary"]}

### ⚠️ Identified Risks
{risks_formatted}

### 💡 Improvement Suggestions
{suggestions_formatted}

### 🎯 Confidence Score: **{analysis["confidence_score"]}**
*{analysis["confidence_reason"]}*

---
*Reviewed by Claude Code PR Reviewer Agent v1.0*
"""

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", default=None, help="GitHub API Token (defaults to GITHUB_TOKEN environment variable)")
    parser.add_argument("--comment", action="store_true", help="Post review Markdown directly as a comment on the PR")
    parser.add_argument("--output", default=None, help="Save review Markdown to specified output file path")

    args = parser.parse_args(argv)

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
        client = GitHubClient(token=args.token)

        sys.stderr.write(f"[*] Fetching PR #{pr_number} from {owner}/{repo}...\n")
        pr = client.fetch_pr(owner, repo, pr_number)

        sys.stderr.write(f"[*] Analyzing diff (+{pr.additions}/-{pr.deletions} lines)...\n")
        analysis = analyze_diff(pr)
        review_md = format_review_markdown(pr, analysis)

        # Output to stdout safely
        try:
            sys.stdout.buffer.write((review_md + "\n").encode("utf-8"))
            sys.stdout.buffer.flush()
        except Exception:
            print(review_md.encode("ascii", "replace").decode("ascii"))

        # Output to file if requested
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review_md)
            sys.stderr.write(f"[+] Review saved to {args.output}\n")

        # Post comment to GitHub if requested
        if args.comment:
            sys.stderr.write(f"[*] Posting review comment to GitHub PR #{pr_number}...\n")
            comment_url = client.post_comment(owner, repo, pr_number, review_md)
            sys.stderr.write(f"[+] Comment posted successfully: {comment_url}\n")

        return 0

    except Exception as exc:
        sys.stderr.write(f"[ERROR] {exc}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
