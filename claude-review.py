#!/usr/bin/env python3
"""
claude-review — Claude Code PR reviewer CLI

Usage:
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output report.md
  claude-review --pr 123 --repo owner/repo          # Short form
"""

import argparse, json, os, re, subprocess, sys, tempfile, textwrap
from datetime import datetime, timezone
from pathlib import Path


# ── Config ──────────────────────────────────────────────────────

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "/usr/local/bin/claude")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("GH_TOKEN", ""))


# ── GitHub API ──────────────────────────────────────────────────

def fetch_pr_info(owner: str, repo: str, pr_number: int, token: str):
    """Fetch PR metadata and diff from GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    import urllib.request

    # Fetch PR metadata
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={**headers, "Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            pr_data = json.loads(resp.read().decode())
    except Exception as e:
        raise RuntimeError(f"Failed to fetch PR metadata: {e}")

    # Fetch diff
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    diff_req = urllib.request.Request(diff_url, headers=headers)
    try:
        with urllib.request.urlopen(diff_req, timeout=30) as resp:
            diff = resp.read().decode()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch PR diff: {e}")

    return {
        "title": pr_data.get("title", ""),
        "body": pr_data.get("body", "") or "",
        "author": pr_data.get("user", {}).get("login", "unknown"),
        "state": pr_data.get("state", ""),
        "created_at": pr_data.get("created_at", ""),
        "changed_files": pr_data.get("changed_files", 0),
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
        "diff": diff,
        "url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
    }


def parse_pr_url(url: str) -> tuple:
    """Parse 'https://github.com/owner/repo/pull/123' or 'owner/repo#123'."""
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    m = re.search(r"([^/]+)/([^#]+)#(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(f"Could not parse PR URL: {url}")


# ── Claude Review ───────────────────────────────────────────────

def call_claude_for_review(pr_info: dict) -> str:
    """Send PR diff to Claude Code for review."""
    # Build a concise prompt with the diff
    diff = pr_info["diff"]
    # Truncate diff if too large (200KB limit)
    if len(diff) > 200_000:
        diff = diff[:200_000] + "\n...(diff truncated due to size)"

    prompt = textwrap.dedent(f"""
    You are a senior code reviewer. Review this PR and output structured Markdown.

    PR: {pr_info['title']}
    Author: {pr_info['author']}
    Files changed: {pr_info['changed_files']} (+{pr_info['additions']}/-{pr_info['deletions']})

    Analyze the following diff and output in this exact format:

    ## Review: {pr_info['title']}

    ### Summary
    (2-3 sentence summary of what this PR does)

    ### Identified Risks
    - (list specific risks with file/line references)

    ### Improvement Suggestions
    - (actionable suggestions)

    ### Confidence Score
    **High** / **Medium** / **Low**
    (brief justification)

    ---

    ```diff
    {diff}
    ```
    """)

    try:
        r = subprocess.run(
            [CLAUDE_BIN, "-p", prompt.strip(), "--bare", "--effort", "high"],
            capture_output=True, text=True, timeout=180,
            env={**os.environ, "CLAUDE_CODE_SIMPLE": "1"}
        )
        if r.returncode == 0:
            return r.stdout.strip()
        else:
            return f"## Review Failed\n\nClaude returned exit code {r.returncode}:\n```\n{r.stderr[:500]}\n```"
    except subprocess.TimeoutExpired:
        return "## Review Failed\n\nClaude timed out after 180 seconds."
    except FileNotFoundError:
        return f"## Review Failed\n\nClaude CLI not found at {CLAUDE_BIN}. Install with: npm install -g @anthropic-ai/claude-code"


# ── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR reviewer — structured Markdown review comments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          claude-review --pr https://github.com/owner/repo/pull/123
          claude-review --pr 123 --repo owner/repo
          claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
          GITHUB_TOKEN=ghp_xxx claude-review --pr https://github.com/owner/repo/pull/123
        """)
    )
    parser.add_argument("--pr", type=str, required=True, help="PR URL or owner/repo#123")
    parser.add_argument("--repo", type=str, help="owner/repo (if --pr is just a number)")
    parser.add_argument("--output", "-o", type=str, help="Write output to file")
    parser.add_argument("--token", type=str, default=GITHUB_TOKEN, help="GitHub token")
    args = parser.parse_args()

    # Parse PR identifier
    try:
        if re.match(r"^\d+$", args.pr) and args.repo:
            owner, repo = args.repo.split("/")
            pr_number = int(args.pr)
        else:
            owner, repo, pr_number = parse_pr_url(args.pr)
    except (ValueError, IndexError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch PR
    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    try:
        pr_info = fetch_pr_info(owner, repo, pr_number, args.token)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"📄 PR: {pr_info['title']}", file=sys.stderr)
    print(f"   {pr_info['changed_files']} files, +{pr_info['additions']}/-{pr_info['deletions']}", file=sys.stderr)

    # Review
    print(f"🤖 Sending to Claude for review...", file=sys.stderr)
    review = call_claude_for_review(pr_info)

    # Add header metadata
    header = f"> Reviewed by **claude-review** · {pr_info['url']}\n>\n> _{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n\n"
    output = header + review

    # Output
    if args.output:
        Path(args.output).write_text(output)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
