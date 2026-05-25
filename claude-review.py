#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent for PR review
Usage: python3 claude-review.py --pr https://github.com/owner/repo/pull/123

Analyzes a GitHub PR diff and returns a structured Markdown review.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def parse_pr_url(url):
    """Extract owner, repo, pr_number from a PR URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    m = re.match(pattern, url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))

def get_pr_diff(owner, repo, pr_number):
    """Fetch the PR diff from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")

def get_pr_info(owner, repo, pr_number):
    """Fetch PR metadata."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def analyze_diff(diff_text, pr_info):
    """Analyze the PR diff and extract insights."""
    files_changed = []
    current_file = None
    total_additions = 0
    total_deletions = 0
    risky_patterns = []
    improvement_areas = []
    file_types = set()

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            if current_file:
                files_changed.append(current_file)
            current_file = {"path": "", "additions": 0, "deletions": 0}
        elif line.startswith("--- a/"):
            if current_file:
                current_file["path"] = line[6:]
                ext = os.path.splitext(current_file["path"])[1]
                if ext:
                    file_types.add(ext)
        elif line.startswith("+++ b/"):
            pass
        elif line.startswith("@@"):
            # Parse hunk header for line counts
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                pass
        elif line.startswith("+") and not line.startswith("+++"):
            if current_file:
                current_file["additions"] += 1
            total_additions += 1
            # Check for risky patterns
            stripped = line[1:].strip()
            if any(p in stripped.lower() for p in ["password", "secret", "token", "api_key", "api-key"]):
                risky_patterns.append(("Possible secret exposure", f"{stripped[:60]}"))
            if "exec" in stripped.lower() or "eval(" in stripped.lower():
                risky_patterns.append(("Code injection risk (eval/exec)", f"{stripped[:60]}"))
        elif line.startswith("-") and not line.startswith("---"):
            if current_file:
                current_file["deletions"] += 1
            total_deletions += 1

    if current_file:
        files_changed.append(current_file)

    # Generate improvement suggestions
    if total_additions > 500:
        improvement_areas.append("Large PR size — consider splitting into smaller, focused changes")
    if len(files_changed) > 10:
        improvement_areas.append("PR touches many files — verify scope is justified")
    if ".py" in file_types and not any("test" in f["path"].lower() for f in files_changed):
        improvement_areas.append("No test files detected — consider adding tests")
    if "TODO" in diff_text or "FIXME" in diff_text:
        improvement_areas.append("Contains TODO/FIXME markers — resolve before merge")
    if "print(" in diff_text and ".py" in file_types:
        improvement_areas.append("Contains debug print statements — replace with proper logging")
    if "except:" in diff_text and ".py" in file_types:
        improvement_areas.append("Bare except clause — use specific exception types instead")

    return {
        "files_changed": files_changed,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "total_files": len(files_changed),
        "risky_patterns": risky_patterns,
        "improvement_areas": improvement_areas,
        "file_types": list(file_types),
        "pr_title": pr_info.get("title", ""),
        "pr_body": pr_info.get("body", ""),
        "pr_author": pr_info.get("user", {}).get("login", "unknown"),
    }

def generate_review(analysis):
    """Generate structured Markdown review."""
    lines = []
    lines.append("## 🔍 PR Review Report")
    lines.append("")
    lines.append(f"**PR:** {analysis['pr_title']}")
    lines.append(f"**Author:** @{analysis['pr_author']}")
    lines.append(f"**Scope:** {analysis['total_files']} files | +{analysis['total_additions']}/-{analysis['total_deletions']} lines")
    lines.append(f"**File types:** {', '.join(analysis['file_types']) if analysis['file_types'] else 'N/A'}")
    lines.append("")

    # Summary
    lines.append("### 📋 Summary of Changes")
    lines.append("")
    summary = f"This PR modifies **{analysis['total_files']} files** with **+{analysis['total_additions']}/-{analysis['total_deletions']} lines** across {len(analysis['file_types'])} file type(s). "
    if analysis['pr_body']:
        summary += f""""{analysis['pr_body'][:200]}""""
    else:
        summary += "No description provided."
    lines.append(summary)
    lines.append("")

    # File list
    lines.append("**Modified files:**")
    for f in analysis['files_changed'][:15]:
        lines.append(f"- `{f['path']}` (+{f['additions']}/-{f['deletions']})")
    if len(analysis['files_changed']) > 15:
        lines.append(f"- *... and {len(analysis['files_changed']) - 15} more files*")
    lines.append("")

    # Risks
    lines.append("### ⚠️ Identified Risks")
    lines.append("")
    if analysis['risky_patterns']:
        for risk, detail in analysis['risky_patterns']:
            lines.append(f"- **{risk}**")
            lines.append(f"  - `{detail}`")
    else:
        lines.append("✅ No critical risks detected. The changes appear safe.")
    lines.append("")

    # Improvements
    lines.append("### 💡 Improvement Suggestions")
    lines.append("")
    if analysis['improvement_areas']:
        for imp in analysis['improvement_areas']:
            lines.append(f"- {imp}")
    else:
        lines.append("No specific improvements suggested — looks clean!")
    lines.append("")

    # Confidence score
    score = "High"
    reasons = []
    if analysis['risky_patterns']:
        score = "Low"
        reasons.append(f"Found {len(analysis['risky_patterns'])} risky pattern(s)")
    if analysis['total_additions'] > 1000:
        if score == "High":
            score = "Medium"
        reasons.append(f"Large diff size ({analysis['total_additions']} additions)")
    if not analysis['pr_body']:
        if score == "High":
            score = "Medium"
        reasons.append("No PR description provided")

    lines.append("### 🎯 Confidence Score")
    lines.append("")
    lines.append(f"**{score}**")
    if reasons:
        for r in reasons:
            lines.append(f"- {r}")
    lines.append("")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR review sub-agent")
    parser.add_argument("--pr", required=True, help="PR URL (e.g., https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()

    print(f"Fetching PR: {args.pr}", file=sys.stderr)
    owner, repo, pr_number = parse_pr_url(args.pr)
    pr_info = get_pr_info(owner, repo, pr_number)
    diff_text = get_pr_diff(owner, repo, pr_number)
    
    print(f"Analyzing {len(diff_text)} bytes of diff...", file=sys.stderr)
    analysis = analyze_diff(diff_text, pr_info)
    review = generate_review(analysis)
    
    print(review)

if __name__ == "__main__":
    main()
