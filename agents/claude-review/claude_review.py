#!/usr/bin/env python3
"""
claude-review — A Claude Code sub-agent that reviews GitHub PRs.
Fetches PR diffs via GitHub API and generates structured code reviews.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr 123 --repo owner/repo
  claude-review --repo owner/repo --pr 123 --output review.md
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


def api_request(url, token=None):
    """Make a GitHub API request."""
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"❌ API Error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def api_request_json(url, token=None):
    """Make a GitHub API request and return JSON."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if hasattr(e, 'read') else ""
        print(f"❌ API Error {e.code}: {e.reason}\n{error_body[:200]}", file=sys.stderr)
        sys.exit(1)


def parse_pr_url(pr_url):
    """Parse a GitHub PR URL into owner, repo, pr_number."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, pr_url)
    if not match:
        print(f"❌ Invalid PR URL: {pr_url}", file=sys.stderr)
        print("   Expected: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2), match.group(3)


def generate_review(diff_text, pr_info, files_data):
    """Generate a structured code review from a PR diff."""
    
    warnings = []
    suggestions = []
    
    # Parse diff into per-file hunks
    current_file = None
    files_changed = set()
    total_additions = 0
    total_deletions = 0
    large_files = []
    
    for line in diff_text.split("\n"):
        # File header
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            continue
        if line.startswith("diff --git"):
            continue
        if line.startswith("@@ "):
            # Hunk header - extract line numbers
            match = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))?", line)
            if match:
                continue
        if line.startswith("+") and not line.startswith("+++"):
            total_additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            total_deletions += 1
    
    # Analyze each file from the files API
    for f in files_data:
        filename = f.get("filename", "")
        files_changed.add(filename)
        status = f.get("status", "modified")
        additions = f.get("additions", 0)
        deletions = f.get("deletions", 0)
        
        # Flag large files
        if additions + deletions > 200:
            large_files.append((filename, additions + deletions))
            warnings.append(f"Large file `{filename}` ({additions + deletions} lines changed) — consider splitting into smaller PRs")
        
        # Flag new files
        if status == "added" and additions > 300:
            warnings.append(f"Large new file `{filename}` ({additions} lines) — consider whether this could be broken up")
    
    total_changes = total_additions + total_deletions
    
    # Generic checks
    if "TODO" in diff_text or "FIXME" in diff_text:
        suggestions.append("Contains TODO/FIXME comments — should these be addressed before merge?")
    
    if "print(" in diff_text or "console.log" in diff_text:
        suggestions.append("Contains debug print/log statements that should be removed in production")
    
    if "password" in diff_text.lower() or "secret" in diff_text.lower() or "api_key" in diff_text.lower():
        if "test" not in diff_text.lower():
            warnings.append("⚠️ Possible secret/key detected in diff — verify no credentials are being committed")
    
    if "import " in diff_text or "require(" in diff_text or "from " in diff_text:
        new_imports = re.findall(r"^\+.*(?:import|require|from)\s+[\"']([^\"']+)[\"']", diff_text, re.MULTILINE)
        if new_imports:
            suggestions.append(f"New dependencies/modules added: {', '.join(new_imports[:5])}")
    
    # Confidence scoring
    confidence = "High"
    if total_changes > 500:
        confidence = "Low"
    elif total_changes > 200:
        confidence = "Medium"
    
    # Build the review
    review = f"""# 🔍 PR Review

## 📋 Overview

**PR:** [{pr_info['full_name']}#{pr_info['number']}]({pr_info['url']})
**Title:** {pr_info.get('title', 'N/A')}
**Author:** {pr_info.get('user', {}).get('login', 'N/A')}
**Status:** {pr_info.get('state', 'N/A')}
**Files Changed:** {len(files_changed)}
**Changes:** +{total_additions}/-{total_deletions} ({total_changes} total)

## 📝 Summary of Changes

This PR modifies {len(files_changed)} files with {total_changes} lines changed across {len(set(f.get('filename', '') for f in files_data))} file(s).

"""
    
    # Group files by type
    if files_data:
        review += "### Files Modified\n\n"
        for f in files_data:
            filename = f.get("filename", "")
            status = f.get("status", "modified")
            adds = f.get("additions", 0)
            dels = f.get("deletions", 0)
            emoji = {"added": "🟢", "modified": "🟡", "removed": "🔴", "renamed": "🔵"}.get(status, "⚪")
            review += f"- {emoji} **{filename}** (+{adds}/-{dels}) — {status}\n"
        review += "\n"
    
    # Risks
    if warnings:
        review += "## ⚠️ Identified Risks\n\n"
        for w in warnings:
            review += f"- {w}\n"
        review += "\n"
    else:
        review += "## ✅ Identified Risks\n\n- None detected by automated analysis\n\n"
    
    # Suggestions
    if suggestions:
        review += "## 💡 Improvement Suggestions\n\n"
        for s in suggestions:
            review += f"- {s}\n"
        review += "\n"
    else:
        review += "## 💡 Improvement Suggestions\n\n- None from automated analysis. Consider manual review for logic correctness.\n\n"
    
    # Confidence
    review += f"""## 📊 Confidence Score

**{confidence}**

"""
    if confidence == "High":
        review += "Small, focused change with no obvious issues detected.\n"
    elif confidence == "Medium":
        review += "Moderate-sized change. Manual review recommended for critical sections.\n"
    else:
        review += "Large change. Thorough manual review strongly recommended.\n"
    
    return review


def main():
    parser = argparse.ArgumentParser(
        description="🔍 claude-review — Automated PR Review Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--pr", type=str, help="PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--repo", type=str, help="Repository (owner/name)")
    parser.add_argument("--number", type=str, help="PR number")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")
    parser.add_argument("--diff-only", action="store_true", help="Only fetch and print the diff")
    parser.add_argument("--json", action="store_true", help="Output PR info as JSON")
    
    args = parser.parse_args()
    
    # Get GitHub token
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    
    # Parse PR identifiers
    if args.pr:
        owner, repo, pr_number = parse_pr_url(args.pr)
    elif args.repo and args.number:
        parts = args.repo.split("/")
        owner, repo = parts[0], parts[1]
        pr_number = args.number
    else:
        parser.print_help()
        print("\n❌ Provide --pr URL or --repo owner/name --number PR_NUMBER", file=sys.stderr)
        sys.exit(1)
    
    # Fetch PR info
    print(f"🔍 Fetching PR {owner}/{repo}#{pr_number}...", file=sys.stderr)
    
    pr_info = api_request_json(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
        token
    )
    pr_info['full_name'] = f"{owner}/{repo}"
    pr_info['url'] = f"https://github.com/{owner}/{repo}/pull/{pr_number}"
    
    # Fetch files
    files_data = api_request_json(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
        token
    )
    
    # Fetch diff
    diff_text = api_request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
        token
    )
    
    if args.diff_only:
        print(diff_text)
        return
    
    if args.json:
        print(json.dumps({"pr": pr_info, "files": files_data}, indent=2))
        return
    
    # Generate review
    review = generate_review(diff_text, pr_info, files_data)
    
    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(review)
    
    print(file=sys.stderr)
    print(f"📊 {len(files_data)} files analyzed", file=sys.stderr)
    print(f"✨ Review generated successfully", file=sys.stderr)


if __name__ == "__main__":
    main()
