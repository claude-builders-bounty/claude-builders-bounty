#!/usr/bin/env python3
"""Small PR review agent that returns a structured Markdown review.

The tool fetches a pull request diff from GitHub and applies deterministic
heuristics to produce a concise review with summary, risks, suggestions, and a
confidence score. It does not post comments by itself.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse

PR_RE = re.compile(r"^/([^/]+)/([^/]+)/pull/(\d+)$")
FILE_RE = re.compile(r"^diff --git a/(.*?) b/(.*?)$", re.MULTILINE)
ADDED_RE = re.compile(r"^\+(?!\+\+)", re.MULTILINE)
REMOVED_RE = re.compile(r"^-(?!--)", re.MULTILINE)
DANGEROUS_PATTERNS = (
    ("destructive shell command", re.compile(r"rm\s+-rf|git\s+push\s+.*--force", re.IGNORECASE)),
    ("unsafe SQL operation", re.compile(r"\b(drop\s+table|truncate|delete\s+from(?![^;\n]*\bwhere\b))", re.IGNORECASE)),
    ("possible secret material", re.compile(r"(api[_-]?key|secret|token|password)\s*[:=]", re.IGNORECASE)),
    ("network call without obvious timeout", re.compile(r"urlopen\(|requests\.(get|post|put|delete)\(", re.IGNORECASE)),
)


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: str


def parse_pr_url(url: str) -> PullRequestRef:
    parsed = urlparse(url)
    match = PR_RE.match(parsed.path)
    if parsed.netloc not in {"github.com", "www.github.com"} or not match:
        raise ValueError("expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestRef(owner, repo, number)


def fetch_diff(ref: PullRequestRef) -> str:
    request = urllib.request.Request(
        f"https://patch-diff.githubusercontent.com/raw/{ref.owner}/{ref.repo}/pull/{ref.number}.diff",
        headers={"Accept": "text/plain", "User-Agent": "claude-review-agent"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def analyze_diff(diff: str) -> dict:
    files = [match.group(2) for match in FILE_RE.finditer(diff)]
    added = len(ADDED_RE.findall(diff))
    removed = len(REMOVED_RE.findall(diff))
    risks = []
    for label, pattern in DANGEROUS_PATTERNS:
        if pattern.search(diff):
            risks.append(label)
    if added + removed > 500:
        risks.append("large diff size")
    suggestions = []
    if any(path.endswith((".py", ".sh", ".js", ".ts")) for path in files):
        suggestions.append("Run the relevant unit or smoke tests before merge.")
    if any(path.lower().endswith(("readme.md", "docs.md")) or "/docs/" in path for path in files):
        suggestions.append("Check rendered Markdown for broken formatting or commands.")
    if risks:
        suggestions.append("Review the flagged risky patterns manually before approval.")
    if not suggestions:
        suggestions.append("No specific follow-up beyond normal reviewer judgment.")
    confidence = "High"
    if not diff.strip() or added + removed == 0:
        confidence = "Low"
    elif risks or added + removed > 300:
        confidence = "Medium"
    return {"files": files, "added": added, "removed": removed, "risks": risks, "suggestions": suggestions, "confidence": confidence}


def render_review(pr_url: str, analysis: dict) -> str:
    files = analysis["files"]
    risks = analysis["risks"] or ["No obvious high-risk patterns detected by heuristic scan."]
    lines = [
        "# PR Review",
        "",
        "## Summary",
        "",
        f"Reviewed `{pr_url}`. The diff touches {len(files)} file(s) with {analysis['added']} added line(s) and {analysis['removed']} removed line(s).",
        f"Primary changed files: {', '.join(files[:5]) if files else 'none detected'}{', ...' if len(files) > 5 else ''}.",
        "",
        "## Identified risks",
        "",
    ]
    lines.extend(f"- {risk}" for risk in risks)
    lines.extend(["", "## Improvement suggestions", ""])
    lines.extend(f"- {suggestion}" for suggestion in analysis["suggestions"])
    lines.extend(["", f"## Confidence: {analysis['confidence']}", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff and print structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    args = parser.parse_args(argv)
    try:
        ref = parse_pr_url(args.pr)
        diff = fetch_diff(ref)
    except (ValueError, urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"claude-review failed: {exc}", file=sys.stderr)
        return 1
    print(render_review(args.pr, analyze_diff(diff)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
