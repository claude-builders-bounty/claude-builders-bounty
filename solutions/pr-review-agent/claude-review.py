#!/usr/bin/env python3
"""
claude-review — AI-powered PR review agent.

Analyzes a GitHub PR diff and produces a structured Markdown review with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score

Usage:
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review.py --pr owner/repo/123
  GITHUB_TOKEN=xxx python3 claude-review.py --pr https://github.com/owner/repo/pull/123
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


# ── GitHub API helpers ──────────────────────────────────────────────

def get_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    return token

def gh_request(url, accept="application/vnd.github.v3.diff"):
    """Make an authenticated GitHub API request."""
    token = get_token()
    headers = {
        "Accept": accept,
        "User-Agent": "claude-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP Error {e.code}: {e.reason}\n")
        sys.stderr.write(f"URL: {url}\n")
        if e.code == 404:
            sys.stderr.write("PR not found. Check the URL and token permissions.\n")
        elif e.code == 403:
            sys.stderr.write("Rate limited or insufficient permissions.\n")
        sys.exit(1)


def parse_pr_url(pr_url):
    """Parse a PR URL into owner, repo, number."""
    # Format: https://github.com/owner/repo/pull/123
    m = re.match(r"(?:https?://github\.com/)?([^/]+)/([^/]+)/?.*?pulls?/(\d+)", pr_url)
    if m:
        return m.group(1), m.group(2), m.group(3)
    # Format: owner/repo/123
    m = re.match(r"([^/]+)/([^/]+)/(\d+)", pr_url)
    if m:
        return m.group(1), m.group(2), m.group(3)
    sys.stderr.write(f"Invalid PR URL: {pr_url}\n")
    sys.stderr.write("Expected formats:\n")
    sys.stderr.write("  https://github.com/owner/repo/pull/123\n")
    sys.stderr.write("  owner/repo/123\n")
    sys.exit(1)


def get_pr_info(owner, repo, number):
    """Get PR metadata."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    raw = gh_request(url, accept="application/vnd.github.v3+json")
    return json.loads(raw)


def get_pr_diff(owner, repo, number):
    """Get the PR diff as text."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    return gh_request(url, accept="application/vnd.github.v3.diff")


def get_pr_commits(owner, repo, number):
    """Get the list of commits in the PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/commits"
    raw = gh_request(url, accept="application/vnd.github.v3+json")
    return json.loads(raw)


# ── Analysis engine ─────────────────────────────────────────────────

DANGEROUS_PATTERNS = [
    (r"(?i)\bconsole\.log\b", "risk", "Console log left in code"),
    (r"(?i)\bdebugger\b", "risk", "Debugger statement left in code"),
    (r"(?i)\btodo\b", "warning", "TODO left in code (incomplete work)"),
    (r"(?i)\bFIXME\b", "risk", "FIXME left in code (known bug area)"),
    (r"(?i)\bhack|hacky|workaround\b", "warning", "Hack/workaround detected"),
    (r"(?i)password|secret|apikey|api_key|token=\w{20,}", "risk", "Potential secret hardcoded"),
    (r"(?i)\bexec\s*\(", "risk", "Dynamic code execution (exec) detected"),
    (r"(?i)\beval\s*\(", "risk", "Dynamic code execution (eval) detected"),
    (r"(r\"|r')\s*\.\s*\+\s*", "warning", "Raw string concatenation (regex injection risk)"),
    (r"(?i)\.innerHTML\s*=", "risk", "XSS vulnerability: innerHTML assignment"),
    (r"(?i)\.outerHTML\s*=", "risk", "XSS vulnerability: outerHTML assignment"),
    (r"(?i)\bSELECT\b.+\bFROM\b.+\bWHERE\b", "info", "SQL query detected — verify parameterization"),
    (r"(?i)\bdrop\s+table\b", "risk", "DROP TABLE detected — destructive SQL"),
    (r"(?i)NODE_ENV\s*=\s*['\"]?development['\"]?", "warning", "Hardcoded NODE_ENV=development"),
    (r"(\d{10,})\s*[-+*/]\s*(\d{10,})", "info", "Large number arithmetic — overflow risk?"),
    (r"(?i)\bawait\b", "info", "Async operation — verify error handling"),
    (r"(?i)\.env\b", "warning", "Environment file reference"),
]


def analyze_diff(diff_text, pr_info, commits):
    """Analyze a PR diff and return structured review data."""
    files_changed = []
    total_additions = 0
    total_deletions = 0
    findings = []
    
    current_file = None
    file_additions = 0
    file_deletions = 0
    file_lines = []
    
    for line in diff_text.split("\n"):
        # Track file changes
        if line.startswith("+++ b/"):
            if current_file and file_lines:
                files_changed.append({
                    "path": current_file,
                    "additions": file_additions,
                    "deletions": file_deletions,
                    "lines": file_lines,
                })
            current_file = line[6:]
            file_additions = 0
            file_deletions = 0
            file_lines = []
        elif line.startswith("@@ "):
            continue
        elif line.startswith("+") and not line.startswith("+++"):
            file_additions += 1
            total_additions += 1
            file_lines.append(("+", line[1:]))
        elif line.startswith("-") and not line.startswith("---"):
            file_deletions += 1
            total_deletions += 1
            file_lines.append(("-", line[1:]))
    
    # Last file
    if current_file and file_lines:
        files_changed.append({
            "path": current_file,
            "additions": file_additions,
            "deletions": file_deletions,
            "lines": file_lines,
        })
    
    # Scan for patterns
    for file in files_changed:
        for line_type, line_content in file["lines"]:
            for pattern, severity, message in DANGEROUS_PATTERNS:
                if re.search(pattern, line_content):
                    findings.append({
                        "file": file["path"],
                        "line_content": line_content.strip()[:120],
                        "pattern": message,
                        "severity": severity,
                    })
                    break  # One finding per line
    
    # Count unique risk/warning/info findings
    risks = [f for f in findings if f["severity"] == "risk"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    infos = [f for f in findings if f["severity"] == "info"]
    
    # Determine confidence score
    total_lines = total_additions + total_deletions
    if total_lines == 0:
        confidence = "Low (empty PR)"
    elif len(risks) > 0 and len(risks) + len(warnings) > total_lines * 0.2:
        confidence = "Low"
    elif total_lines > 1000:
        confidence = "Medium (large diff, sampling applied)"
    elif total_lines < 10:
        confidence = "Low (very small change)"
    else:
        confidence = "High"
    
    # Generate summary
    pr_title = pr_info.get("title", "")
    pr_body = (pr_info.get("body") or "")[:200]
    
    summary_parts = []
    summary_parts.append(f"This PR modifies **{len(files_changed)}** files with **+{total_additions}/-{total_deletions}** lines.")
    
    if risks:
        summary_parts.append(f"Found **{len(risks)} potential risk(s)**, **{len(warnings)} warning(s)**.")
    else:
        summary_parts.append("No critical risks detected.")
    
    summary = " ".join(summary_parts)
    
    # Improvement suggestions
    suggestions = []
    if risks:
        risk_files = set(f["file"] for f in risks)
        for risk_file in list(risk_files)[:3]:
            suggestions.append(f"Review `{risk_file}` — contains potential risks that should be addressed")
    if total_lines > 500:
        suggestions.append("Consider splitting this PR into smaller, focused changes for easier review")
    if len(files_changed) > 10:
        suggestions.append("Large number of files changed — verify scope is focused")
    
    # Risk deduplication
    unique_risks = []
    seen_patterns = set()
    for f in findings:
        key = (f["file"], f["pattern"])
        if key not in seen_patterns:
            seen_patterns.add(key)
            unique_risks.append(f)
    
    return {
        "title": pr_title,
        "summary": summary,
        "files_changed": len(files_changed),
        "additions": total_additions,
        "deletions": total_deletions,
        "file_list": [f["path"] for f in files_changed],
        "risks": [f for f in unique_risks if f["severity"] == "risk"],
        "warnings": [f for f in unique_risks if f["severity"] == "warning"],
        "infos": [f for f in unique_risks if f["severity"] == "info"],
        "suggestions": suggestions,
        "confidence": confidence,
    }


def format_markdown(review, pr_url, owner, repo, number):
    """Format the review as structured Markdown."""
    lines = []
    
    lines.append("## 🔍 PR Review Report")
    lines.append("")
    lines.append(f"**PR:** [{owner}/{repo}#{number}]({pr_url})")
    lines.append(f"**Title:** {review['title']}")
    lines.append(f"**Confidence:** {review['confidence']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Summary
    lines.append("### 📋 Summary")
    lines.append("")
    lines.append(review['summary'])
    lines.append("")
    lines.append(f"Files changed: **{review['files_changed']}** | ")
    lines.append(f"+{review['additions']} / -{review['deletions']} lines")
    lines.append("")
    lines.append("Files:")
    for f in review['file_list']:
        lines.append(f"- `{f}`")
    lines.append("")
    
    # Risks
    if review['risks']:
        lines.append("### 🚫 Identified Risks")
        lines.append("")
        for risk in review['risks'][:10]:
            lines.append(f"- **{risk['pattern']}** in `{risk['file']}`")
            lines.append(f"  ```")
            lines.append(f"  {risk['line_content']}")
            lines.append(f"  ```")
        if len(review['risks']) > 10:
            lines.append(f"- *...and {len(review['risks']) - 10} more*")
        lines.append("")
    
    # Warnings
    if review['warnings']:
        lines.append("### ⚠️ Warnings")
        lines.append("")
        for w in review['warnings'][:8]:
            lines.append(f"- {w['pattern']} in `{w['file']}`")
            lines.append(f"  ```")
            lines.append(f"  {w['line_content']}")
            lines.append(f"  ```")
        if len(review['warnings']) > 8:
            lines.append(f"- *...and {len(review['warnings']) - 8} more*")
        lines.append("")
    
    # Suggestions
    if review['suggestions']:
        lines.append("### 💡 Improvement Suggestions")
        lines.append("")
        for s in review['suggestions']:
            lines.append(f"- {s}")
        lines.append("")
    
    # Confidence explanation
    lines.append("### 📊 Confidence Assessment")
    lines.append("")
    conf = review['confidence']
    if "High" in conf:
        lines.append("This analysis was performed with high confidence. "
                     "The diff is well-scoped and was fully analyzed.")
    elif "Low" in conf:
        lines.append("This analysis has limited confidence due to the "
                     "size or nature of the changes. Manual review is recommended.")
    else:
        lines.append("Review confidence is moderate. Key areas have been analyzed "
                     "but manual review of edge cases is advised.")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `claude-review` agent*")
    
    return "\n".join(lines)


# ── CLI entry point ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR review agent — analyzes PR diffs and produces structured reviews"
    )
    parser.add_argument("--pr", required=True, help="PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    owner, repo, number = parse_pr_url(args.pr)
    pr_url = f"https://github.com/{owner}/{repo}/pull/{number}"
    
    print(f"🔍 Fetching PR {owner}/{repo}#{number}...", file=sys.stderr)
    pr_info = get_pr_info(owner, repo, number)
    diff_text = get_pr_diff(owner, repo, number)
    commits = get_pr_commits(owner, repo, number)
    
    print(f"📊 Analyzing diff ({len(diff_text)} bytes)...", file=sys.stderr)
    review = analyze_diff(diff_text, pr_info, commits)
    
    markdown = format_markdown(review, pr_url, owner, repo, number)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(markdown)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
