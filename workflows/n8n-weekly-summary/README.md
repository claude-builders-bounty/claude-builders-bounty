# n8n + Claude Code — Automated Weekly Dev Summary

An n8n workflow that generates a weekly narrative summary of GitHub repo activity using the Claude API.

**Bounty:** $200 — https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5

## Features

- **Weekly cron trigger** — Runs every Friday at 5pm
- **GitHub API** — Fetches commits, closed issues, and merged PRs from the past 7 days
- **Claude API** — Generates a narrative Markdown summary via `claude-sonnet-4-20250514`
- **Discord delivery** — Posts the summary as a richly formatted embed
- **Configurable** — Set repo, webhook URL, and language (EN/FR) via workflow variables
- **Graceful empty-state** — Handles repos with no activity in the week

## Quick Setup (5 Steps)

### 1. Import the workflow

Open n8n → **Workflows** → **Add Workflow** → **Import from File** → select `weekly-dev-summary.json`

### 2. Create a GitHub credential

1. Generate a [GitHub PAT](https://github.com/settings/tokens) with `repo` scope
2. In n8n: **Credentials** → **Add Credential** → **GitHub API** → paste your token

### 3. Create an Anthropic credential

1. Get an [Anthropic API key](https://console.anthropic.com/)
2. In n8n: **Credentials** → **Add Credential** → **HTTP Header Auth**
   - Name: `Anthropic API`
   - Header Name: `x-api-key`
   - Header Value: your Anthropic key

### 4. Configure variables

Edit the **Set Variables** node:

| Variable | Description | Default |
|---|---|---|
| `repo` | GitHub repo (`owner/name`) | `owner/repo` |
| `discordWebhook` | Discord webhook URL | *(required)* |
| `language` | Output language | `EN` (or `FR`) |

### 5. Activate

Toggle **Active** on. The workflow runs every Friday at 5pm UTC.

## Manual Test

Click **Execute Workflow** to run immediately. Check your Discord channel for the embed.

## Workflow Diagram

```
Weekly Cron (Fri 5pm)
       │
       ▼
  Set Variables
       │
       ├────► Fetch Commits ────┐
       ├────► Fetch Issues ─────┤
       └────► Fetch PRs ────────┤
                                ▼
                          Aggregate Data
                                │
                                ▼
                          Claude API
                                │
                                ▼
                        Format for Discord
                                │
                                ▼
                         Send to Discord
```

## Delivery Channels

Default: **Discord webhook**. To use email or Slack:

- **Email**: Replace the **Send to Discord** node with n8n's **Email** node (SMTP)
- **Slack**: Replace with the **Slack** node and an incoming webhook
