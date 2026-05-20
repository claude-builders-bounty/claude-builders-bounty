#!/usr/bin/env python3
"""
claude-review: PR Review Sub-Agent for Claude Code
====================================================

A Claude Code sub-agent that takes a PR diff as input, analyzes it using 
the Claude API, and returns a structured Markdown review comment.

Usage:
    # Direct PR review via URL
    claude-review --pr https://github.com/owner/repo/pull/123
    
    # Review from a local diff file
    claude-review --diff-file path/to/diff.patch
    
    # Review from stdin
    git diff main...feature | claude-review --stdin
    
    # Specify repo context for better analysis
    claude-review --pr https://github.com/owner/repo/pull/123 --repo owner/repo

Requirements:
    - ANTHROPIC_API_KEY environment variable
    - Python 3.9+
    - anthropic, requests packages

Author: @alicyh
Bounty: #4 ($150) — Claude Code sub-agent that reviews a PR
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Optional

try:
    from anthropic import Anthropic, APIStatusError, APIConnectionError
except ImportError:
    sys.exit("Error: 'anthropic' package required. Install: pip install anthropic")

try:
    import requests
except ImportError:
    sys.exit("Error: 'requests' package required. Install: pip install requests")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
DIFF_MAX_LINES = 600  # Truncate huge diffs to stay within context

SYSTEM_PROMPT = """You are a senior software engineer performing a code review. 
Your goal is to provide a concise, actionable review of a pull request diff.

Guidelines:
- Focus on: logic bugs, security issues, performance problems, race conditions, 
  error handling gaps, API misuse, and code clarity.
- Ignore: formatting issues, missing semicolons, minor style nitpicks.
- For each risk/issue: state the FILE and LINE NUMBER (use @@ hunk headers).
- If there are genuinely no issues, say so clearly — don't fabricate problems.
- Always include a confidence score reflecting how well you can assess the changes.

Output a structured Markdown review (see format in the prompt)."""

REVIEW_PROMPT_TEMPLATE = """Review the following GitHub pull request diff. 
Provide a structured Markdown review with exactly these sections:

## Summary
(2–3 sentences summarizing what the PR changes)

## Identified Risks
(List each risk as: **`filename:line`** — description. If none, write "No risks identified.")

## Improvement Suggestions
(List each suggestion as a bullet point. If none, write "No suggestions.")

## Confidence
**{score}** — (one of: Low / Medium / High, with a brief 1-sentence justification)

---
### PR Diff:
```diff
{diff}
```

Start your review now:"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_pr_diff(pr_url: str) -> tuple[str, str]:
    """Fetch the diff and PR title from a GitHub PR URL via the API.
    Returns (diff_text, pr_title).
    """
    # Parse owner/repo/pull/number from URL
    m = re.match(
        r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)',
        pr_url.rstrip('/'),
    )
    if not m:
        raise ValueError(f"Cannot parse GitHub PR URL: {pr_url}")

    owner, repo, pr_number = m.groups()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Fetch PR title
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    pr_resp = requests.get(api_url, headers={
        **headers, "Accept": "application/vnd.github.v3+json"
    })
    pr_resp.raise_for_status()
    pr_data = pr_resp.json()
    pr_title = pr_data.get("title", f"{owner}/{repo}#{pr_number}")

    # Fetch diff
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}.diff"
    diff_resp = requests.get(diff_url, headers=headers)
    diff_resp.raise_for_status()

    return diff_resp.text, pr_title


def truncate_diff(diff: str, max_lines: int = DIFF_MAX_LINES) -> str:
    """Truncate diff to a reasonable number of lines, keeping file headers."""
    lines = diff.split('\n')
    if len(lines) <= max_lines:
        return diff

    truncated = lines[:max_lines]
    truncated.append(
        f"\n... (truncated {len(lines) - max_lines} more lines — "
        f"showing first {max_lines} of {len(lines)} total lines)"
    )
    return '\n'.join(truncated)


def call_claude(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """Send the review prompt to Claude and return the response text."""
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text from response
        for block in message.content:
            if hasattr(block, 'text'):
                return block.text

        return str(message.content)

    except APIConnectionError:
        raise RuntimeError(
            "Failed to connect to Claude API. Check your internet connection."
        )
    except APIStatusError as e:
        raise RuntimeError(f"Claude API error: {e.status_code} — {e.message}")


def build_header(pr_title: str, pr_url: str | None = None) -> str:
    """Build the Markdown review header."""
    lines = [
        f"## 🤖 Claude Code Review: {pr_title}",
        "",
        f"*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) "
        f"on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "---",
        "",
    ]
    if pr_url:
        lines.insert(1, f"**PR:** {pr_url}")
        lines.insert(2, "")
    return "\n".join(lines)


def run_claude_code_agent(diff: str, pr_title: str, pr_url: str | None = None) -> str:
    """
    Attempt to use the 'claude' CLI if available (more natural for a
    Claude Code sub-agent), otherwise fall back to direct API.
    """
    # Try Claude Code CLI first
    cli_paths = [
        os.environ.get("CLAUDE_CLI_PATH", ""),
        "claude",
        "npx @anthropic-ai/claude-code",
    ]

    cli_found = None
    for p in cli_paths:
        if not p:
            continue
        try:
            subprocess.run([p, "--version"], capture_output=True, timeout=5, check=False)
            cli_found = p
            break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    if cli_found:
        # Use Claude Code CLI with --print mode for non-interactive output
        full_prompt = REVIEW_PROMPT_TEMPLATE.format(
            score="Low / Medium / High",
            diff=truncate_diff(diff),
        )

        try:
            result = subprocess.run(
                [cli_found, "--print", full_prompt, "--output-format", "text"],
                capture_output=True, text=True, timeout=120,
                env={**os.environ, "CLAUDE_CODE_SKIP_UPDATE_CHECK": "1"},
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, Exception):
            pass  # Fall through to API

    # Fallback: Direct API call
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        score="Low / Medium / High",
        diff=truncate_diff(diff),
    )
    return call_claude(prompt)


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="claude-review — Claude Code PR review sub-agent ($150 bounty #4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff-file mychanges.diff
  git diff main...feature | claude-review --stdin
  claude-review --pr URL --output-file review.md
        """,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="GitHub PR URL to review")
    source.add_argument("--diff-file", help="Path to a local .diff or .patch file")
    source.add_argument("--stdin", action="store_true", help="Read diff from stdin")

    parser.add_argument("--output-file", "-o", help="Write review to file (default: stdout)")
    parser.add_argument("--no-header", action="store_true", help="Omit the review header")
    parser.add_argument("--confidence-only", action="store_true",
                        help="Only output the confidence score line")
    parser.add_argument("--raw", action="store_true",
                        help="Output raw Claude response without formatting")

    args = parser.parse_args()

    # Validate API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.stderr.write("⚠️  ANTHROPIC_API_KEY not set. Trying Claude Code CLI fallback...\n")

    # --- Load diff ---
    pr_url = None
    pr_title = "Pull Request Review"

    if args.pr:
        pr_url = args.pr
        try:
            diff, pr_title = get_pr_diff(args.pr)
        except requests.HTTPError as e:
            sys.exit(f"❌ Cannot fetch PR: {e}")
        except ValueError as e:
            sys.exit(f"❌ {e}")

    elif args.diff_file:
        with open(args.diff_file, encoding="utf-8") as f:
            diff = f.read()

    elif args.stdin:
        diff = sys.stdin.read()

    else:
        sys.exit("No diff source provided.")

    if not diff.strip():
        sys.exit("❌ Empty diff — nothing to review.")

    # --- Review ---
    try:
        if args.raw:
            # Direct API call, no header
            review = call_claude(
                REVIEW_PROMPT_TEMPLATE.format(
                    score="Low / Medium / High",
                    diff=truncate_diff(diff),
                )
            )
            output = review
        else:
            review = run_claude_code_agent(diff, pr_title, pr_url)
            header = "" if args.no_header else build_header(pr_title, pr_url)
            output = header + "\n" + review

        if args.confidence_only:
            # Extract just the confidence line
            m = re.search(r'\*\*(Low|Medium|High)\*\*', output)
            if m:
                output = f"Confidence: {m.group(1)}"

    except RuntimeError as e:
        sys.exit(f"❌ {e}")

    # --- Output ---
    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ Review saved to {args.output_file}")
    else:
        print(output)


if __name__ == "__main__":
    main()
