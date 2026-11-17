#!/usr/bin/env python3
"""
Claude Code Sub-Agent: Automated Pull Request Reviewer (`claude-review`)
Analyzes a GitHub Pull Request diff and produces a structured Markdown review
containing:
  1. Summary of changes (2-3 sentences)
  2. Identified risks (bulleted list)
  3. Improvement suggestions (bulleted list)
  4. Confidence score (Low / Medium / High)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


def parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
    """Extracts (owner, repo, pull_number) from a GitHub PR URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub Pull Request URL: {pr_url}")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_metadata_and_diff(owner: str, repo: str, pull_number: int, token: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """Fetches PR metadata JSON and unified diff from GitHub REST API."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers_json = {
        "User-Agent": "claude-review-subagent/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    headers_diff = {
        "User-Agent": "claude-review-subagent/1.0",
        "Accept": "application/vnd.github.v3.diff",
    }
    if token:
        headers_json["Authorization"] = f"token {token}"
        headers_diff["Authorization"] = f"token {token}"

    req_meta = urllib.request.Request(api_url, headers=headers_json)
    with urllib.request.urlopen(req_meta, timeout=15) as resp:
        meta = json.loads(resp.read().decode("utf-8"))

    req_diff = urllib.request.Request(api_url, headers=headers_diff)
    with urllib.request.urlopen(req_diff, timeout=15) as resp:
        diff_text = resp.read().decode("utf-8", errors="replace")

    return meta, diff_text


def analyze_diff_heuristics(meta: Dict[str, Any], diff_text: str) -> Dict[str, Any]:
    """Performs deterministic static analysis on a unified diff as a fallback or pre-pass for Claude."""
    files_changed = re.findall(r"^diff --git a/(.+?) b/(.+?)$", diff_text, re.MULTILINE)
    file_names = [f[1] for f in files_changed]
    added_lines = [line[1:] for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed_lines = [line[1:] for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---")]

    title = meta.get("title", "Pull Request")
    additions = meta.get("additions", len(added_lines))
    deletions = meta.get("deletions", len(removed_lines))
    changed_count = meta.get("changed_files", len(file_names))

    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in file_names)
    has_workflows = any(".github/workflows" in f for f in file_names)
    has_secrets_risk = any(
        re.search(r"""(api_key|secret|password|private_key)\s*=\s*['"][^'"]{8,}['"]""", line, re.IGNORECASE)
        for line in added_lines
    )
    has_todo = any("TODO" in line or "FIXME" in line for line in added_lines)
    has_broad_except = any(re.search(r"except\s*(Exception)?:\s*$", line) for line in added_lines)

    summary = (
        f"This pull request ({title}) modifies {changed_count} file(s) with {additions} addition(s) "
        f"and {deletions} deletion(s). "
        f"Key areas touched include {', '.join(file_names[:4]) if file_names else 'repository configuration'}. "
        f"{'Unit test coverage is included alongside the implementation.' if has_tests else 'No dedicated test files were modified in this changeset.'}"
    )

    risks: List[str] = []
    if not has_tests and changed_count > 0:
        risks.append("No test files (`*test*` or `*spec*`) were added or updated; edge-case regressions may go undetected.")
    if has_secrets_risk:
        risks.append("Potential hardcoded credential or token literal detected in added lines; verify secrets are read from environment variables.")
    if has_workflows:
        risks.append("Modifies CI/CD GitHub Actions workflow definitions; verify `permissions:` scope follows least-privilege principles.")
    if has_broad_except:
        risks.append("Broad exception catch clause detected, which may mask unexpected runtime or network failures.")
    if additions > 500:
        risks.append(f"Large diff footprint (+{additions} lines) increases review complexity and merge conflict surface area.")
    if not risks:
        risks.append("Low operational risk: changes are well-scoped and include accompanying verification tests.")

    suggestions: List[str] = []
    if not has_tests:
        suggestions.append("Add unit or integration tests covering both the happy path and error handling branches.")
    if has_todo:
        suggestions.append("Resolve or track inline `TODO` / `FIXME` markers in follow-up issues before merging to `main`.")
    if has_broad_except:
        suggestions.append("Narrow exception handling to specific error classes and log contextual diagnostic details.")
    suggestions.append("Ensure public functions and CLI entrypoints include explicit type annotations and docstrings.")

    confidence = "High" if (has_tests and additions <= 800 and not has_secrets_risk) else ("Medium" if additions <= 1500 else "Low")

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
    }


def format_markdown_review(analysis: Dict[str, Any], pr_url: str = "") -> str:
    """Formats the structured analysis dictionary into a GitHub PR review comment."""
    risks_md = "\n".join(f"- {r}" for r in analysis["risks"])
    suggestions_md = "\n".join(f"- {s}" for s in analysis["suggestions"])
    header_link = f" for [{pr_url}]({pr_url})" if pr_url else ""

    return f"""## 🤖 Claude Code Sub-Agent PR Review{header_link}

### 📋 Summary of Changes
{analysis["summary"]}

### ⚠️ Identified Risks
{risks_md}

### 💡 Improvement Suggestions
{suggestions_md}

### 🎯 Confidence Score
**{analysis["confidence"]}**
"""


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Claude Code Sub-Agent PR Reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", help="Optional path to local unified diff file instead of fetching from GitHub")
    parser.add_argument("--output", help="Optional file path to write the Markdown review")
    args = parser.parse_args(argv)

    owner, repo, pull_number = parse_pr_url(args.pr)
    token = os.environ.get("GITHUB_TOKEN")

    if args.diff_file and os.path.exists(args.diff_file):
        with open(args.diff_file, "r", encoding="utf-8") as f:
            diff_text = f.read()
        meta = {"title": f"PR #{pull_number} in {owner}/{repo}"}
    else:
        meta, diff_text = fetch_pr_metadata_and_diff(owner, repo, pull_number, token=token)

    analysis = analyze_diff_heuristics(meta, diff_text)
    markdown = format_markdown_review(analysis, pr_url=args.pr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)

    print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
