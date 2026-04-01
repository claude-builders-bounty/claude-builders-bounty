# n8n + Claude Code — Weekly Dev Summary

An n8n workflow that automatically generates and delivers a weekly narrative summary of a GitHub repo's activity using Claude API.

## Setup (5 steps)

### 1. Import the workflow
In n8n → **Workflows** → **Import from JSON** → paste `n8n-weekly-dev-summary.json`

### 2. Configure credentials and variables
In n8n → **Variables**, set these workflow variables:

| Variable | Value |
|---|---|
| `GITHUB_REPO` | `owner/repo` (e.g. `anthropic/claude-code`) |
| `GITHUB_TOKEN` | GitHub PAT with `repo` scope |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `DISCORD_WEBHOOK` | Discord webhook URL |
| `LAST_WEEK_DATE` | Auto-set by the aggregate node |
| `LANGUAGE` | `EN` or `FR` |

### 3. Create the GitHub token
Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens) and create a classic token with `repo` scope.

### 4. Create the Discord webhook
In Discord → Channel Settings → Integrations → Webhooks → Create Webhook. Copy the URL.

### 5. Activate the workflow
Click **Activate** in n8n. The workflow runs every Friday at 5pm UTC automatically.

## What it does

1. **Trigger**: Every Friday at 17:00 UTC (configurable in the Schedule node)
2. **Fetch**: Gathers this week's commits, closed issues, and merged PRs via GitHub REST API
3. **Summarize**: Sends the data to Claude API (`claude-sonnet-4-20250514`) with a prompt to generate a narrative summary
4. **Deliver**: Posts the summary to your Discord channel

## Customization

- **Email delivery**: Replace the Discord node with the n8n **Gmail** node
- **Slack delivery**: Replace with the n8n **Slack** node
- **Change schedule**: Edit the **Schedule Trigger** node (e.g. Monday 9am)
- **Language**: Set `LANGUAGE` to `FR` for French output

## Files

- `n8n-weekly-dev-summary.json` — n8n workflow export (import this into n8n)
- `README.md` — this file

## Tested on

- n8n v1.x
- GitHub API v3
- Claude API (Anthropic) 2023-06-01

## Screenshot

> ⚠️ **Manual step**: After importing and configuring, run the workflow once manually and take a screenshot of the successful execution. Attach it to the PR or share in Discord.

## Payment
PayPal: he.zouiten@hotmail.fr
ETH: 0xC64B172b40721D36318CC4D93111d352d019C40A
