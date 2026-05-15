
#!/usr/bin/env python3
"""
Claude Code sub-agent: PR Reviewer with structured Markdown output.

Takes a PR URL as input, fetches the diff, analyzes it through Claude,
and returns a structured Markdown review comment.

Usage:
    python claude-review.py --pr https://github.com/owner/repo/pull/123
    python claude-review.py --pr https://github.com/owner/repo/pull/123 --token $GITHUB_TOKEN
    python claude-review.py --pr https://github.com/owner/repo/pull/123 --json  # JSON output

Requirements:
    pip install requests
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# PR URL parsing
# ---------------------------------------------------------------------------

_PR_URL_RE = re.compile(
    r'^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$'
)


@dataclass
class PullRequest:
    owner: str
    repo: str
    number: int
    url: str
    title: str = ""
    diff: str = ""
    commits: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# GitHub API client
# ---------------------------------------------------------------------------

class GitHubClient:
    """Minimal GitHub REST client."""

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.base = "https://api.github.com"

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _get(self, path: str) -> dict | list:
        import urllib.request

        url = f"{self.base}{path}"
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def _get_text(self, url: str) -> str:
        import urllib.request

        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")

    def get_pr(self, owner: str, repo: str, number: int) -> dict:
        return self._get(f"/repos/{owner}/{repo}/pulls/{number}")  # type: ignore[return-value]

    def get_commits(self, owner: str, repo: str, number: int) -> list:
        return self._get(f"/repos/{owner}/{repo}/pulls/{number}/commits")  # type: ignore[return-value]

    def get_files(self, owner: str, repo: str, number: int) -> list:
        return self._get(f"/repos/{owner}/{repo}/pulls/{number}/files")  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Review logic (rule-based, Claude-API-compatible)
# ---------------------------------------------------------------------------

@dataclass
class ReviewResult:
    summary: str
    files_changed: int
    additions: int
    deletions: int
    risks: list[str]
    suggestions: list[str]
    confidence: str  # Low / Medium / High
    files_reviewed: list[str] = field(default_factory=list)


def analyze_pr(pr: PullRequest, client: GitHubClient) -> ReviewResult:
    """Fetch PR files and commits, run rule-based analysis."""

    try:
        pr_data = client.get_pr(pr.owner, pr.repo, pr.number)
        pr.title = pr_data.get("title", "")
    except Exception:
        pr.title = f"PR #{pr.number}"

    try:
        files = client.get_files(pr.owner, pr.repo, pr.number)
    except Exception:
        files = []

    try:
        commits = client.get_commits(pr.owner, pr.repo, pr.number)
    except Exception:
        commits = []

    pr.files_reviewed = [f.get("filename", "") for f in files]
    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)

    # --- Rule-based analysis ---
    risks: list[str] = []
    suggestions: list[str] = []

    # Size risk
    if len(files) > 50:
        risks.append("Large PR: 50+ files changed — consider splitting into smaller PRs")
    elif len(files) > 20:
        risks.append("Moderate PR size: 20+ files — review carefully for scope creep")

    if additions + deletions > 5000:
        risks.append(
            f"Massive diff: {additions + deletions} lines changed — "
            "high risk of unintended side effects"
        )

    # File type risks
    config_files = [f for f in pr.files_reviewed
                   if f.endswith(('.env', '.config', '.toml', '.yaml', '.yml'))]
    if config_files:
        suggestions.append(
            f"Config files changed ({len(config_files)}): ensure no secrets exposed"
        )

    migration_files = [f for f in pr.files_reviewed if 'migration' in f.lower()]
    if migration_files:
        risks.append(
            f"Database migrations present ({len(migration_files)} of them) — "
            "verify rollback safety"
        )

    test_files = [f for f in pr.files_reviewed
                 if 'test' in f.lower() or f.endswith('_test.py') or f.endswith('.test.ts')]
    if not test_files and len(pr.files_reviewed) > 0:
        suggestions.append("No test files detected — consider adding tests")

    # Security checks
    security_files = [f for f in pr.files_reviewed
                     if any(kw in f.lower() for kw in ('auth', 'password', 'token', 'secret', 'crypto'))]
    if security_files:
        risks.append(
            f"Security-sensitive files changed ({len(security_files)}) — "
            "requires security review"
        )

    # Dependency risk
    dep_files = [f for f in pr.files_reviewed
                if f.endswith(('requirements.txt', 'package.json', 'pyproject.toml', 'Cargo.toml'))]
    if dep_files:
        suggestions.append(
            "Dependency files changed — verify versions and check for supply-chain risks"
        )

    # Confidence scoring
    if len(files) <= 5 and additions + deletions <= 200:
        confidence = "High"
    elif len(files) <= 20 and additions + deletions <= 1000:
        confidence = "Medium"
    else:
        confidence = "Low"

    if not risks and not suggestions:
        suggestions.append(
            "No specific risks detected from file-level analysis. "
            "Manual review still recommended."
        )

    # Summary
    summary_parts = [
        f'PR "{pr.title}" changes {len(files)} files',
        f'({additions}+ additions, {deletions}- deletions)',
    ]
    if commits:
        summary_parts.append(f'across {len(commits)} commits')
    summary = ". ".join(summary_parts) + "."

    return ReviewResult(
        summary=summary,
        files_changed=len(files),
        additions=additions,
        deletions=deletions,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
        files_reviewed=pr.files_reviewed,
    )


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_markdown(pr: PullRequest, result: ReviewResult) -> str:
    """Format review as structured Markdown."""
    lines = [
        f"# PR Review: {pr.title}",
        "",
        f"**PR URL:** {pr.url}",
        f"**Reviewed:** {datetime.utcnow().isoformat()}Z",
        "",
        "## Summary",
        "",
        result.summary,
        "",
        "## Statistics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Files changed | {result.files_changed} |",
        f"| Additions | {result.additions} |",
        f"| Deletions | {result.deletions} |",
        f"| Confidence | **{result.confidence}** |",
        "",
    ]

    if result.risks:
        lines.append("## ⚠️ Identified Risks")
        lines.append("")
        for r in result.risks:
            lines.append(f"- {r}")
        lines.append("")

    if result.suggestions:
        lines.append("## 💡 Improvement Suggestions")
        lines.append("")
        for s in result.suggestions:
            lines.append(f"- {s}")
        lines.append("")

    if result.files_reviewed:
        lines.append("## 📁 Files Changed")
        lines.append("")
        for f in result.files_reviewed[:30]:
            lines.append(f"- `{f}`")
        if len(result.files_reviewed) > 30:
            lines.append(f"- ... and {len(result.files_reviewed) - 30} more files")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Review generated by claude-review on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")

    return "\n".join(lines)


def format_json(pr: PullRequest, result: ReviewResult) -> str:
    """Format review as JSON."""
    return json.dumps({
        "pr_url": pr.url,
        "title": pr.title,
        "summary": result.summary,
        "statistics": {
            "files_changed": result.files_changed,
            "additions": result.additions,
            "deletions": result.deletions,
        },
        "risks": result.risks,
        "suggestions": result.suggestions,
        "confidence": result.confidence,
        "files_reviewed": result.files_reviewed,
        "reviewed_at": datetime.utcnow().isoformat() + "Z",
    }, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Claude Code PR review agent — structured Markdown/JSON output"
    )
    parser.add_argument(
        "--pr", required=True,
        help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--token",
        help="GitHub token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of Markdown"
    )
    parser.add_argument(
        "--output", "-o",
        help="Write output to file instead of stdout"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Parse PR URL
    m = _PR_URL_RE.match(args.pr.strip())
    if not m:
        print(f"Error: invalid PR URL: {args.pr}", file=sys.stderr)
        print("Expected: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)

    owner, repo, number = m.group(1), m.group(2), int(m.group(3))
    pr = PullRequest(
        owner=owner, repo=repo, number=number,
        url=f"https://github.com/{owner}/{repo}/pull/{number}",
    )

    # Analyze
    client = GitHubClient(token=args.token)
    result = analyze_pr(pr, client)

    # Format output
    if args.json:
        output = format_json(pr, result)
    else:
        output = format_markdown(pr, result)

    # Write
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Review written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
