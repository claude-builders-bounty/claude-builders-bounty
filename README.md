# GitHub Weekly Narrative Summary — n8n Workflow

## Setup (3 steps)

1. Import `github-weekly-summary.workflow.json` into your n8n instance
2. Set environment variables: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`
3. Activate the workflow — it triggers every Friday at 5pm

## What it does

- Fetches commits, closed issues, and merged PRs from the past 7 days
- Calls `claude-sonnet-4-20250514` to generate a narrative summary
- Delivers the summary to Discord via webhook
