#!/usr/bin/env python3
"""
Claude PR Review Agent
CLI tool and GitHub Action for automated PR code review using Claude API.
"""
import os
import sys
import json
import click
import anthropic
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def fetch_pr_diff(pr_url: str) -> dict:
    """Fetch PR diff and metadata from GitHub API."""
    # Parse PR URL: https://github.com/owner/repo/pull/123
    parts = pr_url.replace("https://github.com/", "").split("/")
    if len(parts) < 4 or parts[2] != "pull":
        raise ValueError(f"Invalid PR URL format: {pr_url}")

    owner, repo, _, pr_number = parts[0], parts[1], parts[2], parts[3]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    headers = {"Accept": "application/vnd.github.v3.diff"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(api_url, headers=headers)
    try:
        with urlopen(req, timeout=30) as response:
            diff = response.read().decode("utf-8")
    except HTTPError as e:
        raise RuntimeError(f"GitHub API error {e.code}: {e.reason}")
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")

    # Fetch PR metadata
    headers["Accept"] = "application/vnd.github.v3+json"
    req = Request(api_url, headers=headers)
    with urlopen(req, timeout=30) as response:
        metadata = json.loads(response.read().decode("utf-8"))

    return {
        "diff": diff,
        "title": metadata.get("title", ""),
        "url": pr_url,
        "files_changed": metadata.get("changed_files", 0),
        "additions": metadata.get("additions", 0),
        "deletions": metadata.get("deletions", 0),
    }

def analyze_pr_with_claude(pr_data: dict, api_key: str) -> str:
    """Analyze PR diff using Claude and return structured review."""
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a senior code reviewer. Analyze this GitHub Pull Request and provide a structured review.

PR Title: {pr_data['title']}
PR URL: {pr_data['url']}
Files Changed: {pr_data['files_changed']} | +{pr_data['additions']} -{pr_data['deletions']}

DIFF:
```
{pr_data['diff'][:15000]}
```

Provide a review in this EXACT Markdown format:

## 📋 Summary
[2-3 sentence summary of changes]

## ⚠️ Identified Risks
- [Risk 1]
- [Risk 2]
- [Risk 3 or "None identified"]

## 💡 Improvement Suggestions
- [Suggestion 1]
- [Suggestion 2]
- [Suggestion 3 or "Code looks good"]

## 🎯 Confidence Score
**[Low / Medium / High]**

Justification: [1 sentence why this confidence level]
"""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        raise RuntimeError(f"Claude API error: {str(e)}")

@click.command()
@click.option("--pr", required=True, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
def main(pr: str, api_key: str):
    """Analyze a GitHub PR and generate a structured code review using Claude."""
    if not api_key:
        click.echo("❌ Error: ANTHROPIC_API_KEY not set", err=True)
        sys.exit(1)

    click.echo(f"🔍 Fetching PR: {pr}")
    try:
        pr_data = fetch_pr_diff(pr)
    except Exception as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)

    click.echo(f"📊 Files changed: {pr_data['files_changed']} | +{pr_data['additions']} -{pr_data['deletions']}")
    click.echo("🤖 Analyzing with Claude...")

    try:
        review = analyze_pr_with_claude(pr_data, api_key)
    except Exception as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)

    click.echo("\n" + "="*80 + "\n")
    click.echo(review)
    click.echo("\n" + "="*80)
    click.echo("✅ Review complete")

if __name__ == "__main__":
    main()
