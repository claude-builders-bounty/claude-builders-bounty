#!/usr/bin/env python3
"""
claude-review â€” Claude Code sub-agent that reviews a PR and posts
a structured Markdown comment.

Usage:
  # CLI mode (standalone analysis)
  python review.py --pr https://github.com/owner/repo/pull/123

  # Claude Code integration (piped to Claude for AI review)
  python review.py --pr https://github.com/owner/repo/pull/123 --format diff | claude -p 'Review this PR diff...'

  # Via Claude Code hook
  claude-review --pr https://github.com/owner/repo/pull/123

Output: structured Markdown with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Overall confidence score
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def parse_pr_url(url):
    """Parse a GitHub PR URL into owner, repo, pr_number."""
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def github_api(path, token=None):
    """Make a GitHub API request and return the parsed JSON response."""
    headers = {
        "User-Agent": "claude-review/1.0",
        "Accept": "application/vnd.github.v3.diff",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"GitHub API error {e.code}: {e.reason}\n")
        sys.exit(1)


def github_api_json(path, token=None):
    """Make a GitHub API request and return JSON."""
    headers = {
        "User-Agent": "claude-review/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        data = e.read().decode("utf-8")
        sys.stderr.write(f"GitHub API error {e.code}: {data[:200]}\n")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Static analysis
# ---------------------------------------------------------------------------

SECURITY_PATTERNS = [
    (r'(?i)(password|secret|api_key|apikey|token)\s*[:=]\s*["\'][^"\']+["\']',
     "Possible hardcoded credential â€” use environment variables or a secrets manager"),
    (r'(?i)eval\s*\(', "eval() is dangerous â€” it can execute arbitrary code"),
    (r'(?i)exec\s*\(', "exec() can execute arbitrary code â€” avoid if possible"),
    (r'(?i)(innerHTML|outerHTML|dangerouslySetInnerHTML)',
     "Direct HTML injection can lead to XSS â€” use safe rendering"),
    (r'(?i)(SELECT\s+.*\s+FROM|INSERT\s+INTO|UPDATE\s+.*\s+SET)\s*\+',
     "SQL query concatenation â€” use parameterized queries to prevent SQL injection"),
    (r'(?i)(\bconsole\.log\b|\bprint_r\b|\bvar_dump\b|\bdd\b)\s*\(',
     "Debug statement left in code â€” remove before production"),
    (r'(?i)(TODO|FIXME|HACK|XXX|WORKAROUND)',
     "Unresolved todo â€” should be addressed before merging"),
    (r'(?i)(allow_eval|unsafe|bypass_security|disable_security)',
     "Security bypass detected â€” review carefully"),
    (r'\.env\.', "Environment file committed â€” should be in .gitignore"),
    (r'(?i)(rm\s+-rf|chmod\s+777)',
     "Dangerous filesystem operation â€” confirm this is intentional"),
]

IMPROVEMENT_PATTERNS = [
    (r'(?i)except\s*:', "Bare except clause â€” catches all errors including KeyboardInterrupt"),
    (r'(?i)try\s*:\s*\n\s*pass', "Empty try block â€” remove or add error handling"),
    (r'(?i)if\s+[a-z_]+\s*!=\s*None', "Use 'is not None' instead of '!= None' (PEP 8)"),
    (r'(?i)if\s+[a-z_]+\s*==\s*None', "Use 'is None' instead of '== None' (PEP 8)"),
    (r'(#\s*type:\s*ignore)', "Type ignore comment â€” try to fix the underlying type issue"),
    (r'(?i)(isinstance|type)\s*\(.*,\s*(str|int|float|bool|list|dict|set|tuple)\)',
     "Type check in production code â€” consider restructuring"),
    (r'(\"\"\"|\'\'\')\s*\n\s*\"\"\"', "Empty docstring â€” add documentation or remove"),
]


def analyze_diff(diff_text):
    """Run static analysis on a PR diff and return findings."""
    findings = {
        "summary": {"files_changed": 0, "additions": 0, "deletions": 0},
        "risks": [],
        "suggestions": [],
        "file_details": [],
    }

    current_file = None
    file_additions = 0
    file_deletions = 0
    file_diff_lines = []

    for line in diff_text.split("\n"):
        # Track file changes
        if line.startswith("+++ b/"):
            if current_file:
                findings["file_details"].append({
                    "file": current_file,
                    "additions": file_additions,
                    "deletions": file_deletions,
                })
            current_file = line[6:]
            file_additions = 0
            file_deletions = 0
            file_diff_lines = []
            findings["summary"]["files_changed"] += 1
        elif line.startswith("@@"):
            m = re.search(r'\+(?:(\d+),)?(\d+)', line)
            if m:
                # Reset line tracking at each hunk
                pass
        elif line.startswith("+") and not line.startswith("+++"):
            file_additions += 1
            findings["summary"]["additions"] += 1
            file_diff_lines.append(("+", line[1:]))
        elif line.startswith("-") and not line.startswith("---"):
            file_deletions += 1
            findings["summary"]["deletions"] += 1
            file_diff_lines.append(("-", line[1:]))

    # Add last file
    if current_file:
        findings["file_details"].append({
            "file": current_file,
            "additions": file_additions,
            "deletions": file_deletions,
        })

    # Run pattern analysis on added lines
    added_lines = [content for (op, content) in file_diff_lines if op == "+"]
    added_text = "\n".join(added_lines)

    for pattern, message in SECURITY_PATTERNS:
        matches = re.findall(pattern, added_text)
        if matches:
            findings["risks"].append({"severity": "high", "message": message, "count": len(matches)})

    for pattern, message in IMPROVEMENT_PATTERNS:
        matches = re.findall(pattern, added_text)
        if matches:
            findings["suggestions"].append({"message": message, "count": len(matches)})

    return findings


def generate_review(analysis, pr_info):
    """Generate the structured Markdown review."""
    s = analysis["summary"]

    # Calculate confidence score
    total_lines = s["additions"] + s["deletions"]
    risk_count = len(analysis["risks"])
    suggestion_count = len(analysis["suggestions"])

    if total_lines == 0:
        confidence = "N/A (no changes detected)"
    elif risk_count > 3:
        confidence = "Low"
    elif risk_count > 1:
        confidence = "Medium"
    else:
        confidence = "High"

    lines = []
    lines.append(f"## PR Review: {pr_info}")
    lines.append("")
    lines.append(f"_Generated by claude-review on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_")
    lines.append("")

    # Summary
    lines.append("### Summary")
    lines.append("")
    lines.append(f"This PR changes **{s['files_changed']} file(s)** with "
                 f"**+{s['additions']}** / **-{s['deletions']}** lines.")
    lines.append("")

    # File breakdown
    if analysis["file_details"]:
        lines.append("| File | + | - |")
        lines.append("|-----|---|---|")
        for f in sorted(analysis["file_details"], key=lambda x: -x["additions"] - x["deletions"]):
            lines.append(f"| {f['file']} | +{f['additions']} | -{f['deletions']} |")
        lines.append("")

    # Risks
    lines.append("### Identified Risks")
    lines.append("")
    if analysis["risks"]:
        for risk in analysis["risks"]:
            severity_icon = {"high": "ðŸ”´", "medium": "ðŸŸ¡", "low": "ðŸŸ¢"}.get(risk["severity"], "âšª")
            lines.append(f"- {severity_icon} **{risk['severity'].upper()}**: {risk['message']}"
                         f"{' (x' + str(risk['count']) + ')' if risk['count'] > 1 else ''}")
    else:
        lines.append("No security risks or dangerous patterns detected. âœ…")
    lines.append("")

    # Suggestions
    lines.append("### Improvement Suggestions")
    lines.append("")
    if analysis["suggestions"]:
        for sug in analysis["suggestions"]:
            lines.append(f"- ðŸ’¡ {sug['message']}"
                         f"{' (x' + str(sug['count']) + ')' if sug['count'] > 1 else ''}")
    else:
        lines.append("No style or improvement suggestions. âœ…")
    lines.append("")

    # Confidence
    lines.append(f"### Overall Confidence: **{confidence}**")
    lines.append("")
    if confidence == "High":
        lines.append("The changes are straightforward with minimal risk.")
    elif confidence == "Medium":
        lines.append("Some issues were found. Consider addressing them before merging.")
    elif confidence == "Low":
        lines.append("Multiple risks detected. A thorough manual review is recommended.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def call_claude_code(diff_text):
    """If Claude Code is available, pipe the diff for an AI review."""
    try:
        prompt = (
            "Review this GitHub PR diff and provide:\n"
            "1. A 2-3 sentence summary of the changes\n"
            "2. Identified risks and concerns (as a list)\n"
            "3. Improvement suggestions (as a list)\n"
            "4. An overall confidence score (High/Medium/Low)\n\n"
            "Format as structured Markdown.\n\n"
            f"{diff_text[:50000]}"
        )
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR review sub-agent")
    parser.add_argument("--pr", required=True, help="PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", help="GitHub token (defaults to GITHUB_TOKEN env)")
    parser.add_argument("--format", choices=["markdown", "diff"], default="markdown",
                        help="Output format (default: markdown)")
    parser.add_argument("--claude", action="store_true",
                        help="Use Claude Code CLI for AI review instead of static analysis")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN", "")

    try:
        owner, repo, pr_num = parse_pr_url(args.pr)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    pr_info = f"{owner}/{repo}#{pr_num}"

    # Fetch PR info
    pr_data = github_api_json(f"/repos/{owner}/{repo}/pulls/{pr_num}", token)
    pr_title = pr_data.get("title", "")
    pr_body = (pr_data.get("body", "") or "")[:2000]

    # Fetch diff
    diff_text = github_api(f"/repos/{owner}/{repo}/pulls/{pr_num}", token)

    if args.claude:
        # Try Claude Code AI review
        ai_review = call_claude_code(diff_text)
        if ai_review:
            lines = [
                f"## PR Review: {pr_info} â€” {pr_title}",
                "",
                ai_review,
            ]
            print("\n".join(lines))
            return
        else:
            print("Claude Code CLI not available. Falling back to static analysis.",
                  file=sys.stderr)

    if args.format == "diff":
        # Just output the diff for piping
        print(diff_text)
        return

    # Static analysis
    analysis = analyze_diff(diff_text)
    review = generate_review(analysis, f"{pr_info} â€” {pr_title}")
    print(review)


if __name__ == "__main__":
    main()

