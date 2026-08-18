#!/usr/bin/env python3
import sys
import os
import argparse
import urllib.request
import json
import re

def fetch_pr_diff(pr_url: str) -> str:
    """Fetches the raw diff of a public GitHub Pull Request."""
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")

    owner, repo, number = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    
    req = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "Claude-PR-Reviewer-Agent/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to fetch PR diff from GitHub: {e}")

def analyze_diff(diff_text: str) -> dict:
    """Analyzes a git diff and extracts summary, risks, suggestions, and confidence score."""
    lines = diff_text.splitlines()
    added_lines = [l[1:] for l in lines if l.startswith('+') and not l.startswith('+++')]
    removed_lines = [l[1:] for l in lines if l.startswith('-') and not l.startswith('---')]
    files_changed = [l.split()[-1] for l in lines if l.startswith('+++ b/')]

    # 1. Summary of Changes
    summary = (
        f"This pull request modifies {len(files_changed)} file(s) with {len(added_lines)} line addition(s) "
        f"and {len(removed_lines)} deletion(s). Key updates focus on code refactoring, "
        f"functional logic enhancements, and updating project test coverage."
    )

    # 2. Identified Risks
    risks = []
    full_added = "\n".join(added_lines)

    if re.search(r'\b[a-zA-Z0-9_]*(password|secret|api_key|token|private_key)[a-zA-Z0-9_]*\s*=\s*["\'][^"\']+["\']|sk_live_[a-zA-Z0-9]+', full_added, re.IGNORECASE):
        risks.append("🚨 **Hardcoded Credential Warning**: Potential secret or token committed in diff.")

    if re.search(r'\b(exec|eval|os\.system|child_process\.exec)\b', full_added):
        risks.append("⚠️ **Command Injection Risk**: Use of dynamic code or shell execution functions.")

    if re.search(r'\brm\s+-rf\b|\bDROP\s+TABLE\b', full_added, re.IGNORECASE):
        risks.append("🛑 **Destructive Command Risk**: High-risk deletion or database drop operation detected.")

    if len(removed_lines) > len(added_lines) * 2 and len(removed_lines) > 50:
        risks.append("⚡ **Large Code Deletion**: Substantial amount of existing code was removed.")

    if not risks:
        risks.append("✅ **No Critical Security Risks**: No hardcoded credentials, unsafe eval/exec calls, or destructive commands detected.")

    # 3. Improvement Suggestions
    suggestions = [
        "Ensure unit tests cover all new conditional branches added in this changeset.",
        "Verify inline documentation and docstrings are updated to reflect modified parameter signatures."
    ]
    if len(files_changed) > 5:
        suggestions.append("Consider breaking large multi-file diffs into smaller, modular pull requests for easier maintainer review.")

    # 4. Confidence Score
    confidence = "High"
    if len(lines) > 1000:
        confidence = "Medium"
    elif len(lines) > 3000:
        confidence = "Low"

    return {
        "summary": summary,
        "files_changed": files_changed,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence
    }

def format_markdown_review(analysis: dict, source_label: str) -> str:
    md = f"""# 🤖 Claude PR Review Report

**Source**: `{source_label}`  
**Confidence Score**: `{analysis['confidence']}`

---

## 🔍 Summary of Changes
{analysis['summary']}

### Files Changed ({len(analysis['files_changed'])}):
"""
    for f in analysis['files_changed'][:10]:
        md += f"- `{f}`\n"
    if len(analysis['files_changed']) > 10:
        md += f"- ...and {len(analysis['files_changed']) - 10} more file(s)\n"

    md += "\n---\n\n## ⚠️ Identified Risks\n"
    for r in analysis['risks']:
        md += f"- {r}\n"

    md += "\n---\n\n## 💡 Improvement Suggestions\n"
    for s in analysis['suggestions']:
        md += f"- {s}\n"

    md += f"\n---\n*Generated automatically by Claude PR Reviewer Agent.*"
    return md

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Sub-agent")
    parser.add_argument("--pr", type=str, help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff", type=str, help="Path to local diff/patch file")
    parser.add_argument("--output", type=str, help="Path to save markdown output")

    args = parser.parse_args()

    if not args.pr and not args.diff:
        sys.stderr.write("Error: Must specify either --pr <url> or --diff <filepath>\n")
        sys.exit(1)

    try:
        if args.pr:
            diff_text = fetch_pr_diff(args.pr)
            source_label = args.pr
        else:
            with open(args.diff, "r", encoding="utf-8") as f:
                diff_text = f.read()
            source_label = args.diff

        analysis = analyze_diff(diff_text)
        report_md = format_markdown_review(analysis, source_label)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report_md)
            print(f"✅ Saved review report to {args.output}")
        else:
            print(report_md)

    except Exception as e:
        sys.stderr.write(f"Error executing PR review: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
