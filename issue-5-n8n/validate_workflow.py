#!/usr/bin/env python3
"""
Standalone validation script for the n8n weekly-dev-summary workflow.
Run this to verify the workflow logic without needing an n8n instance.

Usage:
  export GITHUB_TOKEN=ghp_xxx
  export GITHUB_REPO=owner/repo
  export ANTHROPIC_API_KEY=sk-ant-xxx
  python3 validate_workflow.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone


def github_get(path, token):
    """Make an authenticated GitHub API request."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "weekly-dev-summary-validator",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  GitHub API error: {e.code} {e.reason}")
        return []


def fetch_commits(repo, token, since):
    """Fetch commits since the given date."""
    since_iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    data = github_get(f"/repos/{repo}/commits?since={since_iso}&per_page=100", token)
    return data if isinstance(data, list) else []


def fetch_closed_issues(repo, token, since):
    """Fetch issues closed since the given date."""
    since_iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    data = github_get(f"/repos/{repo}/issues?state=closed&since={since_iso}&per_page=100", token)
    if isinstance(data, list):
        # Filter out PRs (they appear in issues endpoint too)
        return [i for i in data if "pull_request" not in i]
    return []


def fetch_merged_prs(repo, token):
    """Fetch recently closed PRs (includes merged ones)."""
    data = github_get(f"/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100", token)
    if isinstance(data, list):
        return [p for p in data if p.get("merged_at") is not None]
    return []


def build_prompt(repo, commits, issues, prs, lang="EN"):
    """Build the Claude prompt from fetched data."""
    commit_lines = "\n".join(
        f"- {c['commit']['message'].split(chr(10))[0]} by {c['commit']['author']['name']}"
        for c in commits[:30]
    ) or "No commits this week."

    issue_lines = "\n".join(
        f"- #{i['number']} {i['title']}"
        for i in issues[:20]
    ) or "No closed issues this week."

    pr_lines = "\n".join(
        f"- #{p['number']} {p['title']} by @{p['user']['login']}"
        for p in prs[:20]
    ) or "No merged PRs this week."

    lang_instruction = "Écrivez le résumé en français." if lang == "FR" else "Write the summary in English."

    return f"""Generate a weekly development summary for the GitHub repository {repo}.

## Data

### Commits this week ({len(commits)})
{commit_lines}

### Closed Issues ({len(issues)})
{issue_lines}

### Merged PRs ({len(prs)})
{pr_lines}

## Instructions
{lang_instruction}

Produce a narrative summary with these sections:
1. **Overview** (2-3 sentences about the week's overall activity)
2. **Key Changes** (highlight the most impactful commits and PRs)
3. **Issues Resolved** (summarize the closed issues)
4. **Contributors** (list unique contributors this week)
5. **Looking Ahead** (brief note about ongoing work based on open issues)
"""


def call_claude(prompt, api_key):
    """Call Claude API to generate the summary."""
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        return data["content"][0]["text"]


def main():
    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPO", "claude-builders-bounty/claude-builders-bounty")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    lang = os.environ.get("SUMMARY_LANGUAGE", "EN")

    if not token:
        print("Error: GITHUB_TOKEN environment variable is required")
        sys.exit(1)

    since = datetime.now(timezone.utc) - timedelta(days=7)
    print(f"Fetching data for {repo} since {since.strftime('%Y-%m-%d')}...")

    print("  Fetching commits...")
    commits = fetch_commits(repo, token, since)
    print(f"  Found {len(commits)} commits")

    print("  Fetching closed issues...")
    issues = fetch_closed_issues(repo, token, since)
    print(f"  Found {len(issues)} closed issues")

    print("  Fetching merged PRs...")
    prs = fetch_merged_prs(repo, token)
    print(f"  Found {len(prs)} merged PRs")

    prompt = build_prompt(repo, commits, issues, prs, lang)

    if api_key:
        print("\nGenerating summary via Claude API...")
        summary = call_claude(prompt, api_key)
        print("\n" + "=" * 60)
        print(summary)
        print("=" * 60)
    else:
        print("\nNo ANTHROPIC_API_KEY set. Prompt that would be sent to Claude:")
        print("\n" + "=" * 60)
        print(prompt)
        print("=" * 60)

    # Save output for documentation
    output = {
        "repo": repo,
        "week_of": since.strftime("%Y-%m-%d"),
        "stats": {
            "commits": len(commits),
            "closed_issues": len(issues),
            "merged_prs": len(prs),
        },
    }
    with open("/tmp/weekly-summary-stats.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nStats saved to /tmp/weekly-summary-stats.json")


if __name__ == "__main__":
    main()
