#!/usr/bin/env python3
"""
Claude Review -- PR review agent for Claude Code.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md

Outputs structured Markdown review with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score: Low / Medium / High
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path


def parse_pr_url(url):
    """Extract owner, repo, pr_number from GitHub PR URL."""
    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) < 4 or parts[2] != "pull":
        raise ValueError(f"Invalid PR URL: {url}")
    return parts[0], parts[1], int(parts[3])


def fetch_pr_data(owner, repo, pr_number):
    """Fetch PR metadata and diff from GitHub API."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    req = urllib.request.Request(api_url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "claude-review")
    with urllib.request.urlopen(req, timeout=30) as resp:
        pr_data = json.loads(resp.read().decode("utf-8"))
    
    req2 = urllib.request.Request(api_url)
    req2.add_header("Accept", "application/vnd.github.v3.diff")
    req2.add_header("User-Agent", "claude-review")
    with urllib.request.urlopen(req2, timeout=30) as resp:
        diff_text = resp.read().decode("utf-8")
    
    return pr_data, diff_text


def parse_diff(diff_text):
    """Parse diff into structured file changes."""
    files = []
    current_file = None
    current_hunk = None
    
    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            if current_file:
                files.append(current_file)
            match = re.search(r"diff --git a/(.+) b/", line)
            filename = match.group(1) if match else "unknown"
            current_file = {
                "filename": filename,
                "additions": 0,
                "deletions": 0,
                "hunks": [],
                "is_new": False,
                "is_deleted": False,
            }
            current_hunk = None
        elif line.startswith("new file mode"):
            if current_file:
                current_file["is_new"] = True
        elif line.startswith("deleted file mode"):
            if current_file:
                current_file["is_deleted"] = True
        elif line.startswith("@@"):
            if current_file:
                current_hunk = {"lines": []}
                current_file["hunks"].append(current_hunk)
        elif current_hunk is not None:
            current_hunk["lines"].append(line)
            if line.startswith("+") and not line.startswith("+++"):
                current_file["additions"] += 1
            elif line.startswith("-") and not line.startswith("---"):
                current_file["deletions"] += 1
    
    if current_file:
        files.append(current_file)
    
    return files


def analyze_changes(files, pr_data):
    """Analyze diff and produce structured review."""
    total_additions = sum(f["additions"] for f in files)
    total_deletions = sum(f["deletions"] for f in files)
    file_count = len(files)
    
    summary = (
        f"This PR modifies {file_count} file(s) with "
        f"{total_additions} addition(s) and {total_deletions} deletion(s). "
        f"It addresses: {pr_data.get('title', 'No title')[:80]}."
    )
    
    risks = []
    
    if total_additions > 500:
        risks.append("Large change set (>500 additions) -- review carefully for unintended side effects")
    
    new_files = [f["filename"] for f in files if f["is_new"]]
    deleted_files = [f["filename"] for f in files if f["is_deleted"]]
    if new_files:
        risks.append(f"New files added: {', '.join(new_files[:3])} -- verify they are needed and properly integrated")
    if deleted_files:
        risks.append(f"Files deleted: {', '.join(deleted_files[:3])} -- confirm no downstream dependencies")
    
    security_patterns = [
        (r"eval\s*\(", "Use of eval() detected -- potential code injection risk"),
        (r"exec\s*\(", "Use of exec() detected -- potential code injection risk"),
        (r"os\.system\s*\(", "Use of os.system() detected -- consider subprocess with shell=False"),
        (r"subprocess\.call.*shell\s*=\s*True", "subprocess with shell=True detected -- command injection risk"),
        (r"password\s*=\s*['\"]", "Hardcoded password detected -- use environment variables or secrets manager"),
        (r"API_KEY\s*=\s*['\"]", "Hardcoded API key detected -- use environment variables"),
        (r"SECRET\s*=\s*['\"]", "Hardcoded secret detected -- use environment variables"),
        (r"TODO|FIXME|HACK|XXX", "TODO/FIXME comments present -- may indicate incomplete implementation"),
        (r"print\(.*password|print\(.*secret|print\(.*key", "Potentially sensitive data in print/debug statements"),
    ]
    
    for pattern, message in security_patterns:
        for f in files:
            for hunk in f["hunks"]:
                for line in hunk["lines"]:
                    if re.search(pattern, line, re.IGNORECASE):
                        risks.append(f"[{f['filename']}] {message}")
                        break
    
    if not risks:
        risks.append("No obvious risks identified by automated scan")
    
    suggestions = []
    
    if total_additions > 200 and total_deletions < 20:
        suggestions.append("Consider breaking this into smaller PRs for easier review")
    
    if any(f["filename"].endswith(".py") for f in files):
        suggestions.append("Add/update tests for new Python code")
        suggestions.append("Run type checker (mypy) on modified files")
    
    if any(f["filename"].endswith(".js") or f["filename"].endswith(".ts") for f in files):
        suggestions.append("Run linter (eslint) on modified JS/TS files")
        suggestions.append("Consider adding TypeScript types for new functions")
    
    if any(f["filename"].endswith(".md") for f in files):
        suggestions.append("Verify markdown renders correctly (no broken links)")
    
    if not any(f["filename"].endswith((".test.", "_test.", "spec.")) for f in files):
        suggestions.append("No test files modified -- confirm tests cover the changes")
    
    if pr_data.get("body"):
        body = pr_data.get("body", "")
        if len(body) < 50:
            suggestions.append("PR description is brief -- add context on what changed and why")
    else:
        suggestions.append("PR has no description -- add one explaining the change")
    
    if not suggestions:
        suggestions.append("No automated suggestions -- manual review recommended")
    
    risk_count = len([r for r in risks if not r.startswith("No obvious")])
    if risk_count >= 3 or total_additions > 500:
        confidence = "Low"
    elif risk_count >= 1 or total_additions > 200:
        confidence = "Medium"
    else:
        confidence = "High"
    
    return {
        "summary": summary,
        "risks": list(set(risks))[:5],
        "suggestions": suggestions[:5],
        "confidence": confidence,
        "stats": {
            "files": file_count,
            "additions": total_additions,
            "deletions": total_deletions,
        },
    }


def generate_markdown(review, pr_url, pr_data):
    """Generate structured Markdown review comment."""
    lines = [
        "## PR Review",
        "",
        f"**PR:** {pr_url}",
        f"**Title:** {pr_data.get('title', 'N/A')}",
        f"**Author:** @{pr_data.get('user', {}).get('login', 'N/A')}",
        f"**Stats:** {review['stats']['files']} files | +{review['stats']['additions']} / -{review['stats']['deletions']}",
        "",
        "---",
        "",
        "### Summary",
        "",
        review["summary"],
        "",
        "### Identified Risks",
        "",
    ]
    
    for risk in review["risks"]:
        lines.append(f"- {risk}")
    
    lines.extend([
        "",
        "### Improvement Suggestions",
        "",
    ])
    
    for suggestion in review["suggestions"]:
        lines.append(f"- {suggestion}")
    
    lines.extend([
        "",
        "### Confidence Score",
        "",
        f"**{review['confidence']}**",
        "",
        "---",
        "",
        "*Generated by claude-review -- an automated PR analysis tool.*",
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Review -- PR review agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    
    try:
        pr_data, diff_text = fetch_pr_data(owner, repo, pr_number)
    except Exception as e:
        print(f"Error fetching PR: {e}", file=sys.stderr)
        sys.exit(1)
    
    files = parse_diff(diff_text)
    review = analyze_changes(files, pr_data)
    markdown = generate_markdown(review, args.pr, pr_data)
    
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
