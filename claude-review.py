#!/usr/bin/env python3
"""
claude-review.py — Claude Code PR Review Agent
Analyzes a GitHub PR diff and returns a structured Markdown review.

Usage:
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
  python3 claude-review.py --pr-diff /path/to/diff.txt
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


def fetch(url, token=None):
    """Fetch a URL with optional GitHub token."""
    headers = {
        "User-Agent": "claude-review-agent/1.0",
        "Accept": "application/vnd.github.v3.diff",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def parse_pr_url(url):
    """Parse a GitHub PR URL into owner/repo/number."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        print(f"❌ Invalid PR URL: {url}", file=sys.stderr)
        print("   Expected: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    return m.group(1), m.group(2), int(m.group(3))


def get_pr_info(owner, repo, number, token):
    """Get PR metadata from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    headers = {
        "User-Agent": "claude-review-agent/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def analyze_diff(diff_text, pr_info=None):
    """Analyze a PR diff and produce a structured review."""
    if not diff_text.strip():
        return {
            "summary": "No changes detected — the diff is empty.",
            "risks": [],
            "suggestions": [],
            "confidence": "High",
            "stats": {"files": 0, "additions": 0, "deletions": 0},
        }

    files = []
    current_file = ""
    file_changes = {}
    stats = {"files": 0, "additions": 0, "deletions": 0}
    findings = {"todos": [], "debug_code": [], "large_files": [], "missing_types": []}

    for line in diff_text.split("\n"):
        # Detect file headers
        fm = re.match(r"^\+\+\+\s+b/(.*)", line)
        if fm:
            current_file = fm.group(1)
            files.append(current_file)
            stats["files"] += 1
            file_changes[current_file] = {"additions": 0, "deletions": 0}
            continue

        # Count changes
        if line.startswith("+"):
            stats["additions"] += 1
            if current_file:
                file_changes[current_file]["additions"] += 1

            # Detect TODO/FIXME/HACK
            if re.search(r"(TODO|FIXME|HACK|XXX|TEMP)", line, re.IGNORECASE):
                findings["todos"].append(
                    f"`{current_file}`: `{line.strip()[:80]}`"
                )

            # Detect debug code
            if re.search(
                r"(console\.log|print\(|pdb\.|ipdb\.|trace\b|debugger|var_dump|dd\()",
                line,
            ):
                findings["debug_code"].append(
                    f"`{current_file}`: `{line.strip()[:60]}`"
                )

        elif line.startswith("-") and not line.startswith("---"):
            stats["deletions"] += 1
            if current_file:
                file_changes[current_file]["deletions"] += 1

        # Track large files
        if current_file and file_changes.get(current_file, {}).get("additions", 0) > 200:
            if current_file not in findings["large_files"]:
                findings["large_files"].append(current_file)

    # Build risks
    risks = []
    if findings["todos"]:
        risks.append(
            f"**Unresolved TODOs/FIXMEs** ({len(findings['todos'])} found): "
            f"{len(findings['todos'])} marker(s) left in code. "
            "Review and resolve before merging."
        )
    if findings["debug_code"]:
        risks.append(
            f"**Debug code left in production** ({len(findings['debug_code'])} instances): "
            "Remove console.log/print statements before deployment."
        )
    if findings["large_files"]:
        risks.append(
            f"**Large file changes** ({len(findings['large_files'])} files >200 lines): "
            "Consider splitting into smaller, focused PRs for easier review."
        )
    if stats["deletions"] == 0 and stats["additions"] > 0:
        risks.append(
            "**No deletions — possible dead code accumulation.** "
            "Old code paths should be removed when replacements are added."
        )

    # Build suggestions
    suggestions = []
    if findings["todos"]:
        suggestions.append(
            "**Resolve markers:** Convert TODOs to GitHub issues "
            "and replace FIXMEs with actual fixes before merging."
        )
    if findings["debug_code"]:
        suggestions.append(
            "**Remove debug output:** Use structured logging instead of print/console.log "
            "for any runtime diagnostics that should remain."
        )
    if findings["large_files"]:
        suggestions.append(
            "**Split large changes:** Break file with 200+ line changes into "
            "separate, focused PRs for faster review cycles."
        )
    
    # Add generic suggestions
    total_changes = stats["additions"] + stats["deletions"]
    if total_changes < 10:
        suggestions.append(
            "**Add tests:** This change is small — ideal candidate for adding "
            "or updating unit tests."
        )
    if total_changes > 500:
        suggestions.append(
            "**Review scope:** Large PRs (>500 changes) are harder to review. "
            "Consider splitting into logical chunks."
        )

    # Determine confidence
    if not risks:
        confidence = "High"
    elif len(risks) <= 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Build summary
    pr_title = pr_info.get("title", "") if pr_info else ""
    pr_author = pr_info.get("user", {}).get("login", "") if pr_info else ""

    summary_parts = []
    if pr_title:
        summary_parts.append(f"PR **\"{pr_title}\"** ")
    if pr_author:
        summary_parts.append(f"by **@{pr_author}** ")
    summary_parts.append(
        f"modifies **{stats['files']} file(s)** "
        f"with **+{stats['additions']}/-{stats['deletions']}** lines."
    )

    if not risks:
        summary_parts.append(
            " No critical issues detected — the changes appear safe and well-structured."
        )
    else:
        summary_parts.append(
            f" {len(risks)} risk(s) identified — see below for details."
        )

    return {
        "summary": "".join(summary_parts),
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "stats": stats,
        "findings": findings,
    }


def render_markdown(review, pr_url, owner, repo, number):
    """Render the review as structured Markdown."""
    emoji_map = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    confidence_emoji = emoji_map.get(review["confidence"], "⚪")

    lines = [
        f"## 🔍 PR Review: {owner}/{repo}#{number}",
        "",
        f"**Confidence:** {confidence_emoji} {review['confidence']}",
        f"**Stats:** +{review['stats']['additions']}/-{review['stats']['deletions']} lines in {review['stats']['files']} files",
        "",
        "---",
        "",
        "### 📝 Summary",
        "",
        review["summary"],
        "",
    ]

    if review["risks"]:
        lines += [
            "---",
            "",
            "### ⚠️ Identified Risks",
            "",
        ]
        for i, risk in enumerate(review["risks"], 1):
            lines.append(f"{i}. {risk}")
            lines.append("")

    if review["suggestions"]:
        lines += [
            "---",
            "",
            "### 💡 Improvement Suggestions",
            "",
        ]
        for i, suggestion in enumerate(review["suggestions"], 1):
            lines.append(f"{i}. {suggestion}")
            lines.append("")

    if review.get("findings", {}).get("todos"):
        lines += [
            "### 📌 TODO/FIXME Locations",
            "",
        ]
        for todo in review["findings"]["todos"][:10]:
            lines.append(f"- {todo}")
        lines.append("")

    lines += [
        "---",
        "",
        f"_Review generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_",
        f"_[PR Link]({pr_url}) — Claude Builders Bounty #4_",
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — structured Markdown reviews"
    )
    parser.add_argument("--pr", help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--pr-diff", help="Path to a local diff file")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    args = parser.parse_args()

    if not args.pr and not args.pr_diff:
        parser.print_help()
        print("\n❌ Provide either --pr or --pr-diff")
        sys.exit(1)

    token = args.token or os.environ.get("GITHUB_TOKEN", "")

    if args.pr:
        owner, repo, number = parse_pr_url(args.pr)
        pr_info = get_pr_info(owner, repo, number, token)
        diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
        diff_text = fetch(diff_url, token)
        pr_url = args.pr
    else:
        owner, repo, number = "local", "repo", 0
        pr_info = None
        with open(args.pr_diff) as f:
            diff_text = f.read()
        pr_url = f"file://{os.path.abspath(args.pr_diff)}"

    review = analyze_diff(diff_text, pr_info)
    markdown = render_markdown(review, pr_url, owner, repo, number)

    if args.output:
        with open(args.output, "w") as f:
            f.write(markdown)
        print(f"✅ Review written to {args.output}")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
