#!/usr/bin/env python3
"""claude-review — AI-powered PR review with structured Markdown output.

Usage: python claude-review.py --pr https://github.com/owner/repo/pull/123
"""

import argparse, json, os, re, subprocess, sys
from datetime import datetime

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def fetch_pr_diff(pr_url):
    """Extract owner/repo/number from PR URL and fetch diff via gh CLI."""
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    owner, repo, number = match.groups()
    diff = run(f"gh pr diff {number} -R {owner}/{repo}")
    return diff, owner, repo, number

def analyze_diff(diff):
    """Lightweight heuristic analysis of the diff."""
    lines = diff.split("\n")
    added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    files_changed = len([l for l in lines if l.startswith("diff --git")])

    risks = []
    suggestions = []

    if "TODO" in diff or "FIXME" in diff:
        risks.append("Contains TODO/FIXME comments that should be resolved before merge")

    if re.search(r"console\.(log|warn|error)", diff):
        risks.append("Contains console.log/warn/error statements — may indicate leftover debugging")

    if re.search(r"\.only\(|it\.only|describe\.only", diff):
        risks.append("Contains .only() in test files — will skip other tests")

    if "process.env" in diff and "NEXT_PUBLIC_" not in diff:
        risks.append("Uses process.env without NEXT_PUBLIC_ prefix — may leak secrets to client")

    if re.search(r"try\s*\{[^}]*\}\s*catch\s*\{[^}]*\}", diff) and "console.error" not in diff:
        suggestions.append("Empty catch blocks detected — log or handle errors explicitly")

    if files_changed > 10:
        risks.append(f"Large PR: {files_changed} files changed — consider splitting into smaller PRs")

    if added > 500:
        suggestions.append(f"Large diff: {added} lines added — review for unnecessary changes")

    # Test file check
    test_files = [l for l in lines if l.startswith("+++ b/") and ("test" in l.lower() or "spec" in l.lower() or "__tests__" in l)]
    src_files = [l for l in lines if l.startswith("+++ b/") and l.endswith((".ts", ".tsx", ".js", ".jsx", ".py")) and "test" not in l.lower()]

    if len(src_files) > len(test_files) and len(test_files) == 0:
        suggestions.append("Source files changed without corresponding test updates")

    if not risks and not suggestions:
        suggestions.append("No obvious issues detected — looks clean!")

    confidence = "High" if not risks else ("Medium" if len(risks) <= 2 else "Low")

    return {
        "files_changed": files_changed,
        "lines_added": added,
        "lines_removed": removed,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
    }

def generate_report(owner, repo, number, analysis):
    """Generate structured Markdown report."""
    lines = []
    lines.append(f"# PR Review: {owner}/{repo}#{number}")
    lines.append(f"**Reviewed:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Confidence:** {analysis['confidence']}")
    lines.append("")

    lines.append("## Summary")
    lines.append(f"- **Files changed:** {analysis['files_changed']}")
    lines.append(f"- **Lines added:** {analysis['lines_added']}")
    lines.append(f"- **Lines removed:** {analysis['lines_removed']}")
    lines.append("")

    if analysis["risks"]:
        lines.append("## Identified Risks")
        for r in analysis["risks"]:
            lines.append(f"- ⚠️ {r}")
        lines.append("")

    if analysis["suggestions"]:
        lines.append("## Improvement Suggestions")
        for s in analysis["suggestions"]:
            lines.append(f"- 💡 {s}")
        lines.append("")

    if not analysis["risks"] and not analysis["suggestions"]:
        lines.append("✅ No risks or suggestions — LGTM!")
        lines.append("")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="AI-powered PR review")
    parser.add_argument("--pr", required=True, help="PR URL (https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", default="-", help="Output file (default: stdout)")
    args = parser.parse_args()

    diff, owner, repo, number = fetch_pr_diff(args.pr)
    if not diff.strip():
        print("Error: Empty diff — PR may have no changes or gh CLI not authenticated", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_diff(diff)
    report = generate_report(owner, repo, number, analysis)

    if args.output == "-":
        print(report)
    else:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to {args.output}")

if __name__ == "__main__":
    main()
