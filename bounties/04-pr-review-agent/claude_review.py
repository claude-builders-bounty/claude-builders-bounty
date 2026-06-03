#!/usr/bin/env python3
"""
Claude Code PR Review Agent

Takes a PR URL or diff as input, analyzes it, and returns a structured
Markdown review comment.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --diff patch.diff
    claude-review --file changes.patch

Output:
    Markdown with: Summary, Risks, Suggestions, Confidence
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import urllib.request
import urllib.error


def fetch_pr_diff(pr_url: str) -> tuple[str, dict]:
    """
    Fetch PR diff and metadata from GitHub.
    Returns: (diff_text, pr_metadata)
    """
    # Parse PR URL: https://github.com/owner/repo/pull/123
    parsed = urlparse(pr_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 4 or path_parts[2] != "pull":
        raise ValueError(f"Invalid PR URL: {pr_url}")

    owner, repo, _, number = path_parts[0], path_parts[1], path_parts[2], path_parts[3]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"

    # Fetch PR metadata
    req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        pr_data = json.loads(resp.read())

    # Fetch diff
    diff_url = pr_data.get("diff_url") or f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    req = urllib.request.Request(diff_url, headers={"Accept": "application/vnd.github.v3.diff"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        diff_text = resp.read().decode("utf-8", errors="replace")

    metadata = {
        "title": pr_data.get("title", ""),
        "author": pr_data.get("user", {}).get("login", "?"),
        "base": pr_data.get("base", {}).get("ref", "?"),
        "head": pr_data.get("head", {}).get("ref", "?"),
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
        "changed_files": pr_data.get("changed_files", 0),
        "body": pr_data.get("body", "") or "",
    }

    return diff_text, metadata


def load_diff_from_file(path: str) -> tuple[str, dict]:
    """Load diff from local file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return p.read_text(encoding="utf-8"), {"title": p.name, "author": "local", "base": "?", "head": "?", "additions": 0, "deletions": 0, "changed_files": 0, "body": ""}


def analyze_diff(diff: str, metadata: dict) -> dict:
    """
    Analyze a diff for risks, suggestions, and confidence.
    Returns structured review data.
    """
    risks = []
    suggestions = []
    file_changes = {}  # filename -> {add, del}

    # Parse diff hunks
    current_file = None
    for line in diff.split("\n"):
        if line.startswith("diff --git"):
            # Extract filename: "diff --git a/path/to/file b/path/to/file"
            match = re.search(r"b/(.+)$", line)
            if match:
                current_file = match.group(1)
                file_changes[current_file] = {"add": 0, "del": 0}
        elif line.startswith("+") and not line.startswith("+++"):
            if current_file:
                file_changes[current_file]["add"] += 1
        elif line.startswith("-") and not line.startswith("---"):
            if current_file:
                file_changes[current_file]["del"] += 1

    # Risk detection patterns
    risk_patterns = [
        (r"\.call\s*\(|\.delegatecall\s*\(|\.send\s*\(|\.transfer\s*\(",
         "External call detected — verify reentrancy protection"),
        (r"onlyOwner|require\s*\(\s*msg\.sender\s*==\s*owner",
         "Owner-only function — centralization risk"),
        (r"selfdestruct|suicide\s*\(",
         "Contract destruction — irreversible"),
        (r"tx\.origin",
         "tx.origin used — phishing vulnerability"),
        (r"block\.timestamp|now\s*\)\s*[<>=]",
         "Timestamp dependence — miner manipulation risk"),
        (r"random|blockhash|block\.prevrandao",
         "Weak randomness source — use Chainlink VRF or commit-reveal"),
        (r"unchecked\s*\{",
         "Unchecked arithmetic — potential overflow"),
        (r"password|secret|api[_-]?key|token",
         "Sensitive value detected — verify not committed"),
        (r"console\.log|print\(|fmt\.Println",
         "Debug output left in production code"),
        (r"TODO|FIXME|XXX|HACK",
         "Incomplete code marker"),
    ]

    for pattern, message in risk_patterns:
        if re.search(pattern, diff, re.IGNORECASE):
            risks.append(message)

    # Suggestion patterns
    suggestion_patterns = [
        (r"function\s+\w+\([^)]*\)\s*public",
         "Consider marking functions `external` instead of `public` for gas savings"),
        (r"uint256\s+\w+\s*=\s*0",
         "Use `uint256(0)` or skip initialization (defaults to 0)"),
        (r"string\s+memory",
         "Use `bytes32` for short fixed strings to save gas"),
        (r"for\s*\([^;]+;\s*\w+\s*<\s*\w+\.length\s*;",
         "Cache array length outside loop for gas savings"),
        (r"require\s*\(\s*\w+\s*!=\s*address\(0\)",
         "Use OpenZeppelin's `Address.isContract` or `nonZeroAddress` modifier"),
        (r"^---$|^--- ",
         "Diff context line (likely false positive)"),  # not a real issue
    ]

    for pattern, message in suggestion_patterns:
        if re.search(pattern, diff, re.IGNORECASE | re.MULTILINE) and "Diff context" not in message:
            suggestions.append(message)

    # Calculate confidence
    total_changes = sum(c["add"] + c["del"] for c in file_changes.values())
    if total_changes < 50 and not risks:
        confidence = "High"
    elif total_changes < 200 or len(risks) <= 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Generate summary
    if file_changes:
        files_summary = ", ".join(
            f"{f} (+{c['add']}/-{c['del']})" for f, c in list(file_changes.items())[:3]
        )
        if len(file_changes) > 3:
            files_summary += f", +{len(file_changes) - 3} more"
        summary = (
            f"PR `{metadata.get('title', '?')}` by @{metadata.get('author', '?')} "
            f"modifies {len(file_changes)} file(s): {files_summary}. "
            f"Net change: +{metadata.get('additions', 0)}/-{metadata.get('deletions', 0)} lines."
        )
    else:
        summary = "No file changes detected in diff."

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
        "files_changed": len(file_changes),
        "file_details": file_changes,
    }


def format_markdown(review: dict, metadata: dict) -> str:
    """Format review as Markdown."""
    lines = [
        "## 🤖 Claude PR Review",
        "",
        f"**PR:** {metadata.get('title', '?')} (by @{metadata.get('author', '?')})",
        f"**Branch:** `{metadata.get('head', '?')}` → `{metadata.get('base', '?')}`",
        f"**Files changed:** {review['files_changed']} | **Confidence:** {review['confidence']}",
        "",
        "### Summary",
        "",
        review["summary"],
        "",
    ]

    if review["risks"]:
        lines.extend([
            "### ⚠️ Identified Risks",
            "",
        ])
        for risk in review["risks"]:
            lines.append(f"- {risk}")
        lines.append("")

    if review["suggestions"]:
        lines.extend([
            "### 💡 Improvement Suggestions",
            "",
        ])
        for sugg in review["suggestions"]:
            lines.append(f"- {sugg}")
        lines.append("")

    lines.extend([
        "---",
        f"*Generated by `claude-review` (Claude Code PR Review Agent)*",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — analyze PR diffs and produce structured reviews"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    group.add_argument("--diff", help="Raw diff text (string)")
    group.add_argument("--file", help="Path to diff file")

    parser.add_argument("--output", "-o", help="Write output to file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of Markdown")

    args = parser.parse_args()

    try:
        # Load diff
        if args.pr:
            diff, metadata = fetch_pr_diff(args.pr)
        elif args.file:
            diff, metadata = load_diff_from_file(args.file)
        else:
            diff = args.diff
            metadata = {"title": "diff input", "author": "?", "base": "?", "head": "?", "additions": 0, "deletions": 0, "changed_files": 0, "body": ""}

        # Analyze
        review = analyze_diff(diff, metadata)

        # Format
        if args.json:
            output = json.dumps({"metadata": metadata, "review": review}, indent=2)
        else:
            output = format_markdown(review, metadata)

        # Write
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Review written to {args.output}", file=sys.stderr)
        else:
            print(output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
