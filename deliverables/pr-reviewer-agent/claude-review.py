#!/usr/bin/env python3
"""
claude-review — PR Reviewer Agent

Takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --diff < diff.patch
    claude-review --diff-file diff.patch

Acceptance Criteria:
    - Works via CLI with GitHub PR URL
    - Structured Markdown output: Summary, Risks, Suggestions, Confidence
    - Tested on real GitHub PRs
"""

import argparse
import json
import os
import re
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' package required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

# ── Configuration ────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

if not GITHUB_TOKEN:
    print("Warning: GITHUB_TOKEN not set. PR diff fetching may fail.", file=sys.stderr)

# ── Risk detection patterns ──────────────────────────────────────────────────
RISK_PATTERNS = [
    # Security risks
    (r'eval\s*\(', '⚠️ Security: eval() usage detected'),
    (r'exec\s*\(', '⚠️ Security: exec() usage detected'),
    (r'sql\s*=\s*["\'].*\{', '⚠️ Security: Possible SQL injection (string formatting in SQL)'),
    (r'innerHTML\s*=', '⚠️ Security: Possible XSS (innerHTML assignment)'),
    (r'localStorage\.setItem\s*\(\s*["\']token["\']', '⚠️ Security: Token stored in localStorage'),
    (r'console\.(log|warn|error)\s*\(', '⚠️ Code Quality: console.log found in code'),
    (r'password\s*=\s*["\'][^"\']+["\']', '⚠️ Security: Hardcoded password detected'),
    (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', '⚠️ Security: Hardcoded API key detected'),
    (r'secret\s*=\s*["\'][^"\']+["\']', '⚠️ Security: Hardcoded secret detected'),
    (r'process\.env\.\w+\s*\?\?\s*["\'][^"\']+["\']', '⚠️ Config: Fallback to hardcoded value for env var'),

    # Code quality issues
    (r'\bTODO\b', '📝 Note: TODO comment found'),
    (r'\bFIXME\b', '📝 Note: FIXME comment found'),
    (r'\bHACK\b', '📝 Note: HACK comment found'),
    (r'var\s+\w+\s*=', '⚠️ Code Quality: Using var instead of let/const'),
    (r'==\s*null', '⚠️ Code Quality: Loose equality check (== null)'),
    (r'==\s*undefined', '⚠️ Code Quality: Loose equality check (== undefined)'),
    (r'!is\s+\w+', '⚠️ Code Quality: Double negation (!is)'),
    (r'\bdebugger\b', '⚠️ Code Quality: debugger statement found'),
    (r'//\s*$\n\s*//', '⚠️ Code Quality: Multiple consecutive comment lines'),

    # Performance concerns
    (r'for\s*\(\s*\w+\s+in\s+\w+\s*\)', '⚠️ Performance: for...in loop (consider Object.keys)'),
    (r'\.forEach\s*\(\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)', '⚠️ Performance: forEach with full arguments'),
    (r'new\s+Date\s*\(\s*["\']\d{4}-\d{2}-\d{2}', '⚠️ Performance: Date from string in loop'),
    (r'\.slice\s*\(\s*0', '⚠️ Performance: slice(0) creates unnecessary copy'),

    # Potential bugs
    (r'&&\s*true', '⚠️ Logic: Redundant && true'),
    (r'\|\|\s*false', '⚠️ Logic: Redundant || false'),
    (r'if\s*\(\s*true\s*\)', '⚠️ Logic: if(true) — dead code?'),
    (r'if\s*\(\s*false\s*\)', '⚠️ Logic: if(false) — dead code?'),
    (r'catch\s*\(\s*\)\s*{', '⚠️ Error Handling: Empty catch block'),
    (r'catch\s*\(\s*[\w_]+\s*\)\s*{\s*}', '⚠️ Error Handling: Empty catch block'),
    (r'\breturn\s*;\s*$', '⚠️ Logic: Bare return in non-void function?'),

    # Testing
    (r'it\s*\(\s*["\']should\b', '✅ Test: Test case found'),
    (r'describe\s*\(\s*["\']', '✅ Test: Test suite found'),
    (r'\.test\s*\(\s*["\']', '✅ Test: Test case found'),
    (r'\.expect\s*\(', '✅ Test: Assertion found'),
    (r'@pytest\.fixture', '✅ Test: pytest fixture found'),
    (r'func\s+Test\w+\s*\(', '✅ Test: Go test function found'),
]

COMPILED_RISKS = [(re.compile(p, re.MULTILINE | re.IGNORECASE), desc) for p, desc in RISK_PATTERNS]


def fetch_pr_diff(pr_url):
    # type: (str) -> str
    """Fetch the diff of a GitHub PR."""
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        print(f"Error: Invalid PR URL: {pr_url}", file=sys.stderr)
        sys.exit(1)

    owner, repo, pr_number = match.groups()

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # Try GitHub API first
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        resp = requests.get(api_url, headers=headers, timeout=30)
        if resp.status_code == 200:
            pr_data = resp.json()
            diff_url = pr_data.get("diff_url", "")
            if diff_url:
                diff_resp = requests.get(diff_url, headers=headers, timeout=30)
                if diff_resp.status_code == 200:
                    return diff_resp.text
    except Exception as e:
        print(f"Warning: GitHub API fetch failed: {e}", file=sys.stderr)

    # Fallback: try the diff URL directly
    diff_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
    try:
        diff_resp = requests.get(diff_url, headers=headers, timeout=30)
        if diff_resp.status_code == 200:
            return diff_resp.text
    except Exception as e:
        print(f"Error: Could not fetch PR diff: {e}", file=sys.stderr)
        sys.exit(1)

    print("Error: Could not retrieve PR diff", file=sys.stderr)
    sys.exit(1)


def analyze_diff(diff_content):
    # type: (str) -> dict
    """Analyze a PR diff and return structured review data."""
    # Count changes
    additions = len(re.findall(r'^\+', diff_content, re.MULTILINE)) - len(re.findall(r'^\+\+\+', diff_content, re.MULTILINE))
    deletions = len(re.findall(r'^-', diff_content, re.MULTILINE)) - len(re.findall(r'^---', diff_content, re.MULTILINE))
    files_changed = len(re.findall(r'^diff --git ', diff_content, re.MULTILINE))

    # Detect changed files
    changed_files = re.findall(r'^\+\+\+ b/(.+)$', diff_content, re.MULTILINE)
    changed_files = sorted(set(changed_files))

    # Detect language
    ext_counts = {}
    for f in changed_files:
        ext = Path(f).suffix.lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
    primary_ext = max(ext_counts, key=ext_counts.get) if ext_counts else ".txt"

    # Detect risk patterns
    risks_found = []
    suggestions = []

    for pattern, description in COMPILED_RISKS:
        matches = pattern.findall(diff_content)
        if matches:
            count = len(matches)
            # Only report unique descriptions
            existing = [r for r in risks_found if r["description"] == description]
            if not existing:
                risks_found.append({
                    "description": description,
                    "count": count,
                })

    # Generate summary
    if additions > 0 and deletions == 0:
        change_type = "addition"
        summary = f"This PR introduces **{additions} new lines** across **{files_changed} file(s)**."
    elif deletions > 0 and additions == 0:
        change_type = "deletion"
        summary = f"This PR removes **{deletions} lines** across **{files_changed} file(s)**."
    elif additions > deletions:
        change_type = "modification"
        summary = f"This PR **adds {additions} lines and removes {deletions} lines** across **{files_changed} file(s)**."
    else:
        change_type = "modification"
        summary = f"This PR **removes {deletions} lines and adds {additions} lines** across **{files_changed} file(s)**."

    # Determine confidence
    risk_count = len(risks_found)
    if risk_count == 0:
        confidence = "High"
    elif risk_count <= 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Generate suggestions based on file types
    if any(f.endswith(('.js', '.ts', '.jsx', '.tsx')) for f in changed_files):
        suggestions.append("Consider adding TypeScript types for new functions and variables")
        suggestions.append("Add unit tests for new exported functions")
    if any(f.endswith(('.py',)) for f in changed_files):
        suggestions.append("Add type hints for function parameters and return values")
        suggestions.append("Consider adding docstrings for public functions")
    if any(f.endswith(('.sql',)) for f in changed_files):
        suggestions.append("Add indexes for frequently queried columns")
        suggestions.append("Consider adding constraints for data integrity")
    if any(f.endswith(('.md', '.txt')) for f in changed_files):
        suggestions.append("Update CHANGELOG.md if this is a user-facing change")

    # Add general suggestions
    if risk_count > 0:
        suggestions.append(f"Review {risk_count} potential issue(s) flagged below before merging")
    if files_changed > 5:
        suggestions.append("Consider splitting this PR into smaller, focused changes")

    return {
        "summary": summary,
        "change_type": change_type,
        "files_changed": files_changed,
        "changed_files": changed_files,
        "additions": additions,
        "deletions": deletions,
        "risks_found": risks_found,
        "suggestions": suggestions,
        "confidence": confidence,
        "primary_language": primary_ext,
    }


def format_review(analysis, pr_url):
    # type: (dict, str) -> str
    """Format the analysis as a structured Markdown review."""
    lines = []
    lines.append("## 🔍 PR Review")
    lines.append("")
    lines.append(f"> **Source:** [{pr_url}]({pr_url})")
    lines.append(f"> **Reviewed:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # Summary
    lines.append("### 📋 Summary")
    lines.append("")
    lines.append(analysis["summary"])
    lines.append("")

    # Change stats
    lines.append("### 📊 Change Stats")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Files changed | {analysis['files_changed']} |")
    lines.append(f"| Lines added | {analysis['additions']} |")
    lines.append(f"| Lines removed | {analysis['deletions']} |")
    lines.append(f"| Primary language | {analysis['primary_language']} |")
    lines.append("")

    # Changed files
    if analysis["changed_files"]:
        lines.append("### 📁 Changed Files")
        lines.append("")
        for f in analysis["changed_files"][:20]:  # Limit to 20
            lines.append(f"- `{f}`")
        if len(analysis["changed_files"]) > 20:
            lines.append(f"- ... and {len(analysis['changed_files']) - 20} more")
        lines.append("")

    # Risks
    lines.append("### ⚠️ Identified Risks")
    lines.append("")
    if analysis["risks_found"]:
        for risk in analysis["risks_found"]:
            lines.append(f"- {risk['description']} ({risk['count']} occurrence{'s' if risk['count'] > 1 else ''})")
    else:
        lines.append("✅ No significant risks detected.")
    lines.append("")

    # Suggestions
    lines.append("### 💡 Improvement Suggestions")
    lines.append("")
    if analysis["suggestions"]:
        for s in analysis["suggestions"]:
            lines.append(f"- {s}")
    else:
        lines.append("No specific suggestions at this time.")
    lines.append("")

    # Confidence
    lines.append("### 🎯 Confidence Score")
    lines.append("")
    emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(analysis["confidence"], "⚪")
    lines.append(f"**{emoji} {analysis['confidence']}**")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by `claude-review` PR Reviewer Agent*")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="PR Reviewer Agent — Analyze a GitHub PR and generate a structured review"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", help="GitHub PR URL to review")
    group.add_argument("--diff", help="Read diff from stdin (use with pipe)")
    group.add_argument("--diff-file", help="Read diff from file")
    group.add_argument("--demo", action="store_true", help="Run with demo diff")

    args = parser.parse_args()

    # Get diff content
    if args.demo:
        diff_content = """diff --git a/src/utils/math.js b/src/utils/math.js
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/src/utils/math.js
@@ -0,0 +1,25 @@
+/**
+ * Math utility functions
+ */
+
+export function add(a, b) {
+    return a + b;
+}
+
+export function multiply(a, b) {
+    return a * b;
+}
+
+// TODO: Add divide and subtract functions
+export function calculate(operation, a, b) {
+    if (operation === 'add') return add(a, b);
+    if (operation === 'multiply') return multiply(a, b);
+    console.log('Unknown operation:', operation);
+    return null;
+}
+
+const API_KEY = "sk-demo-key-12345";
+
+export function fetchData(url) {
+    return fetch(url, { headers: { 'Authorization': `Bearer ${API_KEY}` } });
+}
"""
    elif args.diff:
        diff_content = sys.stdin.read()
    elif args.diff_file:
        with open(args.diff_file, "r") as f:
            diff_content = f.read()
    else:
        diff_content = fetch_pr_diff(args.pr)

    # Analyze and format
    analysis = analyze_diff(diff_content)
    review = format_review(analysis, args.pr or "local diff")

    print(review)

    # Also write to file if output specified
    if os.environ.get("REVIEW_OUTPUT"):
        output_path = os.environ["REVIEW_OUTPUT"]
        with open(output_path, "w") as f:
            f.write(review)
        print(f"\nReview saved to: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
