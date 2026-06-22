#!/usr/bin/env python3
"""claude-review: A Claude Code agent that reviews GitHub PRs."""

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from urllib.request import Request, urlopen
from urllib.error import HTTPError


REVIEW_PROMPT = textwrap.dedent("""\
    You are a senior code reviewer. Analyze the following PR diff and provide
    a structured review in Markdown.

    Format your response EXACTLY as follows (use these exact headers):

    ## Summary
    2-3 sentence summary of the changes.

    ## Risks
    - Risk 1
    - Risk 2
    (list any potential issues, breaking changes, security concerns, etc.)

    ## Suggestions
    - Suggestion 1
    - Suggestion 2
    (list improvements, best practices, or cleaner alternatives)

    ## Confidence
    Low / Medium / High

    PR diff:
    {diff}
""")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    pattern = r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError(f"Invalid PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch PR diff using the gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr_number), "--repo", f"{owner}/{repo}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except FileNotFoundError:
        print("Error: 'gh' CLI not found. Install it from https://cli.github.com/", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR diff: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_info(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata using the gh CLI."""
    try:
        result = subprocess.run(
            [
                "gh", "pr", "view", str(pr_number),
                "--repo", f"{owner}/{repo}",
                "--json", "title,body,author,headRefName,baseRefName,files",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}


def call_claude(diff: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Call the Anthropic API to review the diff."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        print("Get your key at https://console.anthropic.com/", file=sys.stderr)
        sys.exit(1)

    prompt = REVIEW_PROMPT.format(diff=diff[:100_000])  # Truncate very large diffs

    payload = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except HTTPError as e:
        body = e.read().decode()
        print(f"API error ({e.code}): {body}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, IndexError):
        print("Unexpected API response format.", file=sys.stderr)
        sys.exit(1)


def call_claude_code(diff: str) -> str:
    """Use Claude Code CLI as the review engine (no API key needed)."""
    prompt = f"Review this PR diff and give a structured review with sections: Summary, Risks, Suggestions, Confidence.\n\n{diff[:100_000]}"

    try:
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except FileNotFoundError:
        print("Error: 'claude' CLI not found. Install Claude Code.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running Claude Code: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              claude-review --pr https://github.com/owner/repo/pull/123
              claude-review --pr https://github.com/owner/repo/pull/123 --engine claude-code
              claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
        """),
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument(
        "--engine",
        choices=["api", "claude-code"],
        default="api",
        help="Review engine: 'api' (Anthropic API) or 'claude-code' (Claude Code CLI). Default: api",
    )
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Anthropic model (API engine only)")
    parser.add_argument("--output", "-o", help="Write review to file instead of stdout")

    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)
    print(f"Reviewing {owner}/{repo}#{pr_number}...", file=sys.stderr)

    pr_info = fetch_pr_info(owner, repo, pr_number)
    diff = fetch_pr_diff(owner, repo, pr_number)

    if not diff.strip():
        print("No diff found for this PR.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetched diff ({len(diff)} bytes). Running review...", file=sys.stderr)

    if args.engine == "claude-code":
        review = call_claude_code(diff)
    else:
        review = call_claude(diff, model=args.model)

    header = f"# PR Review: {owner}/{repo}#{pr_number}"
    if pr_info.get("title"):
        header += f" — {pr_info['title']}"

    output = f"{header}\n\n{review}"

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
