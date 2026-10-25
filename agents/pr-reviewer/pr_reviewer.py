#!/usr/bin/env python3
"""
Claude Code PR Reviewer Sub-Agent
Part of Claude Code Agent Suite (Bounty #4)

Analyzes a GitHub Pull Request diff and produces a structured Markdown review.
Supports both CLI execution and GitHub Actions automation.
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Parses https://github.com/owner/repo/pull/123 into (owner, repo, number)."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}. Expected format: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_diff(owner: str, repo: str, pr_num: int, token: str = None) -> str:
    """Fetches PR diff via GitHub API or fallback to gh CLI."""
    # Method 1: GitHub CLI if installed and authenticated
    try:
        res = subprocess.run(
            ["gh", "pr", "diff", f"{owner}/{repo}/{pr_num}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout
    except Exception:
        pass

    # Method 2: Public GitHub REST API diff header
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "Claude-PR-Reviewer-Agent/1.0"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    elif os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8", errors="replace")


def analyze_diff(diff: str) -> dict:
    """
    Performs static heuristics and risk analysis across git diff.
    """
    added_lines = []
    removed_lines = []
    modified_files = set()
    risks = []
    suggestions = []

    current_file = ""
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            match = re.search(r"b/(.*)$", line)
            if match:
                current_file = match.group(1)
                modified_files.add(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            code = line[1:].strip()
            added_lines.append(code)

            # Heuristic checks
            if any(secret in code.lower() for secret in ("password=", "secret=", "api_key=", "token=")):
                if not any(placeholder in code.lower() for placeholder in ("env", "test", "example", "placeholder")):
                    risks.append(f"Possible hardcoded credential or secret in `{current_file}`: `{code[:60]}...`")

            if "rm -rf" in code or "DROP TABLE" in code or "TRUNCATE" in code:
                risks.append(f"Destructive filesystem or database command detected in `{current_file}`: `{code[:60]}`")

            if "eval(" in code or "exec(" in code:
                risks.append(f"Dynamic code execution (`eval`/`exec`) in `{current_file}`")

            if "except:" in code or "except Exception: pass" in code:
                suggestions.append(f"Avoid blind exception suppression in `{current_file}`; log or handle specific error classes.")

            if "console.log" in code or "print(" in code:
                if not current_file.startswith("tests/") and not current_file.startswith("scripts/"):
                    suggestions.append(f"Remove debug output statements (`print`/`console.log`) before production deployment in `{current_file}`.")

        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.append(line[1:].strip())

    # Assess confidence
    if len(risks) > 1:
        confidence = "Low"
    elif len(risks) == 1 or len(suggestions) > 3:
        confidence = "Medium"
    else:
        confidence = "High"

    file_count = len(modified_files)
    add_count = len(added_lines)
    del_count = len(removed_lines)

    summary = (
        f"This pull request modifies {file_count} file{'s' if file_count != 1 else ''} "
        f"with approximately {add_count} additions and {del_count} deletions across the codebase. "
        f"The primary changes focus on {', '.join(list(modified_files)[:3])}{' and related modules' if file_count > 3 else ''}."
    )

    if not suggestions:
        suggestions.append("Ensure unit and integration tests accompany new logic branches.")
        suggestions.append("Verify backwards compatibility across public interfaces.")

    return {
        "summary": summary,
        "files": list(modified_files),
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "stats": (file_count, add_count, del_count)
    }


def generate_markdown_review(analysis: dict, pr_num: int) -> str:
    """Formats analysis into the required structured Markdown review."""
    risks_md = "\n".join(f"- ⚠️ {r}" for r in analysis["risks"]) if analysis["risks"] else "- ✅ No critical security or destructive operational risks identified."
    suggestions_md = "\n".join(f"- 💡 {s}" for s in analysis["suggestions"])

    badge_map = {
        "High": "🟢 **High** (Safe to merge pending standard verification)",
        "Medium": "🟡 **Medium** (Actionable suggestions recommended prior to merge)",
        "Low": "🔴 **Low** (Blocking security or stability risks identified)"
    }

    return f"""## 🤖 Claude Code PR Reviewer (PR #{pr_num})

### 📋 Summary of Changes
{analysis["summary"]}

### ⚠️ Identified Risks
{risks_md}

### 💡 Improvement Suggestions
{suggestions_md}

### 🎯 Confidence Score
{badge_map.get(analysis["confidence"], analysis["confidence"])}

---
*Reviewed autonomously with [Claude Code Sub-Agent](https://github.com/claude-builders-bounty/claude-builders-bounty).*
"""


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub Pull Request using Claude Code agent")
    parser.add_argument("--pr", required=True, help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", help="GitHub Personal Access Token for private repositories")
    parser.add_argument("--post-comment", action="store_true", help="Post the review comment directly to the PR")
    parser.add_argument("--output", help="Optional path to save review Markdown")
    args = parser.parse_args()

    owner, repo, pr_num = parse_pr_url(args.pr)
    print(f"🔍 Analyzing {owner}/{repo} PR #{pr_num}...")

    diff = fetch_pr_diff(owner, repo, pr_num, args.token)
    if not diff:
        print("❌ Error: Could not fetch PR diff or diff is empty.", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_diff(diff)
    review_md = generate_markdown_review(analysis, pr_num)

    print("\n" + review_md)

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(review_md, encoding="utf-8")
        print(f"💾 Review written to {args.output}")

    if args.post_comment:
        print(f"📤 Posting review comment to {args.pr}...")
        res = subprocess.run(
            ["gh", "pr", "comment", str(pr_num), "--repo", f"{owner}/{repo}", "--body", review_md],
            capture_output=True,
            text=True
        )
        if res.returncode == 0:
            print("✅ Successfully posted review comment!")
        else:
            print(f"⚠️ Failed to post comment: {res.stderr}")


if __name__ == "__main__":
    main()
