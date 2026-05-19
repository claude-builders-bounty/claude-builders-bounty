#!/usr/bin/env python3
"""
claude-review — Claude Code PR review sub-agent.
CLI tool that analyzes GitHub PR diffs and returns structured review comments.

Usage: claude-review --pr https://github.com/owner/repo/pull/123
       claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def fatal(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def parse_pr_url(url):
    """Parse GitHub PR URL into owner/repo/number."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        fatal(f"Invalid PR URL: {url}. Expected: https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), int(m.group(3))

def api_get(url):
    """Fetch JSON from GitHub API."""
    if not GITHUB_TOKEN:
        fatal("GITHUB_TOKEN environment variable not set")
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("User-Agent", "claude-review")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        fatal(f"API error {e.code}: {body}")
    except Exception as e:
        fatal(f"Request failed: {e}")

def get_pr_diff(owner, repo, number):
    """Fetch raw PR diff."""
    if not GITHUB_TOKEN:
        fatal("GITHUB_TOKEN environment variable not set")
    req = urllib.request.Request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("User-Agent", "claude-review")
    req.add_header("Accept", "application/vnd.github.diff")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.read().decode()
    except urllib.error.HTTPError as e:
        fatal(f"Diff fetch error {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        fatal(f"Diff request failed: {e}")

def get_pr_metadata(owner, repo, number):
    """Get PR title, description, changed files."""
    data = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
    files = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files")

    changed_files = []
    total_additions = 0
    total_deletions = 0
    for f in files:
        changed_files.append({
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "changes": f["changes"],
        })
        total_additions += f["additions"]
        total_deletions += f["deletions"]

    return {
        "title": data.get("title", ""),
        "description": data.get("body", "") or "",
        "author": data.get("user", {}).get("login", "unknown"),
        "state": data.get("state", ""),
        "changed_files": changed_files,
        "total_changed_files": len(changed_files),
        "total_additions": total_additions,
        "total_deletions": total_deletions,
    }

def analyze_diff(diff, metadata):
    """
    Analyze the PR diff and generate a review.
    This function examines the diff for common issues.
    """
    findings = {
        "risks": [],
        "improvements": [],
        "positives": [],
    }

    lines = diff.split("\n")
    current_file = ""
    added_lines = []
    removed_lines = []

    for line in lines:
        # Track file changes
        fm = re.match(r"\+\+\+ b/(.+)", line)
        if fm:
            current_file = fm.group(1)
            continue

        if line.startswith("+"):
            added_lines.append((current_file, line[1:]))
        elif line.startswith("-"):
            removed_lines.append((current_file, line[1:]))

    # Check for common code issues
    for fname, code in added_lines:
        # Hardcoded strings / secrets
        if re.search(r"(password|secret|api_key|token)\s*[:=]\s*['\"][^'\"]+['\"]", code, re.IGNORECASE):
            findings["risks"].append(f"Potential hardcoded credential in `{fname}`")
        # Print/console.log left in
        if re.search(r"\b(print|console\.log|fmt\.Print|System\.out\.print)\s*\(", code):
            findings["improvements"].append(f"Debug output left in `{fname}` line: `{code.strip()[:60]}`")
        # TODO comments
        if re.search(r"TODO|FIXME|HACK|XXX", code):
            findings["improvements"].append(f"Unresolved TODO/FIXME in `{fname}`: `{code.strip()[:60]}`")
        # Empty exception handlers
        if re.search(r"except\s*:", code) or re.search(r"catch\s*\{?\s*\}?\s*\{", code):
            findings["risks"].append(f"Bare/empty exception handler in `{fname}`")
        # SQL injection risk (string concatenation in SQL)
        if re.search(r"SELECT.*FROM.*\+|INSERT INTO.*\+|DELETE.*\+", code, re.IGNORECASE):
            findings["risks"].append(f"Possible SQL injection (string concatenation) in `{fname}`")

    # File-level analysis
    for f in metadata["changed_files"]:
        name = f["filename"]
        if f["additions"] > 200:
            findings["risks"].append(f"`{name}` has {f['additions']} additions — consider splitting into smaller changes")

    # General observations
    total_changes = metadata["total_additions"] + metadata["total_deletions"]
    if total_changes > 1000:
        findings["risks"].append(f"PR is very large ({total_changes} changes) — hard to review thoroughly")
    elif total_changes < 20:
        findings["positives"].append("Small, focused change — easy to review")

    if metadata["total_changed_files"] <= 3:
        findings["positives"].append(f"Change touches only {metadata['total_changed_files']} files — focused scope")

    if not findings["risks"]:
        findings["positives"].append("No significant risks detected")

    if not findings["improvements"]:
        findings["positives"].append("Code quality looks clean — no debug artifacts or TODOs")

    return findings


def generate_review(metadata, diff, findings):
    """Generate structured Markdown review output."""
    lines = []
    lines.append(f"# PR Review: {metadata['title']}")
    lines.append(f"")
    lines.append(f"**PR:** `{metadata['author']}/{metadata['state']}` | "
                 f"**Files:** {metadata['total_changed_files']} | "
                 f"**+{metadata['total_additions']}/-{metadata['total_deletions']}")
    lines.append(f"")

    # Summary
    lines.append(f"## Summary")
    summary_parts = []
    summary_parts.append(f"This PR modifies {metadata['total_changed_files']} files "
                         f"with {metadata['total_additions']} additions and "
                         f"{metadata['total_deletions']} deletions.")
    if metadata["description"]:
        desc = metadata["description"].split("\n")[0][:100]
        summary_parts.append(f"Description: {desc}...")
    lines.append(" ".join(summary_parts))
    lines.append(f"")

    # Changed files
    lines.append(f"## Changed Files")
    for f in metadata["changed_files"]:
        status_icon = {"added": "🆕", "modified": "📝", "removed": "🗑️", "renamed": "📄"}.get(f["status"], "📄")
        lines.append(f"- {status_icon} `{f['filename']}` (+{f['additions']}/-{f['deletions']})")
    lines.append(f"")

    # Risks
    lines.append(f"## 🔴 Identified Risks")
    if findings["risks"]:
        for r in findings["risks"]:
            lines.append(f"- {r}")
    else:
        lines.append("_No risks identified._")
    lines.append(f"")

    # Improvements
    lines.append(f"## 🟡 Improvement Suggestions")
    if findings["improvements"]:
        for s in findings["improvements"]:
            lines.append(f"- {s}")
    else:
        lines.append("_No specific improvements suggested._")
    lines.append(f"")

    # Positives
    lines.append(f"## 🟢 Positives")
    if findings["positives"]:
        for p in findings["positives"]:
            lines.append(f"- {p}")
    else:
        lines.append("_No specific observations._")
    lines.append(f"")

    # Confidence
    risk_count = len(findings["risks"])
    if risk_count >= 3:
        confidence = "Low"
        confidence_note = "Several risks detected — manual review recommended"
    elif risk_count >= 1:
        confidence = "Medium"
        confidence_note = "Some issues found — review flagged items carefully"
    else:
        confidence = "High"
        confidence_note = "No risks detected — looks good"

    lines.append(f"## Confidence Score")
    lines.append(f"**{confidence}** — {confidence_note}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"_Generated by claude-review at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", "-o", help="Write output to file")
    args = parser.parse_args()

    owner, repo, number = parse_pr_url(args.pr)

    print(f"Fetching PR #{number} from {owner}/{repo}...", file=sys.stderr)
    diff = get_pr_diff(owner, repo, number)
    metadata = get_pr_metadata(owner, repo, number)
    findings = analyze_diff(diff, metadata)
    review = generate_review(metadata, diff, findings)

    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(review)


if __name__ == "__main__":
    main()
