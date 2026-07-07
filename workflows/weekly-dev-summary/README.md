# Weekly Dev Summary — n8n Workflow

Generates a weekly narrative summary of GitHub repo activity using Claude API.

## Setup

1. Install n8n (see [docs.n8n.io](https://docs.n8n.io))
2. Import `workflow.json` → Workflows → New → Import
3. Set these variables in the workflow:
   - **GITHUB_TOKEN** — Personal access token with `repo` scope
   - **CLAUDE_API_KEY** — Anthropic API key
   - **DISCORD_WEBHOOK_URL** — Discord channel webhook (or swap with Slack)

4. Activate the workflow

## Schedule

Defaults to **Friday at 5pm** (configurable in the cron trigger).

## What It Does

1. Fetches commits, closed issues, and merged PRs from the past week
2. Sends them to Claude API (`claude-sonnet-4-20250514`) for summarization
3. Posts a formatted narrative to your Discord channel
