#!/usr/bin/env python3
"""
Claude Code PR Review Sub-agent

Fetches a GitHub PR diff and produces a structured Markdown code review.
Can be used as CLI or as a GitHub Action.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr owner/repo#123
    claude-review --diff < diff_file
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ReviewFinding:
    severity: str  # "critical", "warning", "info"
    category: str  # "security", "performance", "bug", "style", "maintainability"
    file: str
    line: Optional[int]
    description: str
    suggestion: str


@dataclass
class ReviewResult:
    pr_url: str
    summary: str
    confidence: str  # "Low", "Medium", "High"
    risks: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    findings: list[ReviewFinding] = field(default_factory=list)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, pr_number."""
    patterns = [
        r"github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        r"([^/]+)/([^/]+)#(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2), int(match.group(3))
    raise ValueError(f"Cannot parse PR URL: {url}")


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch PR diff using gh CLI."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}",
         "--jq", ".diff_url"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        # Fallback: use gh pr diff
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr_number),
             "-R", f"{owner}/{repo}"],
            capture_output=True, text=True
        )
    return result.stdout


def fetch_pr_info(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout) if result.returncode == 0 else {}


def analyze_diff(diff_text: str) -> ReviewResult:
    """Analyze a diff and produce structured findings."""
    findings = []
    risks = []
    improvements = []

    files_changed = re.findall(r"^diff --git a/(.*?) b/", diff_text, re.MULTILINE)
    additions = len(re.findall(r"^\+[^+]", diff_text, re.MULTILINE))
    deletions = len(re.findall(r"^-[^-]", diff_text, re.MULTILINE))

    # Security checks
    if re.search(r"(password|secret|token|api_key)\s*=\s*['"][^'"]+['"]", diff_text, re.IGNORECASE):
        findings.append(ReviewFinding(
            severity="critical", category="security",
            file="multiple", line=None,
            description="Hardcoded credentials detected in diff",
            suggestion="Move secrets to environment variables or a secrets manager"
        ))
        risks.append("Hardcoded credentials could be exposed in version control")

    if re.search(r"eval\(|exec\(|subprocess\.call.*shell=True", diff_text):
        findings.append(ReviewFinding(
            severity="critical", category="security",
            file="multiple", line=None,
            description="Potential code injection via eval/exec/shell=True",
            suggestion="Use subprocess.run with shell=False and a list of args"
        ))
        risks.append("Code injection vulnerability")

    # SQL injection checks
    if re.search(r"f['"].*SELECT.*{.*}.*FROM|f['"].*INSERT.*{.*}|\.format\(.*SELECT", diff_text, re.IGNORECASE):
        findings.append(ReviewFinding(
            severity="critical", category="security",
            file="multiple", line=None,
            description="Potential SQL injection via string formatting",
            suggestion="Use parameterized queries"
        ))

    # Performance checks
    if re.search(r"\bfor\b.*\bin\b.*:\s*$.*\bfor\b.*\bin\b", diff_text, re.DOTALL):
        improvements.append("Consider if nested loops can be optimized (O(n²) pattern detected)")

    # Error handling
    if re.search(r"except\s*:", diff_text):
        findings.append(ReviewFinding(
            severity="warning", category="maintainability",
            file="multiple", line=None,
            description="Bare except clause catches all exceptions including KeyboardInterrupt",
            suggestion="Catch specific exceptions: except (ValueError, TypeError) as e:"
        ))

    if re.search(r"except.*:\s*\n\s*pass", diff_text):
        findings.append(ReviewFinding(
            severity="warning", category="maintainability",
            file="multiple", line=None,
            description="Silenced exception (except: pass)",
            suggestion="At minimum, log the exception for debugging"
        ))

    # TODO/FIXME tracking
    todos = re.findall(r"(TODO|FIXME|HACK|XXX):?\s*(.*)", diff_text)
    for tag, desc in todos:
        improvements.append(f"Found {tag}: {desc.strip()}")

    # Determine confidence
    if len(files_changed) <= 5 and additions <= 200:
        confidence = "High"
    elif len(files_changed) <= 15 and additions <= 500:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Generate summary
    summary_parts = [f"Changes across {len(files_changed)} file(s)"]
    summary_parts.append(f"+{additions}/-{deletions} lines")
    if findings:
        critical = sum(1 for f in findings if f.severity == "critical")
        if critical:
            summary_parts.append(f"⚠️ {critical} critical finding(s)")

    return ReviewResult(
        pr_url="",
        summary=". ".join(summary_parts) + ".",
        confidence=confidence,
        risks=risks,
        improvements=improvements,
        findings=findings,
    )


def format_markdown(review: ReviewResult) -> str:
    """Format review as Markdown."""
    lines = ["# 🔍 PR Review Report", ""]

    lines.append(f"**Confidence:** {review.confidence}")
    lines.append(f"**Summary:** {review.summary}")
    lines.append("")

    if review.risks:
        lines.append("## ⚠️ Identified Risks")
        for risk in review.risks:
            lines.append(f"- {risk}")
        lines.append("")

    if review.findings:
        lines.append("## 🔎 Findings")
        for f in review.findings:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[f.severity]
            lines.append(f"### {icon} [{f.severity.upper()}] {f.category}: {f.description}")
            lines.append(f"**File:** `{f.file}`")
            if f.line:
                lines.append(f"**Line:** {f.line}")
            lines.append(f"**Suggestion:** {f.suggestion}")
            lines.append("")

    if review.improvements:
        lines.append("## 💡 Improvement Suggestions")
        for imp in review.improvements:
            lines.append(f"- {imp}")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by claude-review*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument("--pr", help="GitHub PR URL or owner/repo#number")
    parser.add_argument("--diff", help="Read diff from stdin", action="store_true")
    parser.add_argument("--json", help="Output as JSON", action="store_true")
    args = parser.parse_args()

    if args.diff:
        diff_text = sys.stdin.read()
        review = analyze_diff(diff_text)
        review.pr_url = "stdin"
    elif args.pr:
        owner, repo, pr_number = parse_pr_url(args.pr)
        diff_text = fetch_pr_diff(owner, repo, pr_number)
        pr_info = fetch_pr_info(owner, repo, pr_number)
        review = analyze_diff(diff_text)
        review.pr_url = args.pr
    else:
        parser.error("Either --pr or --diff is required")

    if args.json:
        print(json.dumps({
            "pr_url": review.pr_url,
            "summary": review.summary,
            "confidence": review.confidence,
            "risks": review.risks,
            "improvements": review.improvements,
            "findings": [{
                "severity": f.severity,
                "category": f.category,
                "file": f.file,
                "description": f.description,
                "suggestion": f.suggestion,
            } for f in review.findings],
        }, indent=2))
    else:
        print(format_markdown(review))


if __name__ == "__main__":
    main()
