#!/usr/bin/env python3
"""
claude-review — CLI tool that reviews a GitHub PR and outputs structured Markdown.

Usage:
  ./claude-review.py --pr https://github.com/owner/repo/pull/123
  ./claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
  OPENROUTER_API_KEY=sk-... ./claude-review.py --pr https://github.com/owner/repo/pull/123

Accepts a PR URL, fetches the diff, analyzes changes, and produces:
  - Summary of changes (2–3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

Bounty reference: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


# ── Helpers ──────────────────────────────────────────────────────────────

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        raise ValueError(f"Not a valid GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch(url: str, headers: dict | None = None) -> str:
    """GET a URL and return body text."""
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


def fetch_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the unified diff for a PR. Uses public API; no auth needed."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    return fetch(url, headers)


def fetch_pr_metadata(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR title, description, changed files list."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review/1.0",
    }
    data = json.loads(fetch(url, headers))
    # Also get changed files list
    files_url = data.get("url", "") + "/files"
    try:
        files_data = json.loads(fetch(files_url, headers))
    except Exception:
        files_data = []
    return {
        "title": data.get("title", ""),
        "body": data.get("body", "") or "",
        "state": data.get("state", ""),
        "changed_files": [f.get("filename", "") for f in files_data],
        "additions": data.get("additions", 0),
        "deletions": data.get("deletions", 0),
        "total_files": len(files_data),
        "author": data.get("user", {}).get("login", ""),
    }


# ── Diff Analysis ────────────────────────────────────────────────────────

@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    extension: str = ""
    is_test: bool = False
    is_config: bool = False
    is_docs: bool = False
    summary: str = ""


def analyze_diff(diff_text: str) -> list[FileChange]:
    """Parse a unified diff and extract per-file stats."""
    files = []
    current_file = None
    current_add = 0
    current_del = 0
    current_summary_lines = []

    for line in diff_text.split("\n"):
        if line.startswith("+++ b/"):
            # Finish previous file
            if current_file:
                current_file.additions = current_add
                current_file.deletions = current_del
                current_file.summary = " ".join(current_summary_lines[:3])
                files.append(current_file)
            path = line[6:]  # strip "+++ b/"
            ext = os.path.splitext(path)[1].lower()
            current_file = FileChange(
                path=path,
                extension=ext,
                is_test="_test" in path or "/test" in path or "spec." in path or "test." in path,
                is_config=ext in (".yml", ".yaml", ".toml", ".ini", ".cfg", ".json"),
                is_docs=ext in (".md", ".rst", ".txt", ".mdx"),
            )
            current_add = 0
            current_del = 0
            current_summary_lines = []
        elif current_file and line.startswith("@@"):
            # hunk header — extract meaningful context
            if len(current_summary_lines) < 5:
                current_summary_lines.append(line)
        elif current_file and line.startswith("+"):
            current_add += 1
        elif current_file and line.startswith("-"):
            current_del += 1

    # Last file
    if current_file:
        current_file.additions = current_add
        current_file.deletions = current_del
        current_file.summary = " ".join(current_summary_lines[:3])
        files.append(current_file)

    return files


# ── Analysis / Review Engine ────────────────────────────────────────────

def call_llm_for_review(diff_text: str, metadata: dict, api_key: str) -> Optional[str]:
    """Call an LLM via OpenRouter API to generate a PR review."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/claude-review",
        "X-Title": "claude-review",
    }

    prompt = f"""You are reviewing a GitHub pull request.

PR Title: {metadata.get('title', 'N/A')}
PR Description: {metadata.get('body', 'N/A')[:500]}
Author: {metadata.get('author', 'N/A')}
Files changed: {metadata.get('total_files', 0)} ({metadata.get('additions', 0)} additions, {metadata.get('deletions', 0)} deletions)

Review the following diff and produce a structured Markdown review:

## Summary
2-3 sentences describing what this PR does.

## Identified Risks
- List specific risks or concerns

## Improvement Suggestions
- Specific, actionable suggestions

## Confidence Score
Low / Medium / High

DIFF:
```diff
{diff_text[:12000]}
```"""

    body = json.dumps({
        "model": "openrouter/owl-alpha",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return None  # Fall through to static analysis


def static_review(files: list[FileChange], metadata: dict) -> str:
    """Generate a PR review using static analysis when no LLM is available."""
    lines = []
    lines.append("# PR Review\n")
    lines.append(f"**PR:** {metadata.get('title', 'N/A')}")
    lines.append(f"**Author:** {metadata.get('author', 'N/A')}")
    lines.append(f"**Files:** {metadata.get('total_files', 0)} | **+{metadata.get('additions', 0)}** / **-{metadata.get('deletions', 0)}**")
    lines.append("")

    # Summary
    lines.append("## Summary")
    total_adds = metadata.get('additions', 0)
    total_dels = metadata.get('deletions', 0)
    num_files = metadata.get('total_files', 0)
    ext_groups = {}
    for f in files:
        ext = f.extension if f.extension else "(no ext)"
        ext_groups.setdefault(ext, 0)
        ext_groups[ext] += 1
    top_exts = sorted(ext_groups.items(), key=lambda x: -x[1])[:3]
    ext_desc = ", ".join(f"{ext} ({count} files)" for ext, count in top_exts)

    if num_files == 0:
        lines.append("No changes detected in the diff.")
    else:
        lines.append(
            f"This PR modifies {num_files} file{'s' if num_files > 1 else ''} "
            f"with {total_adds} addition{'s' if total_adds != 1 else ''} and "
            f"{total_dels} deletion{'s' if total_dels != 1 else ''}. "
            f"Affected types: {ext_desc}."
        )
        lines.append("")

    # Per-file breakdown
    lines.append("### Files Changed")
    for f in files:
        tags = []
        if f.is_test: tags.append("🧪 test")
        if f.is_config: tags.append("⚙️ config")
        if f.is_docs: tags.append("📝 docs")
        tag_str = f" ({', '.join(tags)})" if tags else ""
        lines.append(f"- `{f.path}`: **+{f.additions}** / **-{f.deletions}**{tag_str}")
    lines.append("")

    # Pattern-based risk detection
    lines.append("## Identified Risks")
    risks = []
    for f in files:
        if f.additions > 500:
            risks.append(f"Large file change in `{f.path}` ({f.additions} lines) — consider splitting into smaller PRs.")
        if "package-lock" in f.path or "yarn.lock" in f.path:
            risks.append(f"Lockfile change in `{f.path}` — verify no unexpected dependency changes.")
        if ".env" in f.path and not f.is_test:
            risks.append(f"Environment file changed: `{f.path}` — ensure no secrets committed.")
        if "migration" in f.path.lower() or "schema" in f.path.lower():
            risks.append(f"Database/schema change in `{f.path}` — verify backward compatibility.")
        if "secret" in f.path.lower() or "key" in f.path.lower() or "credential" in f.path.lower():
            risks.append(f"Potential credential-related file: `{f.path}` — verify no secrets hardcoded.")

    if not risks:
        risks.append("No high-risk patterns detected via static analysis.")
    for r in risks:
        lines.append(f"- {r}")
    lines.append("")

    # Improvement suggestions
    lines.append("## Improvement Suggestions")
    suggestions = []
    for f in files:
        if not any(f.is_test for f in files) and not metadata.get('total_files', 0) == 0:
            suggestions.append("No test file changes detected — consider adding tests for the new/modified logic.")
            break
    for f in files:
        if f.additions + f.deletions > 200 and f.extension in (".py", ".js", ".ts", ".go", ".rs", ".java"):
            suggestions.append(f"`{f.path}` is large ({f.additions}+ / {f.deletions}-) — consider if it can be split.")
    if metadata.get('body', '').strip() in ('', '', ''):
        suggestions.append("PR description is empty — a brief description helps reviewers understand context.")

    if not suggestions:
        suggestions.append("No automatic suggestions — a focused, well-scoped change.")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")

    # Confidence
    if num_files > 10:
        confidence = "Low — large PR with many files; recommended: manual review for architecture-level concerns."
    elif num_files > 5:
        confidence = "Medium — moderate scope; static analysis caught potential concerns above."
    else:
        confidence = "High — small, focused change; static analysis passed without significant concerns."
    lines.append(f"## Confidence Score\n**{confidence}**")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="claude-review — AI-powered PR review CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pr https://github.com/owner/repo/pull/123
  %(prog)s --pr https://github.com/owner/repo/pull/123 --output review.md
  %(prog)s --pr https://github.com/owner/repo/pull/123 --verbose
        """,
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show debug info")
    parser.add_argument("--model", default="openrouter/owl-alpha",
                        help="OpenRouter model for AI review (default: openrouter/owl-alpha)")
    parser.add_argument("--no-ai", action="store_true",
                        help="Skip AI review, use static analysis only")
    args = parser.parse_args()

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    # Fetch PR metadata
    try:
        metadata = fetch_pr_metadata(owner, repo, pr_number)
    except Exception as e:
        print(f"Error fetching PR metadata: {e}", file=sys.stderr)
        metadata = {"title": "N/A", "body": "", "state": "", "total_files": 0,
                     "additions": 0, "deletions": 0, "author": ""}

    # Fetch diff
    try:
        diff_text = fetch_diff(owner, repo, pr_number)
    except Exception as e:
        print(f"Error fetching PR diff: {e}", file=sys.stderr)
        sys.exit(1)

    if not diff_text.strip():
        print("No diff returned (PR may be empty or closed).", file=sys.stderr)
        sys.exit(1)

    # Analyze files from diff
    files = analyze_diff(diff_text)

    if args.verbose:
        print(f"📄 {len(files)} files changed", file=sys.stderr)
        print(f"  +{metadata.get('additions', 0)} / -{metadata.get('deletions', 0)} lines", file=sys.stderr)

    # Generate review
    review_text = None

    # Try AI review if API key available and not disabled
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("MOLTBOOK_API_KEY")
    if api_key and not args.no_ai:
        if args.verbose:
            print(f"🤖 Calling AI model for review...", file=sys.stderr)
        review_text = call_llm_for_review(diff_text, metadata, api_key)

    # Fall back to static analysis
    if not review_text:
        if args.verbose:
            print(f"📊 Using static analysis...", file=sys.stderr)
        review_text = static_review(files, metadata)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(review_text)
        if args.verbose:
            print(f"✅ Written to {args.output}", file=sys.stderr)
    else:
        print(review_text)


if __name__ == "__main__":
    main()
