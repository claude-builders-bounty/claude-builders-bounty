#!/usr/bin/env python3
"""claude_review.py — Multi-backend PR review agent.

Fetches a GitHub PR diff (or reads a local diff file), analyzes it, and
outputs a structured Markdown review.  Supports three backends:

  • heuristic   — pure-Python regex analysis (always works, no API key)
  • anthropic   — Anthropic Messages API (requires ANTHROPIC_API_KEY)
  • claude-cli  — local ``claude`` CLI binary (requires claude installed)

Usage:
  python3 claude_review.py --pr https://github.com/owner/repo/pull/123
  python3 claude_review.py --pr owner/repo#123
  python3 claude_review.py --diff changes.diff
  python3 claude_review.py --pr URL --backend heuristic --output review.md
  python3 claude_review.py --pr URL --post-comment
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
DEFAULT_MAX_DIFF_BYTES = 500_000
GITHUB_API = "https://api.github.com"
REVIEW_PROMPT = textwrap.dedent("""\
    You are an expert code reviewer. Analyze the following pull request diff
    and produce a structured Markdown review with these exact sections:

    ## Summary
    2-3 sentences describing what the PR does and its overall impact.

    ## Identified Risks
    A markdown table with columns: # | Severity | Category | Description | File(s)
    Severity: critical / high / medium / low
    Categories: security / bug / performance / breaking-change / quality / style

    ## Improvement Suggestions
    Numbered list. Each item: **[Category]** Description — `file:Lline`

    ## Confidence
    **Score:** Low / Medium / High
    **Rationale:** Why this confidence level

    PR metadata:
    Title: {title}
    Author: {author}
    Files changed: {files}
    +{additions} / -{deletions}

    Diff:
    ```diff
    {diff}
    ```
""")

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PRMetadata:
    """Metadata fetched from the GitHub API."""

    url: str = ""
    title: str = ""
    author: str = ""
    body: str = ""
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0
    number: int = 0
    repo_full_name: str = ""  # owner/repo


@dataclass
class Risk:
    severity: str  # critical / high / medium / low
    category: str  # security / bug / performance / breaking-change / quality / style
    description: str
    files: str


@dataclass
class Review:
    summary: str = ""
    risks: List[Risk] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence_score: str = "Low"  # Low / Medium / High
    confidence_rationale: str = ""
    backend: str = ""
    model: str = ""


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------


def _github_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Return headers for GitHub API requests."""
    h = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-multimodel/" + VERSION,
    }
    if token:
        h["Authorization"] = "Bearer " + token
    return h


def _github_request(url: str, headers: Dict[str, str], timeout: int = 30) -> bytes:
    """Make a GitHub API request and return raw response bytes."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_pr_ref(ref: str) -> Tuple[str, str, int]:
    """Parse a PR reference into (owner, repo, pr_number).

    Accepted formats:
      - https://github.com/owner/repo/pull/123
      - owner/repo#123
    """
    # Full URL
    m = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", ref
    )
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    # Short ref
    m = re.match(r"^([^/]+)/([^#]+)#(\d+)$", ref)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(
        f"Cannot parse PR reference: {ref!r}. "
        "Use https://github.com/owner/repo/pull/123 or owner/repo#123"
    )


def fetch_pr_metadata(
    owner: str, repo: str, number: int, token: Optional[str] = None
) -> PRMetadata:
    """Fetch PR metadata from GitHub API."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}"
    data = json.loads(_github_request(url, _github_headers(token)))
    return PRMetadata(
        url=data.get("html_url", ""),
        title=data.get("title", ""),
        author=data.get("user", {}).get("login", ""),
        body=data.get("body", "") or "",
        files_changed=data.get("changed_files", 0),
        additions=data.get("additions", 0),
        deletions=data.get("deletions", 0),
        number=number,
        repo_full_name=f"{owner}/{repo}",
    )


def fetch_pr_diff(
    owner: str, repo: str, number: int, token: Optional[str] = None
) -> str:
    """Fetch the PR diff text."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}"
    headers = _github_headers(token)
    headers["Accept"] = "application/vnd.github.v3.diff"
    return _github_request(url, headers).decode("utf-8", errors="replace")


def post_pr_comment(
    owner: str,
    repo: str,
    number: int,
    body: str,
    token: str,
) -> None:
    """Post a review comment on the PR."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    headers = _github_headers(token)
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()
    print(f"Posted review comment on {owner}/{repo}#{number}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Diff processing
# ---------------------------------------------------------------------------


def truncate_diff(diff: str, max_bytes: int = DEFAULT_MAX_DIFF_BYTES) -> str:
    """Truncate diff to max_bytes and add a note if truncated."""
    encoded = diff.encode("utf-8")
    if len(encoded) <= max_bytes:
        return diff
    truncated = encoded[:max_bytes].decode("utf-8", errors="replace")
    truncated += (
        f"\n\n--- DIFF TRUNCATED at {max_bytes} bytes "
        f"(original: {len(encoded)} bytes) ---\n"
    )
    return truncated


def parse_diff_stats(diff: str) -> Dict[str, Dict[str, int]]:
    """Parse per-file change counts from a unified diff.

    Returns {filename: {additions: N, deletions: N}}.
    """
    stats: Dict[str, Dict[str, int]] = {}
    current_file = ""
    for line in diff.splitlines():
        # New file in diff
        m = re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            current_file = m.group(1)
            if current_file not in stats:
                stats[current_file] = {"additions": 0, "deletions": 0}
            continue
        if not current_file:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            stats[current_file]["additions"] += 1
        elif line.startswith("-") and not line.startswith("---"):
            stats[current_file]["deletions"] += 1
    return stats


# ---------------------------------------------------------------------------
# Heuristic backend
# ---------------------------------------------------------------------------

# Patterns for heuristic detection
_SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey|secret|token|password|passwd|pwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}", "Potential hardcoded secret/credential"),
    (r"(?i)(AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}", "AWS access key ID pattern"),
    (r"(?i)sk-[a-zA-Z0-9]{20,}", "OpenAI/Anthropic API key pattern"),
    (r"(?i)ghp_[a-zA-Z0-9]{36}", "GitHub personal access token pattern"),
    (r"(?i)gho_[a-zA-Z0-9]{36}", "GitHub OAuth token pattern"),
]

_DEBUG_PATTERNS = [
    (r"\bprint\s*\(", "Debug print statement"),
    (r"\bconsole\.log\s*\(", "Debug console.log statement"),
    (r"\bdebugger\b", "Debugger statement"),
    (r"\bpdb\.set_trace\s*\(", "Python pdb breakpoint"),
    (r"\bbreakpoint\s*\(", "Python breakpoint() call"),
    (r"\bprintln!\s*\(", "Rust debug println"),
]

_EMPTY_CATCH_PATTERNS = [
    (r"except\s*:\s*pass", "Bare except with pass (same line)"),
    (r"except\s+[\w.]+\s*:\s*pass", "Empty exception handler (same line)"),
    (r"catch\s*\(\s*\w+\s*\)\s*\{\s*\}", "Empty catch block"),
]

# Multi-line patterns: we collapse consecutive added lines to detect cross-line constructs
_MULTI_LINE_EMPTY_CATCH = [
    (r"except\s*:\s*\n\s*pass", "Bare except with pass"),
    (r"except\s+[\w.]+\s*:\s*\n\s*pass", "Empty exception handler"),
]

_TODO_PATTERNS = [
    (r"(?i)\bTODO\b", "TODO comment"),
    (r"(?i)\bFIXME\b", "FIXME comment"),
    (r"(?i)\bHACK\b", "HACK comment"),
    (r"(?i)\bXXX\b", "XXX comment"),
]

_ERROR_HANDLING_PATTERNS = [
    (r"(?i)open\s*\([^)]*\)(?!\s*as\b)", "File open without context manager (potential resource leak)"),
    (r"(?i)requests\.(get|post|put|delete|patch)\s*\([^)]*\)(?!\s*\.raise_for_status)", "HTTP request without status check"),
]


def _find_pattern_matches(
    diff: str, patterns: List[Tuple[str, str]], category: str, severity: str
) -> List[Risk]:
    """Find regex matches in added lines and return risks.

    For multi-line patterns (containing ``\\n``), matches against the full diff
    after stripping leading ``+`` from added lines.  For single-line patterns,
    matches against each added line individually for accurate file attribution.
    """
    risks: List[Tuple[str, str, str, int]] = []  # (desc, file, category, severity, count placeholder)

    for pattern, desc in patterns:
        is_multiline = "\n" in pattern or r"\n" in pattern
        if is_multiline:
            # Collapse added lines: strip leading '+' from diff lines,
            # join consecutive added lines, then match
            added_lines = []
            current_file = "unknown"
            file_map: Dict[str, str] = {}  # matched text -> file
            for line in diff.splitlines():
                m = re.match(r"^\+\+\+ b/(.+)$", line)
                if m:
                    current_file = m.group(1)
                    continue
                if line.startswith("+") and not line.startswith("+++"):
                    stripped = line[1:]  # remove leading '+'
                    added_lines.append(stripped)
                    # Track which file each line belongs to
                    file_map[stripped.strip()] = current_file
                elif not line.startswith("-") and not line.startswith("\\"):
                    added_lines.append(line[1:] if line.startswith(" ") else line)

            collapsed = "\n".join(added_lines)
            matches = list(re.finditer(pattern, collapsed))
            if not matches:
                continue

            # Find which files contain the pattern
            affected_files = set()
            for match in matches:
                matched_text = match.group()
                first_line = matched_text.split("\n")[0].strip()
                if first_line in file_map:
                    affected_files.add(file_map[first_line])
                else:
                    # Try to find the file by scanning for the matched text in original diff
                    for line in diff.splitlines():
                        if first_line in line and line.startswith("+"):
                            # Walk back to find the file header
                            for prev in diff.splitlines():
                                pm = re.match(r"^\+\+\+ b/(.+)$", prev)
                                if pm:
                                    affected_files.add(pm.group(1))
                                    break
                            break
            if affected_files:
                risks.append((desc, ", ".join(sorted(affected_files)), category, len(matches)))
        else:
            # Single-line pattern matching (original logic)
            matches = list(re.finditer(pattern, diff))
            if not matches:
                continue
            affected_files = set()
            current_file = "unknown"
            for line in diff.splitlines():
                m = re.match(r"^\+\+\+ b/(.+)$", line)
                if m:
                    current_file = m.group(1)
                for match in matches:
                    if match.group() in line and line.startswith("+") and not line.startswith("+++"):
                        affected_files.add(current_file)
            if affected_files:
                risks.append((desc, ", ".join(sorted(affected_files)), category, len(matches)))

    # Deduplicate and create Risk objects
    seen: set = set()
    result = []
    for desc, files, cat, count in risks:
        key = (desc, files)
        if key not in seen:
            seen.add(key)
            result.append(
                Risk(
                    severity=severity,
                    category=cat,
                    description=f"{desc} ({count} occurrence(s))" if count > 1 else desc,
                    files=files,
                )
            )
    return result


def heuristic_review(diff: str, meta: Optional[PRMetadata] = None) -> Review:
    """Produce a review using pure-Python heuristic analysis."""
    risks: List[Risk] = []
    suggestions: List[str] = []

    # --- Secret / credential detection ---
    risks.extend(_find_pattern_matches(diff, _SECRET_PATTERNS, "security", "critical"))

    # --- Debug statements ---
    debug_risks = _find_pattern_matches(diff, _DEBUG_PATTERNS, "quality", "medium")
    risks.extend(debug_risks)
    if debug_risks:
        suggestions.append(
            "**quality** Remove debug/print statements before merging — "
            "use a proper logging framework instead"
        )

    # --- Empty catch blocks ---
    catch_risks = _find_pattern_matches(diff, _EMPTY_CATCH_PATTERNS, "bug", "high")
    catch_risks.extend(_find_pattern_matches(diff, _MULTI_LINE_EMPTY_CATCH, "bug", "high"))
    risks.extend(catch_risks)
    if catch_risks:
        suggestions.append(
            "**bug** Handle exceptions explicitly instead of silently swallowing them — "
            "at minimum log the error"
        )

    # --- TODO/FIXME/HACK ---
    todo_risks = _find_pattern_matches(diff, _TODO_PATTERNS, "quality", "low")
    risks.extend(todo_risks)
    if todo_risks:
        suggestions.append(
            "**quality** Resolve or track TODO/FIXME/HACK items — "
            "create issues for any that should be addressed later"
        )

    # --- Error handling patterns ---
    err_risks = _find_pattern_matches(diff, _ERROR_HANDLING_PATTERNS, "bug", "medium")
    risks.extend(err_risks)

    # --- Large changes ---
    file_stats = parse_diff_stats(diff)
    large_files = [
        (f, s) for f, s in file_stats.items() if s["additions"] + s["deletions"] > 500
    ]
    for fname, s in large_files:
        risks.append(
            Risk(
                severity="medium",
                category="quality",
                description=f"Large change in {fname} (+{s['additions']}/-{s['deletions']} lines) — "
                "consider splitting into smaller, focused PRs",
                files=fname,
            )
        )

    # --- Diff stats summary ---
    total_add = sum(s["additions"] for s in file_stats.values())
    total_del = sum(s["deletions"] for s in file_stats.values())
    n_files = len(file_stats)

    # Use metadata if available, else parsed stats
    if meta:
        title = meta.title
        author = meta.author
        files_changed = meta.files_changed or n_files
        additions = meta.additions or total_add
        deletions = meta.deletions or total_del
    else:
        title = "Unknown"
        author = "Unknown"
        files_changed = n_files
        additions = total_add
        deletions = total_del

    # --- Build summary ---
    summary_parts = []
    if title and title != "Unknown":
        summary_parts.append(f"This PR ({title})")
    else:
        summary_parts.append("This PR")
    summary_parts.append(
        f"modifies {files_changed} file(s) with +{additions}/-{deletions} lines changed."
    )
    if risks:
        severities = [r.severity for r in risks]
        if "critical" in severities:
            summary_parts.append("Critical issues detected that should be addressed before merging.")
        elif "high" in severities:
            summary_parts.append("Several high-severity issues found that warrant attention.")
        else:
            summary_parts.append(
                f"{len(risks)} issue(s) detected, mostly medium/low severity."
            )
    else:
        summary_parts.append("No significant issues detected by heuristic analysis.")
    summary = " ".join(summary_parts)

    # --- Confidence ---
    n_critical = sum(1 for r in risks if r.severity == "critical")
    n_high = sum(1 for r in risks if r.severity == "high")
    if n_critical > 0:
        conf_score = "High"
        conf_rationale = "Critical security issues (potential secrets) found with high-confidence regex patterns."
    elif n_high > 0:
        conf_score = "Medium"
        conf_rationale = "High-severity issues found, but heuristic analysis may produce false positives."
    elif risks:
        conf_score = "Medium"
        conf_rationale = "Issues detected by pattern matching — some may be false positives; LLM review recommended."
    else:
        conf_score = "Low"
        conf_rationale = (
            "No issues found by heuristic analysis, but heuristic review cannot "
            "detect logic errors, architectural issues, or domain-specific concerns. "
            "LLM-based review recommended for thorough analysis."
        )

    # Sort risks by severity
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    risks.sort(key=lambda r: sev_order.get(r.severity, 99))

    # Default suggestion if no specific ones
    if not suggestions:
        suggestions.append(
            "**quality** Consider using an LLM backend (anthropic/claude-cli) for deeper "
            "semantic analysis beyond pattern matching"
        )

    return Review(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence_score=conf_score,
        confidence_rationale=conf_rationale,
        backend="heuristic",
        model="heuristic",
    )


# ---------------------------------------------------------------------------
# Anthropic backend
# ---------------------------------------------------------------------------


def anthropic_review(
    diff: str,
    meta: Optional[PRMetadata] = None,
    model: str = "claude-sonnet-4-20250514",
    api_key: Optional[str] = None,
) -> str:
    """Call Anthropic Messages API and return the raw review text."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    title = meta.title if meta else "Unknown"
    author = meta.author if meta else "Unknown"
    files = str(meta.files_changed) if meta else "?"
    additions = str(meta.additions) if meta else "?"
    deletions = str(meta.deletions) if meta else "?"

    prompt = REVIEW_PROMPT.format(
        title=title, author=author, files=files,
        additions=additions, deletions=deletions, diff=diff,
    )

    payload = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "User-Agent": "claude-review-multimodel/" + VERSION,
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    # Extract text from response
    text_blocks = [
        b["text"] for b in result.get("content", []) if b.get("type") == "text"
    ]
    return "\n\n".join(text_blocks)


# ---------------------------------------------------------------------------
# Claude CLI backend
# ---------------------------------------------------------------------------


def claude_cli_review(
    diff: str,
    meta: Optional[PRMetadata] = None,
    model: Optional[str] = None,
) -> str:
    """Call the local ``claude`` CLI binary and return the review text."""
    title = meta.title if meta else "Unknown"
    author = meta.author if meta else "Unknown"
    files = str(meta.files_changed) if meta else "?"
    additions = str(meta.additions) if meta else "?"
    deletions = str(meta.deletions) if meta else "?"

    prompt = REVIEW_PROMPT.format(
        title=title, author=author, files=files,
        additions=additions, deletions=deletions, diff=diff,
    )

    cmd = ["claude", "--print"]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(
            f"claude CLI failed (exit {result.returncode}): {result.stderr[:500]}"
        )
    return result.stdout


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def format_review(review: Review, meta: Optional[PRMetadata] = None) -> str:
    """Format a Review object into the final Markdown output."""
    lines: List[str] = []

    # Header
    title = meta.title if meta and meta.title else "Unknown PR"
    url = meta.url if meta and meta.url else ""
    author = meta.author if meta and meta.author else "Unknown"
    files_n = str(meta.files_changed) if meta and meta.files_changed else "?"
    additions = str(meta.additions) if meta and meta.additions else "?"
    deletions = str(meta.deletions) if meta and meta.deletions else "?"

    lines.append(f"# PR Review: {title}")
    lines.append("")
    if url:
        lines.append(f"**PR:** {url}")
    lines.append(f"**Author:** {author}")
    lines.append(f"**Files Changed:** {files_n} | **Insertions:** +{additions} | **Deletions:** -{deletions}")
    lines.append(f"**Backend:** {review.backend} | **Model:** {review.model}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(review.summary)
    lines.append("")

    # Risks
    lines.append("## Identified Risks")
    lines.append("")
    if review.risks:
        lines.append("| # | Severity | Category | Description | File(s) |")
        lines.append("|---|----------|----------|-------------|---------|")
        for i, r in enumerate(review.risks, 1):
            lines.append(
                f"| {i} | {r.severity} | {r.category} | {r.description} | {r.files} |"
            )
    else:
        lines.append("No risks identified.")
    lines.append("")

    # Suggestions
    lines.append("## Improvement Suggestions")
    lines.append("")
    if review.suggestions:
        for s in review.suggestions:
            lines.append(f"{s}")
    else:
        lines.append("No specific suggestions.")
    lines.append("")

    # Confidence
    lines.append("## Confidence")
    lines.append("")
    lines.append(f"**Score:** {review.confidence_score}")
    lines.append(f"**Rationale:** {review.confidence_rationale}")
    lines.append("")

    return "\n".join(lines)


def format_raw_review(
    raw_text: str, meta: Optional[PRMetadata] = None, backend: str = "", model: str = ""
) -> str:
    """Wrap a raw LLM review text with metadata header."""
    lines: List[str] = []

    title = meta.title if meta and meta.title else "Unknown PR"
    url = meta.url if meta and meta.url else ""
    author = meta.author if meta and meta.author else "Unknown"
    files_n = str(meta.files_changed) if meta and meta.files_changed else "?"
    additions = str(meta.additions) if meta and meta.additions else "?"
    deletions = str(meta.deletions) if meta and meta.deletions else "?"

    lines.append(f"# PR Review: {title}")
    lines.append("")
    if url:
        lines.append(f"**PR:** {url}")
    lines.append(f"**Author:** {author}")
    lines.append(f"**Files Changed:** {files_n} | **Insertions:** +{additions} | **Deletions:** -{deletions}")
    lines.append(f"**Backend:** {backend} | **Model:** {model}")
    lines.append("")
    lines.append("---")
    lines.append("")
    # The LLM output should already have the structured sections
    lines.append(raw_text)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------


def _detect_claude_cli() -> bool:
    """Check if the claude CLI is available."""
    try:
        result = subprocess.run(
            ["claude", "--version"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def select_backend(requested: str) -> str:
    """Resolve the backend to use, considering availability."""
    if requested != "auto":
        return requested

    if _detect_claude_cli():
        return "claude-cli"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "heuristic"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Multi-backend PR review agent with structured Markdown output",
    )
    parser.add_argument("--pr", help="GitHub PR URL or owner/repo#123")
    parser.add_argument("--diff", help="Local diff file to review")
    parser.add_argument(
        "--backend",
        choices=["auto", "claude-cli", "anthropic", "heuristic"],
        default="auto",
        help="Review backend (default: auto)",
    )
    parser.add_argument("--model", help="Model name for LLM backends")
    parser.add_argument(
        "--post-comment", action="store_true",
        help="Post review as PR comment (requires GITHUB_TOKEN)",
    )
    parser.add_argument("--output", help="Write review to file")
    parser.add_argument(
        "--max-diff-bytes", type=int, default=DEFAULT_MAX_DIFF_BYTES,
        help=f"Max diff size in bytes before truncation (default: {DEFAULT_MAX_DIFF_BYTES})",
    )
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args(argv)

    if not args.pr and not args.diff:
        parser.error("Either --pr or --diff is required")

    # --- Resolve backend ---
    backend = select_backend(args.backend)
    verbose = args.verbose

    if verbose:
        print(f"Backend: {backend}", file=sys.stderr)

    # --- Fetch diff and metadata ---
    meta: Optional[PRMetadata] = None
    diff_text = ""

    if args.pr:
        try:
            owner, repo, number = parse_pr_ref(args.pr)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        token = os.environ.get("GITHUB_TOKEN")
        if verbose:
            print(f"Fetching PR {owner}/{repo}#{number}...", file=sys.stderr)

        try:
            meta = fetch_pr_metadata(owner, repo, number, token)
            diff_text = fetch_pr_diff(owner, repo, number, token)
        except urllib.error.HTTPError as e:
            print(f"GitHub API error: {e.code} {e.reason}", file=sys.stderr)
            if e.code == 404:
                print("PR not found. Check the URL or ensure GITHUB_TOKEN is set for private repos.", file=sys.stderr)
            elif e.code == 403:
                print("Rate limited. Set GITHUB_TOKEN for higher limits.", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error fetching PR: {e}", file=sys.stderr)
            return 1

        if verbose:
            print(f"Title: {meta.title}", file=sys.stderr)
            print(f"Files: {meta.files_changed}, +{meta.additions}/-{meta.deletions}", file=sys.stderr)
            print(f"Diff size: {len(diff_text)} bytes", file=sys.stderr)
    else:
        # Read local diff file
        try:
            with open(args.diff, "r", encoding="utf-8", errors="replace") as f:
                diff_text = f.read()
        except OSError as e:
            print(f"Error reading diff file: {e}", file=sys.stderr)
            return 1

    # --- Truncate if needed ---
    diff_text = truncate_diff(diff_text, args.max_diff_bytes)

    # --- Run review ---
    if verbose:
        print(f"Running review with backend: {backend}...", file=sys.stderr)

    try:
        if backend == "heuristic":
            review = heuristic_review(diff_text, meta)
            output = format_review(review, meta)

        elif backend == "anthropic":
            raw = anthropic_review(diff_text, meta, args.model or "claude-sonnet-4-20250514")
            model_name = args.model or "claude-sonnet-4-20250514"
            output = format_raw_review(raw, meta, backend="anthropic", model=model_name)

        elif backend == "claude-cli":
            raw = claude_cli_review(diff_text, meta, args.model)
            model_name = args.model or "claude-cli-default"
            output = format_raw_review(raw, meta, backend="claude-cli", model=model_name)

        else:
            print(f"Unknown backend: {backend}", file=sys.stderr)
            return 1

    except RuntimeError as e:
        print(f"Review error: {e}", file=sys.stderr)
        if backend != "heuristic":
            print("Falling back to heuristic backend...", file=sys.stderr)
            review = heuristic_review(diff_text, meta)
            output = format_review(review, meta)
        else:
            return 1

    # --- Output ---
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        if verbose:
            print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)

    # --- Post comment if requested ---
    if args.post_comment and meta:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            print("Error: --post-comment requires GITHUB_TOKEN", file=sys.stderr)
            return 1
        try:
            owner, repo, number = parse_pr_ref(args.pr)
            post_pr_comment(owner, repo, number, output, token)
        except Exception as e:
            print(f"Error posting comment: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
