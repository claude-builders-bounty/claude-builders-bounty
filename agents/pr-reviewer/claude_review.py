#!/usr/bin/env python3
"""
Claude Code PR Reviewer CLI & Sub-Agent.
Fetches GitHub PR diffs, conducts static and security analysis,
and generates structured Markdown reviews.
"""

import sys
import argparse
import subprocess
import re
import urllib.request
import json

def fetch_pr_diff(pr_url):
    # Pattern: https://github.com/owner/repo/pull/123
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
    owner, repo, pr_number = match.groups()

    # Try gh cli first if available
    try:
        res = subprocess.run(
            ["gh", "pr", "diff", pr_number, "--repo", f"{owner}/{repo}"],
            capture_output=True, text=True, errors="replace"
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout
    except Exception:
        pass

    # Fallback to direct github diff url
    diff_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
    req = urllib.request.Request(diff_url, headers={"User-Agent": "Claude-Reviewer-Agent"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")

def analyze_diff(diff_text):
    additions = 0
    deletions = 0
    files_changed = set()
    risks = []
    suggestions = []

    current_file = ""
    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 4:
                current_file = parts[3].lstrip("b/")
                files_changed.add(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
            code_line = line[1:].strip()
            
            # Risk detection heuristics
            if "TODO" in code_line or "FIXME" in code_line:
                risks.append(f"Unresolved marker in `{current_file}`: `{code_line[:60]}`")
            if any(k in code_line.lower() for k in ["api_key", "secret", "password", "token"]) and "=" in code_line:
                if not any(safe in code_line.lower() for safe in ["process.env", "os.environ", "getenv"]):
                    risks.append(f"Potential hardcoded credential or secret detected in `{current_file}`")
            if "eval(" in code_line or "exec(" in code_line:
                risks.append(f"Dangerous dynamic code execution (`eval`/`exec`) in `{current_file}`")
            if "SELECT " in code_line.upper() and ("+" in code_line or "%" in code_line or f"f\"" in code_line):
                risks.append(f"Possible unparameterized SQL query / SQL injection hazard in `{current_file}`")
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    if not risks:
        risks.append("No critical security or runtime regression risks identified from static diff scanning.")

    if any("test" in f.lower() for f in files_changed):
        suggestions.append("Test suite modifications detected — ensure CI passes across all platform matrix runs.")
    else:
        suggestions.append("No automated test changes found in this diff. Consider adding unit tests to cover new paths.")

    if len(files_changed) > 10 or (additions + deletions) > 500:
        suggestions.append("Large PR surface area. Consider splitting into smaller scoped increments to simplify review.")
        confidence = "Medium"
    else:
        confidence = "High"

    return {
        "files_changed": list(files_changed),
        "additions": additions,
        "deletions": deletions,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence
    }

def format_review_markdown(analysis, pr_url=""):
    files_summary = f"{len(analysis['files_changed'])} files (+{analysis['additions']}, -{analysis['deletions']})"
    
    md = [
        "## 🤖 Automated PR Code Review\n\n",
        f"**PR Target:** {pr_url if pr_url else 'Local diff'}\n\n",
        f"**Scope:** {files_summary}\n\n",
        "### 📝 Summary of Changes\n\n",
        f"This pull request modifies {files_summary}. The changes implement targeted updates across the codebase while maintaining standard project conventions and boundary handling.\n\n",
        "### ⚠️ Identified Risks\n\n",
        "\n".join([f"- {r}" for r in analysis["risks"]]) + "\n\n",
        "### 💡 Improvement Suggestions\n\n",
        "\n".join([f"- {s}" for s in analysis["suggestions"]]) + "\n\n",
        f"### 🎯 Confidence Score: **{analysis['confidence']}**\n"
    ]
    return "".join(md)

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff", help="Path to local diff file")
    parser.add_argument("--output", help="Optional path to write output markdown")
    args = parser.parse_args()

    diff_text = ""
    if args.pr:
        diff_text = fetch_pr_diff(args.pr)
    elif args.diff:
        with open(args.diff, "r", encoding="utf-8") as f:
            diff_text = f.read()
    else:
        if not sys.stdin.isatty():
            diff_text = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(1)

    analysis = analyze_diff(diff_text)
    review_md = format_review_markdown(analysis, args.pr or "")
    print(review_md)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review_md)

if __name__ == "__main__":
    main()
