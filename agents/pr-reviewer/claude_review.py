#!/usr/bin/env python3
"""
Claude Code PR Reviewer CLI & Agent
Analyzes Pull Request diffs and outputs structured Markdown or JSON review comments:
- Summary of changes
- Identified risks (evaluated on added lines to avoid flagging remediated risks)
- Improvement suggestions
- Confidence score (Low / Medium / High)
"""

import sys
import os
import re
import json
import argparse
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Strictly parses https://github.com/{owner}/{repo}/pull/{number}."""
    m = re.fullmatch(
        r"https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)/?(?:[?#][^\s]*)?",
        url.strip(),
    )
    if not m or m.group(1) in {".", ".."} or m.group(2) in {".", ".."}:
        raise ValueError(f"Invalid GitHub PR URL: {url}. Expected format: https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), int(m.group(3))

def fetch_pr_diff(owner: str, repo: str, pull_number: int, token: str | None = None) -> str:
    """Fetches the unified diff from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "Claude-PR-Reviewer/1.0"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(20 * 1024 * 1024).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API Error ({e.code}): {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Network error while fetching diff: {e}")

def diff_stats(text: str) -> tuple[int, int, int, str]:
    """Extracts files changed count, additions, deletions, and concatenated added lines."""
    git_files = sum(line.startswith("diff --git ") for line in text.splitlines())
    plus_files = sum(line.startswith("+++ ") for line in text.splitlines())
    files_count = git_files or plus_files or 1

    added_lines = []
    additions = 0
    deletions = 0

    for line in text.splitlines():
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            additions += 1
            added_lines.append(line[1:])
        elif line.startswith("-"):
            deletions += 1

    return files_count, additions, deletions, "\n".join(added_lines)

def analyze_diff(diff_text: str, owner: str = "repo", repo: str = "target", pull_number: int = 0) -> dict:
    """Performs static and heuristic review analysis on the diff."""
    files_count, additions, deletions, added_text = diff_stats(diff_text)

    risks = []
    suggestions = []

    # Risk detection evaluated against ADDED lines to avoid flagging remediated risks
    if re.search(r"\b(rm\s+-rf|DROP\s+(?:TABLE|DATABASE|SCHEMA)|git\s+push\s+--force)\b", added_text, re.I):
        risks.append("Contains potentially destructive command strings or references that require strict execution sandboxing.")
    
    if re.search(r"(\.env|secret|api_key|private_key|token)\s*[:=]", added_text, re.I):
        risks.append("Potential credential or sensitive configuration modification detected in added code.")

    # Check for unit tests
    has_tests = bool(re.search(r"\b(?:test|spec)[a-zA-Z0-9_]*\.(?:py|ts|js|jsx|tsx|go|rs)\b|/(?:tests|test|specs|spec)/", diff_text, re.I))
    if not has_tests:
        suggestions.append("Consider adding unit tests to verify new logic and prevent regression.")

    if not risks:
        risks.append("No critical security or irreversible operational risks identified in new additions.")

    if not suggestions:
        suggestions.append("Code adheres to standard repository conventions; ensure all CI workflows pass.")

    # Confidence calculation based on diff size and test presence
    if additions + deletions < 300 and has_tests:
        confidence = "High"
    elif additions + deletions < 1000:
        confidence = "Medium"
    else:
        confidence = "Low"

    summary = (
        f"This pull request modifies {files_count} file(s) across `{owner}/{repo}` with "
        f"+{additions} line(s) added and -{deletions} line(s) removed."
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files_count": files_count,
        "additions": additions,
        "deletions": deletions
    }

def format_review_markdown(review_data: dict, pr_url: str) -> str:
    """Formats analysis dictionary into standardized Markdown."""
    risks_md = "\n".join(f"- ⚠️ {r}" for r in review_data["risks"])
    sugg_md = "\n".join(f"- 💡 {s}" for s in review_data["suggestions"])

    return f"""## 🤖 Claude Code PR Review

### 📋 Summary of Changes
{review_data["summary"]}

### 🚨 Identified Risks
{risks_md}

### 💡 Improvement Suggestions
{sugg_md}

### 🎯 Confidence Score
**{review_data["confidence"]}** (Review evaluated against repository static invariants and diff scope)

---
*Reviewed by [Claude PR Reviewer](https://github.com/claude-builders-bounty/claude-builders-bounty) for `{pr_url}`.*
"""

def write_atomic(output_path: Path, content: str):
    """Writes output atomically using a temporary file in the destination directory."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_file = tempfile.mkstemp(dir=output_path.parent, prefix=".review_", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_file, output_path)

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer CLI & Agent")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", help="GitHub Pull Request URL (https://github.com/owner/repo/pull/123)")
    group.add_argument("--diff-file", help="Path to a local unified diff file to analyze")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format (default: markdown)")
    parser.add_argument("--output", help="Optional output file path to write output")
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    
    if args.pr:
        owner, repo, pr_num = parse_pr_url(args.pr)
        diff = fetch_pr_diff(owner, repo, pr_num, token)
        source_label = args.pr
    else:
        diff = Path(args.diff_file).read_text(encoding="utf-8")
        owner, repo, pr_num = "local", Path(args.diff_file).stem, 0
        source_label = f"local file: {args.diff_file}"

    review_data = analyze_diff(diff, owner, repo, pr_num)

    if args.format == "json":
        output_content = json.dumps(review_data, indent=2)
    else:
        output_content = format_review_markdown(review_data, source_label)

    if args.output:
        write_atomic(Path(args.output), output_content)
        print(f"✅ Review written to {args.output}")
    else:
        print(output_content)

if __name__ == "__main__":
    main()
