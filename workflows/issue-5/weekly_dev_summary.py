#!/usr/bin/env python3
"""
Weekly Dev Summary Generator — Python Alternative to n8n Workflow
=================================================================

This script provides a standalone Python version of the n8n workflow
for generating weekly narrative summaries of GitHub repo activity
using the Claude API (claude-sonnet-4-20250514).

Usage:
    python weekly_dev_summary.py --owner OWNER --repo REPO [--language EN|FR] \
        [--slack-url URL] [--discord-url URL] [--output-dir DIR] [--days N]

Environment Variables:
    GITHUB_TOKEN     — GitHub personal access token (required)
    ANTHROPIC_API_KEY — Anthropic API key (required)
    SLACK_WEBHOOK_URL — Slack incoming webhook URL (optional)
    DISCORD_WEBHOOK_URL — Discord webhook URL (optional)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests library...")
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests


# ─── Configuration ───────────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096


# ─── GitHub Fetchers ─────────────────────────────────────────────────────────

def fetch_commits(owner: str, repo: str, since: str, until: str, token: str) -> list:
    """Fetch commits from GitHub API for the given date range."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "since": f"{since}T00:00:00Z",
        "until": f"{until}T23:59:59Z",
        "per_page": 100,
    }
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return [
        {
            "sha": c.get("sha", "")[:7],
            "message": c.get("commit", {}).get("message", "").split("\n")[0],
            "author": c.get("commit", {}).get("author", {}).get("name", "unknown"),
            "date": c.get("commit", {}).get("author", {}).get("date", ""),
            "url": c.get("html_url", ""),
        }
        for c in resp.json()
    ]


def fetch_closed_issues(owner: str, repo: str, since: str, until: str, token: str) -> list:
    """Fetch closed issues from GitHub API (excludes PRs)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "state": "closed",
        "since": f"{since}T00:00:00Z",
        "per_page": 100,
    }
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "labels": [l["name"] for l in i.get("labels", [])],
            "closed_at": i.get("closed_at", ""),
            "url": i.get("html_url", ""),
        }
        for i in resp.json()
        if "pull_request" not in i  # Exclude PRs
    ]


def fetch_merged_prs(owner: str, repo: str, since: str, until: str, token: str) -> list:
    """Fetch merged pull requests from GitHub API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "state": "closed",
        "per_page": 100,
    }
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return [
        {
            "number": p["number"],
            "title": p["title"],
            "author": p.get("user", {}).get("login", "unknown"),
            "merged_at": p.get("merged_at", ""),
            "url": p.get("html_url", ""),
            "additions": p.get("additions", 0),
            "deletions": p.get("deletions", 0),
        }
        for p in resp.json()
        if p.get("merged_at")  # Only merged PRs
    ]


# ─── Data Aggregation ────────────────────────────────────────────────────────

def aggregate_data(owner: str, repo: str, since: str, until: str, language: str,
                   commits: list, issues: list, prs: list) -> dict:
    """Aggregate fetched data into a structured format."""
    contributor_counts = {}
    for c in commits:
        author = c["author"]
        contributor_counts[author] = contributor_counts.get(author, 0) + 1

    top_contributors = sorted(contributor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_contributors = [{"name": name, "commits": count} for name, count in top_contributors]

    return {
        "repo": f"{owner}/{repo}",
        "weekStart": since,
        "weekEnd": until,
        "language": language,
        "stats": {
            "totalCommits": len(commits),
            "totalClosedIssues": len(issues),
            "totalMergedPRs": len(prs),
        },
        "topContributors": top_contributors,
        "commits": commits,
        "closedIssues": issues,
        "mergedPRs": prs,
    }


# ─── Claude API ──────────────────────────────────────────────────────────────

def generate_summary(data: dict, api_key: str) -> str:
    """Call Claude API to generate the narrative summary."""
    lang = "French" if data["language"] == "FR" else "English"

    prompt = f"""Generate a weekly development summary for the repository "{data['repo']}" covering {data['weekStart']} to {data['weekEnd']}.

Language: {lang}

## Raw Data

### Stats
- Total Commits: {data['stats']['totalCommits']}
- Closed Issues: {data['stats']['totalClosedIssues']}
- Merged PRs: {data['stats']['totalMergedPRs']}

### Top Contributors
{chr(10).join(f"- {c['name']}: {c['commits']} commits" for c in data['topContributors'])}

### Commits
{chr(10).join(f"- [{c['sha']}] {c['message']} ({c['author']})" for c in data['commits'])}

### Closed Issues
{chr(10).join(f"- #{i['number']} {i['title']} {'[' + ', '.join(i['labels']) + ']' if i['labels'] else ''}" for i in data['closedIssues'])}

### Merged PRs
{chr(10).join(f"- #{p['number']} {p['title']} by {p['author']} (+{p['additions']}/-{p['deletions']})" for p in data['mergedPRs'])}

## Instructions
Write a well-structured Markdown summary with these sections:
1. **Overview** — 2-3 sentence narrative of the week's activity
2. **By the Numbers** — key metrics in bullet form
3. **Top Contributors** — acknowledge contributors with commit counts
4. **Key Changes** — highlight the most significant commits/PRs with brief explanations
5. **Closed Issues** — list resolved issues with context
6. **Looking Ahead** — a brief forward-looking statement

Keep the tone professional but engaging. Use emojis sparingly. Do NOT fabricate data not present in the raw data above."""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = requests.post(ANTHROPIC_API, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    result = resp.json()

    return "".join(
        block["text"] for block in result.get("content", []) if block.get("type") == "text"
    )


# ─── Output Delivery ─────────────────────────────────────────────────────────

def save_markdown(summary: str, repo: str, week_start: str, week_end: str, output_dir: str) -> str:
    """Save summary to a Markdown file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    filename = f"weekly-summary-{week_start}-to-{week_end}.md"
    filepath = output_path / filename
    full_content = f"# Weekly Dev Summary — {repo}\n_{week_start} → {week_end}_\n\n{summary}"
    filepath.write_text(full_content, encoding="utf-8")
    print(f"✅ Markdown saved to: {filepath}")
    return str(filepath)


def post_to_slack(summary: str, repo: str, week_start: str, week_end: str, webhook_url: str) -> bool:
    """Post summary to Slack via webhook."""
    full_summary = f"*Weekly Dev Summary — {repo}*\n_{week_start} → {week_end}_\n\n{summary}"
    payload = {"text": full_summary, "mrkdwn": True}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        print("✅ Posted to Slack successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to post to Slack: {e}")
        return False


def post_to_discord(summary: str, repo: str, week_start: str, week_end: str, webhook_url: str) -> bool:
    """Post summary to Discord via webhook (splits into 2000-char chunks if needed)."""
    full_summary = f"**Weekly Dev Summary — {repo}**\n_{week_start} → {week_end}_\n\n{summary}"
    chunks = [full_summary[i:i+2000] for i in range(0, len(full_summary), 2000)]
    success = True
    for chunk in chunks:
        payload = {"content": chunk, "username": "Weekly Dev Summary Bot"}
        try:
            resp = requests.post(webhook_url, json=payload, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to post to Discord: {e}")
            success = False
    if success:
        print("✅ Posted to Discord successfully")
    return success


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Weekly Dev Summary Generator — Python alternative to n8n workflow"
    )
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--language", default="EN", choices=["EN", "FR"], help="Output language")
    parser.add_argument("--slack-url", default=os.getenv("SLACK_WEBHOOK_URL", ""), help="Slack webhook URL")
    parser.add_argument("--discord-url", default=os.getenv("DISCORD_WEBHOOK_URL", ""), help="Discord webhook URL")
    parser.add_argument("--output-dir", default=os.getenv("OUTPUT_DIR", "/tmp/weekly-dev-summary"), help="Output directory")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back")
    args = parser.parse_args()

    github_token = os.getenv("GITHUB_TOKEN")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not github_token:
        print("❌ GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY environment variable is required")
        sys.exit(1)

    # Compute date range
    now = datetime.now(timezone.utc)
    week_end = now.strftime("%Y-%m-%d")
    week_start = (now - timedelta(days=args.days)).strftime("%Y-%m-%d")

    print(f"📊 Fetching data for {args.owner}/{args.repo} ({week_start} → {week_end})...")

    # Fetch data from GitHub
    print("  → Fetching commits...")
    commits = fetch_commits(args.owner, args.repo, week_start, week_end, github_token)
    print(f"    Found {len(commits)} commits")

    print("  → Fetching closed issues...")
    issues = fetch_closed_issues(args.owner, args.repo, week_start, week_end, github_token)
    print(f"    Found {len(issues)} closed issues")

    print("  → Fetching merged PRs...")
    prs = fetch_merged_prs(args.owner, args.repo, week_start, week_end, github_token)
    print(f"    Found {len(prs)} merged PRs")

    # Aggregate data
    data = aggregate_data(args.owner, args.repo, week_start, week_end, args.language, commits, issues, prs)

    # Generate summary via Claude
    print("🤖 Generating summary via Claude API...")
    summary = generate_summary(data, anthropic_key)

    # Save to Markdown file
    save_markdown(summary, f"{args.owner}/{args.repo}", week_start, week_end, args.output_dir)

    # Post to Slack if configured
    if args.slack_url:
        post_to_slack(summary, f"{args.owner}/{args.repo}", week_start, week_end, args.slack_url)
    else:
        print("ℹ️  No Slack webhook configured, skipping Slack notification")

    # Post to Discord if configured
    if args.discord_url:
        post_to_discord(summary, f"{args.owner}/{args.repo}", week_start, week_end, args.discord_url)
    else:
        print("ℹ️  No Discord webhook configured, skipping Discord notification")

    # Print summary to stdout
    print("\n" + "=" * 60)
    print(f"📄 WEEKLY DEV SUMMARY — {args.owner}/{args.repo}")
    print(f"   {week_start} → {week_end}")
    print("=" * 60)
    print(summary)
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
