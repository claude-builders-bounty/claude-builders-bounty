#!/usr/bin/env python3
"""
claude-review: AI-powered PR reviewer using Claude API
Usage: claude-review --pr https://github.com/owner/repo/pull/123
"""

import argparse
import os
import sys
import json
import re
import urllib.request
import urllib.error
from datetime import datetime


def github_api_get(url: str, token: str) -> dict:
    """Make authenticated GitHub API request."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"token {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "claude-review/1.0")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Fetch the PR diff from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.diff")
    req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "claude-review/1.0")
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_pr_info(owner: str, repo: str, pr_number: int, token: str) -> dict:
    """Get PR metadata."""
    return github_api_get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
        token
    )


def get_pr_files(owner: str, repo: str, pr_number: int, token: str) -> list:
    """Get list of changed files."""
    return github_api_get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
        token
    )


def call_claude(prompt: str, api_key: str, model: str = "claude-sonnet-4-5") -> str:
    """Call Claude API and return the response text."""
    payload = json.dumps({
        "model": model,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST"
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data["content"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"Claude API error {e.code}: {error_body}")


def parse_pr_url(url: str):
    """Parse GitHub PR URL into (owner, repo, pr_number)."""
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        url.strip()
    )
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def build_review_prompt(pr_info: dict, files: list, diff: str, lang: str = "EN") -> str:
    """Build the review prompt for Claude."""
    file_summary = "\n".join([
        f"- {f['filename']} (+{f['additions']}/-{f['deletions']})"
        for f in files[:30]
    ])

    # Truncate diff if too long
    diff_truncated = diff[:12000]
    if len(diff) > 12000:
        diff_truncated += "\n\n[... diff truncated for length ...]"

    if lang == "FR":
        instruction = """Analyse cette Pull Request GitHub et génère une revue de code structurée en Markdown.

Inclure obligatoirement:
1. **Résumé des changements** (2-3 phrases)
2. **Risques identifiés** (liste à puces, vide si aucun)
3. **Suggestions d'amélioration** (liste à puces)
4. **Score de confiance**: Faible / Moyen / Élevé (avec justification)

Sois précis, technique et actionnable. Cite des lignes/fichiers spécifiques."""
    else:
        instruction = """Analyze this GitHub Pull Request and generate a structured Markdown code review.

You MUST include these exact sections:
1. **Summary of Changes** (2-3 sentences)
2. **Identified Risks** (bullet list — empty if none)
3. **Improvement Suggestions** (bullet list)
4. **Confidence Score**: Low / Medium / High (with one-line justification)

Be specific, technical, and actionable. Reference specific files/lines when relevant."""

    return f"""{instruction}

## PR Information
- **Title**: {pr_info.get('title', 'N/A')}
- **Author**: @{pr_info.get('user', {}).get('login', 'unknown')}
- **Repository**: {pr_info.get('base', {}).get('repo', {}).get('full_name', 'N/A')}
- **Base branch**: {pr_info.get('base', {}).get('ref', 'main')} ← {pr_info.get('head', {}).get('ref', 'feature')}
- **Description**: {pr_info.get('body', '(no description)') or '(no description)'}

## Changed Files ({len(files)} total)
{file_summary}

## Diff
```diff
{diff_truncated}
```
"""


def format_review(review_text: str, pr_info: dict, pr_url: str) -> str:
    """Format the final review output."""
    repo = pr_info.get('base', {}).get('repo', {}).get('full_name', 'unknown/repo')
    pr_number = pr_info.get('number', '?')
    title = pr_info.get('title', 'N/A')
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    return f"""# 🤖 Claude Code Review

**PR**: [{repo}#{pr_number}]({pr_url}) — {title}
**Generated**: {generated_at}

---

{review_text}

---
*Generated by [claude-review](https://github.com/santozion17-afk/claude-builders-bounty/tree/feature/claude-review-agent) using Claude API*
"""


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered GitHub PR reviewer using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --lang FR
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
        """
    )
    parser.add_argument(
        "--pr", required=True,
        help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--lang", default="EN", choices=["EN", "FR"],
        help="Language for the review (default: EN)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output file path (default: prints to stdout)"
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-5",
        help="Claude model to use (default: claude-sonnet-4-5)"
    )

    args = parser.parse_args()

    # Get credentials from environment
    github_token = os.environ.get("GITHUB_TOKEN")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        print("  export GITHUB_TOKEN=ghp_your_token_here", file=sys.stderr)
        sys.exit(1)

    if not anthropic_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY=sk-ant-your_key_here", file=sys.stderr)
        sys.exit(1)

    # Parse PR URL
    print(f"📥 Fetching PR data from GitHub...", file=sys.stderr)
    owner, repo, pr_number = parse_pr_url(args.pr)

    # Fetch PR data
    pr_info = get_pr_info(owner, repo, pr_number, github_token)
    files = get_pr_files(owner, repo, pr_number, github_token)
    diff = get_pr_diff(owner, repo, pr_number, github_token)

    print(f"✅ Fetched: {len(files)} files changed, {len(diff)} chars diff", file=sys.stderr)
    print(f"🤖 Calling Claude ({args.model})...", file=sys.stderr)

    # Build prompt and call Claude
    prompt = build_review_prompt(pr_info, files, diff, args.lang)
    review_text = call_claude(prompt, anthropic_key, args.model)

    # Format output
    final_output = format_review(review_text, pr_info, args.pr)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(final_output)
        print(f"✅ Review saved to {args.output}", file=sys.stderr)
    else:
        print(final_output)


if __name__ == "__main__":
    main()
