#!/usr/bin/env python3
"""Claude PR Reviewer — CLI tool that reviews GitHub PRs and outputs structured Markdown."""

import argparse
import os
import re
import subprocess
import sys

import anthropic

MODEL = "claude-sonnet-4-20250514"
MAX_DIFF_LINES = 15000

REVIEW_PROMPT = """\
You are a senior software engineer performing a pull request code review.
Analyze the following PR diff and produce a structured review in Markdown format.

Your review MUST follow this exact structure:

## Summary
(2-3 sentences describing what this PR does and why)

## Risks
(Bulleted list of potential risks: bugs, security issues, performance problems, breaking changes.
If none found, write "- No significant risks identified.")

## Suggestions
(Bulleted list of improvement suggestions: code quality, readability, testing, edge cases.
If none, write "- No suggestions — changes look good.")

## Confidence
(One of: **Low** / **Medium** / **High**)
- **Low**: Complex changes, unclear intent, or insufficient context to judge correctness
- **Medium**: Reasonable changes with some areas that need closer inspection
- **High**: Clear, simple, well-structured changes that are easy to verify

---

Rules:
- Be specific — reference file names and line numbers from the diff when possible.
- Focus on substance, not style nitpicks.
- If the diff is a test-only change, note that the risk is inherently low.
- Keep the review concise but thorough.
"""


def parse_pr_url(url: str) -> tuple[str, int]:
    """Extract owner/repo and PR number from a GitHub PR URL."""
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", url)
    if not match:
        print(f"Error: Invalid PR URL: {url}", file=sys.stderr)
        print("Expected format: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    return match.group(1), int(match.group(2))


def fetch_pr_diff(repo: str, pr_number: int) -> str:
    """Fetch PR diff using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr_number), "--repo", repo],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except FileNotFoundError:
        print("Error: 'gh' CLI not found. Install it: https://cli.github.com/", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Error: Timed out fetching PR diff.", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        print(f"Error fetching PR diff: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    return result.stdout


def fetch_pr_metadata(repo: str, pr_number: int) -> dict:
    """Fetch PR title and body using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(pr_number), "--repo", repo, "--json", "title,body,author"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}

    if result.returncode != 0:
        return {}

    import json
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def truncate_diff(diff: str, max_lines: int = MAX_DIFF_LINES) -> str:
    """Truncate diff if too large, keeping a note about truncation."""
    lines = diff.split("\n")
    if len(lines) <= max_lines:
        return diff
    truncated = "\n".join(lines[:max_lines])
    truncated += f"\n\n... [TRUNCATED — diff had {len(lines)} lines, showing first {max_lines}]"
    return truncated


def review_pr(diff: str, metadata: dict) -> str:
    """Send diff to Claude API and get structured review."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    user_content = ""
    if metadata:
        title = metadata.get("title", "")
        body = metadata.get("body", "") or ""
        author = metadata.get("author", {})
        author_login = author.get("login", "unknown") if isinstance(author, dict) else str(author)
        user_content += f"**PR Title:** {title}\n**Author:** {author_login}\n"
        if body.strip():
            # Limit PR body to avoid wasting tokens
            body_truncated = body[:2000] + ("..." if len(body) > 2000 else "")
            user_content += f"**PR Description:**\n{body_truncated}\n\n"

    user_content += f"**Diff:**\n```diff\n{diff}\n```"

    message = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[
            {"role": "user", "content": user_content},
        ],
        system=REVIEW_PROMPT,
    )

    return message.content[0].text


def main():
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub PR using Claude AI and output structured Markdown.",
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)",
    )
    parser.add_argument(
        "--output",
        help="Write output to a file instead of stdout.",
    )
    args = parser.parse_args()

    repo, pr_number = parse_pr_url(args.pr)

    # Fetch diff and metadata
    diff = fetch_pr_diff(repo, pr_number)
    if not diff.strip():
        print("Error: PR diff is empty.", file=sys.stderr)
        sys.exit(1)

    diff = truncate_diff(diff)
    metadata = fetch_pr_metadata(repo, pr_number)

    # Build header
    title = metadata.get("title", f"PR #{pr_number}")
    header = f"# PR Review: {title}\n"
    header += f"**Repository:** [{repo}](https://github.com/{repo})\n"
    header += f"**PR:** [#{pr_number}](https://github.com/{repo}/pull/{pr_number})\n\n"
    header += "---\n\n"

    # Get review from Claude
    review = review_pr(diff, metadata)

    output = header + review + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
