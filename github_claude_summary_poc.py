#!/usr/bin/env python3
"""
GitHub Weekly Summary POC
Proof-of-concept: Fetch GitHub activity and generate narrative with Claude API
"""

import os
import json
import requests
from datetime import datetime, timedelta
from anthropic import Anthropic

# Initialize clients
github_api_key = os.environ.get('GITHUB_API_KEY')
claude_client = Anthropic()

GITHUB_API_BASE = "https://api.github.com"
REPO_OWNER = "Nireus79"
REPO_NAME = "claude-builders-bounty"


def fetch_github_activity(days=7):
    """Fetch commits, PRs, and issues from the last N days."""

    headers = {
        'Authorization': f'token {github_api_key}',
        'Accept': 'application/vnd.github.v3+json'
    }

    activity = {
        'commits': [],
        'pull_requests': [],
        'issues': []
    }

    # Fetch commits
    print(f"Fetching GitHub activity for {REPO_OWNER}/{REPO_NAME}...")
    commits_url = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    response = requests.get(commits_url, headers=headers)

    if response.status_code == 200:
        commits_data = response.json()
        for commit in commits_data[:20]:  # Last 20 commits
            activity['commits'].append({
                'date': commit['commit']['author']['date'][:10],
                'message': commit['commit']['message'].split('\n')[0],
                'author': commit['commit']['author']['name'],
                'url': commit['html_url']
            })
        print(f"  ✓ Found {len(activity['commits'])} commits")

    return activity


def filter_meaningful_activity(activity):
    """Filter out trivial commits like typos and doc updates."""

    filtered = activity.copy()

    # Filter commits - remove trivial ones
    filtered['commits'] = [
        c for c in activity['commits']
        if not any(trivial in c['message'].lower() for trivial in [
            'typo', 'fix typo', 'update readme', 'update docs',
            'formatting', 'whitespace', 'bump version'
        ])
    ]

    return filtered


def format_for_claude(activity):
    """Format activity data into a readable string for Claude."""

    output = "## GitHub Activity Summary\n\n"

    if activity['commits']:
        output += "### Commits\n"
        for commit in activity['commits']:
            output += f"- **{commit['date']}**: {commit['message']} (by {commit['author']})\n"

    output += f"\nTotal commits: {len(activity['commits'])}\n"

    return output


def generate_narrative_summary(activity_text):
    """Use Claude to generate a narrative summary of the activity."""

    prompt = f"""You are a technical business analyst. Analyze this GitHub activity data and write
a brief executive summary of what was accomplished:

{activity_text}

Write a narrative summary (not a list) with these sections using markdown:

# Weekly Development Summary

## 🎯 Highlights
What were the main achievements this week?

## 🔧 Technical Work
What important technical changes were made?

## 📊 Progress
Overall momentum and direction.

## 🚀 Next Steps
Recommended priorities based on momentum.

Be concise, insightful, and business-focused. Avoid generic statements."""

    print("\nGenerating narrative with Claude API...")

    message = claude_client.messages.create(
        model="claude-opus-4-1-20250805",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def main():
    """Main POC flow."""

    print("=" * 80)
    print("GitHub + Claude Weekly Summary POC")
    print("=" * 80)
    print()

    # Step 1: Fetch GitHub activity
    activity = fetch_github_activity()

    # Step 2: Filter meaningful data
    filtered_activity = filter_meaningful_activity(activity)

    # Step 3: Format for Claude
    formatted = format_for_claude(filtered_activity)
    print("\n" + formatted)

    # Step 4: Generate narrative with Claude
    narrative = generate_narrative_summary(formatted)

    # Step 5: Display result
    print("\n" + "=" * 80)
    print("CLAUDE NARRATIVE SUMMARY")
    print("=" * 80)
    print()
    print(narrative)
    print()

    # Step 6: Save output
    output_file = "github_summary_output.md"
    with open(output_file, 'w') as f:
        f.write("# GitHub Weekly Summary\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(narrative)

    print("=" * 80)
    print(f"✅ Summary saved to {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
