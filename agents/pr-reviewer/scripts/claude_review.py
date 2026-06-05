#!/usr/bin/env python3
"""
claude-review — Structured PR review agent for Claude Code.

Analyzes a GitHub PR diff via CLI and produces a structured Markdown review.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --diff diff.patch
    claude-review --pr 123 --repo owner/repo
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════════
#  DIFF FETCHING
# ══════════════════════════════════════════════════════════════════════════

def parse_pr_url(url: str) -> tuple[str, str, str]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def fetch_pr_diff(owner: str, repo: str, pr_number: str) -> str:
    """Fetch the diff for a GitHub PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-review/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_info(owner: str, repo: str, pr_number: str) -> dict:
    """Fetch PR metadata (title, description, files changed)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "claude-review/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return {}


# ══════════════════════════════════════════════════════════════════════════
#  DIFF PARSING
# ══════════════════════════════════════════════════════════════════════════

def parse_diff(diff_text: str) -> list[dict]:
    """
    Parse a unified diff into file-level chunks.
    
    Returns list of dicts: {file, status, additions, deletions, hunks, content}
    """
    files = []
    current_file = None
    current_hunk = None

    for line in diff_text.split("\n"):
        # File header: diff --git a/file b/file
        m = re.match(r"^diff --git a/(.+?)\s+b/(.+?)$", line)
        if m:
            if current_file:
                files.append(current_file)
            current_file = {
                "file_a": m.group(1),
                "file_b": m.group(2),
                "status": "modified",
                "additions": 0,
                "deletions": 0,
                "hunks": [],
                "content": [],
            }
            continue

        # New file
        m = re.match(r"^new file mode \d+", line)
        if m and current_file:
            current_file["status"] = "added"
            continue

        # Deleted file
        m = re.match(r"^deleted file mode \d+", line)
        if m and current_file:
            current_file["status"] = "deleted"
            continue

        # Renamed
        m = re.match(r"^rename from (.+)$", line)
        if m and current_file:
            current_file["status"] = "renamed"
            continue

        # Hunk header: @@ -a,b +c,d @@
        m = re.match(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@(.*)", line)
        if m and current_file:
            current_hunk = {
                "old_start": int(m.group(1)),
                "old_count": int(m.group(2)) if m.group(2) else 1,
                "new_start": int(m.group(3)),
                "new_count": int(m.group(4)) if m.group(4) else 1,
                "section": m.group(5).strip(),
                "lines": [],
            }
            current_file["hunks"].append(current_hunk)
            current_file["content"].append(line)
            continue

        if current_file:
            current_file["content"].append(line)

        if current_hunk:
            current_hunk["lines"].append(line)
            if line.startswith("+"):
                current_file["additions"] += 1
            elif line.startswith("-"):
                current_file["deletions"] += 1

    if current_file:
        files.append(current_file)

    return files


# ══════════════════════════════════════════════════════════════════════════
#  ANALYSIS
# ══════════════════════════════════════════════════════════════════════════

def analyze_files(files: list[dict]) -> dict:
    """Analyze parsed diff and produce review data."""
    summary_lines = []
    risks = []
    improvements = []
    findings = []

    total_additions = sum(f["additions"] for f in files)
    total_deletions = sum(f["deletions"] for f in files)
    total_files = len(files)

    # ── Summary ──────────────────────────────────────────────────────────
    statuses = defaultdict(int)
    for f in files:
        statuses[f["status"]] += 1

    summary_parts = []
    if statuses.get("added", 0):
        summary_parts.append(f"**{statuses['added']} new files**")
    if statuses.get("modified", 0):
        summary_parts.append(f"**{statuses['modified']} modified files**")
    if statuses.get("deleted", 0):
        summary_parts.append(f"**{statuses['deleted']} deleted files**")
    if statuses.get("renamed", 0):
        summary_parts.append(f"**{statuses['renamed']} renamed files**")

    summary_lines.append(
        f"This PR changes {total_files} file{'s' if total_files != 1 else ''} "
        f"({', '.join(summary_parts)}) with "
        f"**+{total_additions}** / **-{total_deletions}** lines."
    )

    # ── File-level analysis ──────────────────────────────────────────────
    for f in files:
        file_name = f["file_b"]
        ext = Path(file_name).suffix.lower()

        # Detect large files
        if f["additions"] + f["deletions"] > 500:
            risks.append(f"`{file_name}` is very large ({f['additions']}+/{f['deletions']}- lines). Consider splitting into smaller changes.")

        # Detect binary-ish content
        if ext in (".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip", ".tar", ".gz"):
            findings.append(f"`{file_name}` appears to be a binary/asset file ({f['status']})")
            continue

        # Scan for common issues
        content = "\n".join(f["content"])
        lines_added = [l[1:] for l in content.split("\n") if l.startswith("+") and len(l) > 1]

        # TODO/FIXME markers
        todos = [l for l in lines_added if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", l, re.IGNORECASE)]
        if todos:
            for t in todos[:3]:
                improvements.append(f"`{file_name}` contains a TODO/FIXME: `{t.strip()[:60]}`")

        # Debug print statements
        debug_stmts = [l for l in lines_added if re.search(r"\b(print|console\.log|pdb\.set_trace|var_dump|dd\()\b", l)]
        if debug_stmts:
            for d in debug_stmts[:2]:
                risks.append(f"`{file_name}` has a debug statement left in: `{d.strip()[:60]}`")

        # Hardcoded secrets/credentials
        secrets = [l for l in lines_added if re.search(r"(password|secret|api_key|api\.key|token|auth_token|private_key)\s*[:=]\s*['\"]", l, re.IGNORECASE) and "example" not in l.lower()]
        if secrets:
            for s in secrets[:2]:
                risks.append(f"⚠️ **Potential hardcoded secret** in `{file_name}`: `{s.strip()[:50]}`")

        # SQL injection risk (string concatenation in SQL)
        sql_risks = [l for l in lines_added if re.search(r"(SELECT|INSERT|UPDATE|DELETE)\s+.*\bf\b.*(\+|f\()", l, re.IGNORECASE) or re.search(r"execute\(.*['\"]\s*\+", l)]
        if sql_risks:
            risks.append(f"Potential SQL injection risk in `{file_name}`: string concatenation in SQL query")

        # Large functions (approximate: many consecutive additions)
        if f["additions"] > 100 and ext in (".py", ".js", ".ts", ".java", ".go", ".rs"):
            improvements.append(f"`{file_name}` adds {f['additions']} lines. Consider breaking into smaller functions/modules.")

    # ── Overall suggestions ──────────────────────────────────────────────
    if total_files > 20:
        improvements.append("This PR touches many files. Consider splitting into smaller, focused PRs for easier review.")

    # ── Confidence score ─────────────────────────────────────────────────
    risk_count = len(risks)
    if risk_count >= 3:
        confidence = "Low"
    elif risk_count >= 1:
        confidence = "Medium"
    else:
        confidence = "High"

    return {
        "summary": " ".join(summary_lines) if summary_lines else f"PR changes {total_files} files.",
        "total_files": total_files,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "risks": risks if risks else ["No significant risks detected."],
        "improvements": improvements if improvements else ["No specific suggestions — looks clean."],
        "findings": findings,
        "confidence": confidence,
    }


def format_review(review: dict, pr_url: str | None = None, pr_title: str | None = None) -> str:
    """Format the review as structured Markdown."""
    lines = []

    if pr_url:
        lines.append(f"# 🔍 PR Review: [{pr_title or pr_url}]({pr_url})")
    else:
        lines.append("# 🔍 PR Review")
    lines.append("")

    # Summary
    lines.append("## 📋 Summary")
    lines.append("")
    lines.append(review["summary"])
    lines.append(f"\n- Files changed: **{review['total_files']}**")
    lines.append(f"- Additions: **+{review['total_additions']}**")
    lines.append(f"- Deletions: **-{review['total_deletions']}**")
    lines.append("")

    # Identified Risks
    lines.append("## ⚠️ Identified Risks")
    lines.append("")
    for r in review["risks"]:
        lines.append(f"- {r}")
    lines.append("")

    # Improvement suggestions
    lines.append("## 💡 Improvement Suggestions")
    lines.append("")
    for imp in review["improvements"]:
        lines.append(f"- {imp}")
    lines.append("")

    # Confidence
    emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    lines.append("## ✅ Review Confidence")
    lines.append("")
    lines.append(f"Confidence: **{emoji.get(review['confidence'], '⚪')} {review['confidence']}**")
    if review["confidence"] == "Low":
        lines.append("\n_A low confidence score indicates potential risks that need human review._")
    elif review["confidence"] == "Medium":
        lines.append("\n_A few items flagged — review recommended._")
    else:
        lines.append("\n_No significant issues found. Looks good!_")
    lines.append("")

    # Stats footer
    lines.append("---")
    lines.append(f"_Auto-generated by claude-review · {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="claude-review — Structured PR review agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr 123 --repo owner/repo
  claude-review --diff changes.patch
  claude-review --diff changes.patch --title "My PR"
  cat changes.patch | claude-review --stdin
        """,
    )

    # PR source
    pr_group = parser.add_argument_group("PR source (choose one)")
    pr_group.add_argument("--pr", type=str, help="Full PR URL (e.g., https://github.com/owner/repo/pull/123)")
    pr_group.add_argument("--repo", type=str, help="Repository as owner/repo (used with --pr-number)")
    pr_group.add_argument("--pr-number", type=str, help="PR number (used with --repo)")
    pr_group.add_argument("--diff", type=str, help="Path to diff/patch file")
    pr_group.add_argument("--stdin", action="store_true", help="Read diff from stdin")

    # Options
    parser.add_argument("-o", "--output", type=str, help="Output file (default: stdout)")
    parser.add_argument("--title", type=str, help="PR title (for display)")

    args = parser.parse_args()

    # ── Fetch diff ───────────────────────────────────────────────────────
    diff_text = None
    pr_url = None
    pr_title = args.title

    if args.pr:
        pr_url = args.pr
        owner, repo, pr_number = parse_pr_url(args.pr)
        print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
        diff_text = fetch_pr_diff(owner, repo, pr_number)
        info = fetch_pr_info(owner, repo, pr_number)
        if info.get("title"):
            pr_title = info["title"]
        if not pr_title:
            pr_title = f"{owner}/{repo} #{pr_number}"
        pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"

    elif args.repo and args.pr_number:
        owner, repo = args.repo.split("/")
        print(f"Fetching PR #{args.pr_number} from {owner}/{repo}...", file=sys.stderr)
        diff_text = fetch_pr_diff(owner, repo, args.pr_number)
        info = fetch_pr_info(owner, repo, args.pr_number)
        if info.get("title"):
            pr_title = info["title"]
        pr_url = f"https://github.com/{owner}/{repo}/pull/{args.pr_number}"

    elif args.diff:
        with open(args.diff, "r", encoding="utf-8") as f:
            diff_text = f.read()

    elif args.stdin:
        diff_text = sys.stdin.read()

    else:
        parser.print_help()
        sys.exit(1)

    if not diff_text or not diff_text.strip():
        print("Error: empty diff", file=sys.stderr)
        sys.exit(1)

    # ── Analyze ──────────────────────────────────────────────────────────
    print(f"Parsing diff ({len(diff_text)} bytes)...", file=sys.stderr)
    files = parse_diff(diff_text)
    print(f"Found {len(files)} file(s) changed.", file=sys.stderr)

    review_data = analyze_files(files)
    markdown = format_review(review_data, pr_url, pr_title)

    # ── Output ───────────────────────────────────────────────────────────
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
