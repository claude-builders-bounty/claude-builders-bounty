#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claude-review — Claude Code PR reviewer sub-agent.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123

Fetches a public PR diff via the GitHub REST API (no auth required for public
repos), analyzes it, and prints a structured Markdown review comment to stdout:
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

Read-only: never writes to the PR, never mutates the repository.
"""
import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from typing import Dict, List, Tuple


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Extract (owner, repo, pull_number) from a GitHub PR URL."""
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid GitHub PR URL format: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def _get(url: str) -> Dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "claude-review/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_pr(owner: str, repo: str, pull_number: int) -> Dict:
    return _get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}")


def fetch_pr_files(owner: str, repo: str, pull_number: int) -> List[Dict]:
    """Fetch PR files (includes unified `patch` per file)."""
    return _get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files")


def classify_risk(diff_text: str) -> List[str]:
    """Heuristic risk identification from the unified diff."""
    risks: List[str] = []
    low = diff_text.lower()

    if re.search(r"(secret|password|api_key|token|private_key)", low):
        risks.append("Possible hardcoded secret (password/api_key/token/private_key). Use env vars or secret management instead.")
    if re.search(r"\b(eval|exec|system|popen|subprocess)\b", low):
        risks.append("Dynamic code execution call (eval/exec/system/popen/subprocess). Confirm input is strictly validated.")
    if re.search(r"\b(DELETE|UPDATE|INSERT|DROP|TRUNCATE)\b", low):
        risks.append("Destructive SQL operation (DELETE/UPDATE/INSERT/DROP/TRUNCATE). Confirm a WHERE clause and backups.")
    if re.search(r"\b(rm -rf|unlink)\b", low):
        risks.append("Destructive file deletion (rm -rf/unlink). Add protection checks and backup confirmation.")
    if re.search(r"(http|fetch|axios|requests)", low):
        risks.append("Outbound network request detected. Add timeouts, retries, and response validation.")

    if not risks:
        risks.append("No obvious high-risk patterns detected (heuristic scan only).")
    return risks


def suggest_improvements(diff_text: str, files: List[Dict]) -> List[str]:
    """Generate improvement suggestions from the diff."""
    suggestions: List[str] = []
    added_lines = [l for l in diff_text.splitlines() if l.startswith("+") and not l.startswith("+++")]
    added_text = "\n".join(added_lines)

    if any(f.get("filename", "").endswith((".ts", ".tsx")) for f in files):
        suggestions.append("TypeScript files present — consider strict typing and avoid `any`.")
    if "test" in added_text.lower() or "__tests__" in diff_text:
        suggestions.append("Test changes detected — pair with unit/integration tests.")
    if any("api" in f.get("filename", "").lower() for f in files):
        suggestions.append("API files changed — consider Zod/input validation and proper error responses.")
    if re.search(r"(console\.log|print|debugger)", added_text):
        suggestions.append("Debug output found (console.log/print/debugger). Remove or use structured logging.")

    if not suggestions:
        suggestions.append("Code looks clean. No specific improvement suggestions.")
    return suggestions


def confidence_score(risks: List[str], files: List[Dict], additions: int) -> str:
    """Low / Medium / High confidence."""
    high_risk = any(r.startswith(("Possible hardcoded", "Dynamic code execution", "Destructive SQL", "Destructive file")) for r in risks)
    if high_risk or additions > 500 or len(files) > 10:
        return "Low"
    if additions > 100 or len(files) > 3:
        return "Medium"
    return "High"


def build_review(pr: Dict, files: List[Dict]) -> str:
    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)
    diff_text = "\n".join(f.get("patch", "") or "" for f in files)
    risks = classify_risk(diff_text)
    suggestions = suggest_improvements(diff_text, files)
    confidence = confidence_score(risks, files, additions)

    title = pr.get("title", "")
    body = pr.get("body") or ""
    changed = [f.get("filename", "") for f in files][:12]

    lines: List[str] = []
    lines.append("## PR Review Summary")
    lines.append("")
    lines.append(f"- **PR**: #{pr.get('number')} {title}")
    lines.append(f"- **Repo**: {pr.get('base', {}).get('repo', {}).get('full_name', '')}")
    lines.append(f"- **Files**: {len(files)} | **Additions**: {additions} | **Deletions**: {deletions}")
    lines.append("")
    lines.append("### Summary of Changes")
    lines.append("")
    summary = (body[:400] + ("..." if len(body) > 400 else "")) if body else "No PR body; reviewed diff only."
    lines.append(summary)
    lines.append("")
    lines.append("### Changed Files (first 12)")
    lines.append("")
    for f in changed:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("### Identified Risks")
    lines.append("")
    for r in risks:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("### Improvement Suggestions")
    lines.append("")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")
    lines.append(f"### Confidence Score: {confidence}")
    lines.append("")
    lines.append("*Generated by `claude-review` (heuristic scan, not a manual review, for reference only).*")
    return "\n".join(lines)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Claude Code PR reviewer (structured Markdown output)")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    args = parser.parse_args()

    try:
        owner, repo, pull_number = parse_pr_url(args.pr)
        pr = fetch_pr(owner, repo, pull_number)
        files = fetch_pr_files(owner, repo, pull_number)
        review = build_review(pr, files)
        print(review)
        return 0
    except Exception as exc:
        print(f"[claude-review] error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
