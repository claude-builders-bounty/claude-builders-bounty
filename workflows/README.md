# n8n Weekly Dev Summary with Claude AI

An importable [n8n](https://n8n.io) workflow that automatically generates a **narrative weekly dev summary** for any GitHub repository using Claude AI (`claude-sonnet-4-20250514`), then delivers it via **Discord** or **Slack** webhook.

## What it does

1. **Triggers** every Friday at 5 PM (instance timezone)
2. **Fetches** from the GitHub API in parallel: commits, closed issues, and merged pull requests from the past 7 days
3. **Merges** all data and builds a rich prompt for Claude
4. **Calls Claude API** to generate a structured narrative summary with highlights, stats, and contributor breakdown
5. **Delivers** the summary to Discord or Slack via webhook (auto-detected from env vars)

## Setup (5 steps)

### Step 1 — Import the workflow

Open n8n → **Workflows** → **Import from File** → select `n8n-weekly-dev-summary.json`.

### Step 2 — Set environment variables

In n8n, go to **Settings → Variables** (or `.env`) and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_REPO` | ✅ | Target repo as `owner/repo` (e.g. `claude-builders-bounty/claude-builders-bounty`) |
| `GITHUB_TOKEN` | ✅ | GitHub personal access token with repo read access |
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key |
| `DISCORD_WEBHOOK_URL` | ⚠️ | Discord incoming webhook URL (set this OR Slack) |
| `SLACK_WEBHOOK_URL` | ⚠️ | Slack incoming webhook URL (set this OR Discord) |
| `SUMMARY_LANGUAGE` | ❌ | `EN` (default) or `FR` for French summaries |

### Step 3 — Configure the schedule

Open the **"Weekly Friday 5pm Trigger"** node and verify the timezone matches your n8n instance. Adjust `triggerAtDay` / `triggerAtHour` if needed.

### Step 4 — Test manually

Click **Execute Workflow** in n8n. Check that:
- GitHub data is fetched (the Fetch nodes should return arrays of commits/issues/PRs)
- Claude returns a narrative summary (check the "Generate Summary with Claude" output)
- The summary arrives in your Discord channel or Slack workspace

### Step 5 — Activate

Toggle the workflow **Active**. It will now run automatically every Friday at 5 PM.

## Workflow architecture

```
Weekly Friday 5pm Trigger
    └→ Load Configuration (env vars + date range)
        ├→ Fetch Commits (GitHub API)
        ├→ Fetch Closed Issues (GitHub API)
        └→ Fetch Closed Pull Requests (GitHub API)
            └→ Merge GitHub Data
                └→ Build Claude Request (prompt engineering)
                    └→ Generate Summary with Claude (Anthropic API)
                        └→ Build Output Messages (Discord/Slack format)
                            └→ Send to Webhook
```

## Delivery options

### Discord
Uses an [Incoming Webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks). The summary is sent as a formatted message with the repo name, date range, and stats.

### Slack
Uses a [Slack Incoming Webhook](https://api.slack.com/messaging/webhooks). The summary is sent as Block Kit formatted message with header, stats, and full summary text.

Set `DISCORD_WEBHOOK_URL` for Discord delivery, or `SLACK_WEBHOOK_URL` for Slack. The workflow auto-detects which one to use.

## Language support

Set `SUMMARY_LANGUAGE=FR` for French summaries, or leave it blank / `EN` for English. The prompt sent to Claude adapts to the chosen language while commit messages stay in their original language.

## Validation

```bash
# Verify the JSON is valid and importable
jq empty workflows/n8n-weekly-dev-summary.json
```

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub personal access token (read access to target repo)
- Anthropic API key with Claude API access
- Discord webhook URL **or** Slack webhook URL
