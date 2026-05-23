# Weekly Dev Summary — n8n Workflow

An n8n workflow that automatically generates a weekly development summary from GitHub activity, powered by Claude, and posts it to Discord.

## What It Does

Every **Friday at 5:00 PM**, the workflow:
1. Fetches **commits**, **closed issues**, and **merged PRs** from a GitHub repository for the past week
2. Merges the data and sends it to **Claude (claude-sonnet-4-20250514)** to generate a narrative summary
3. Posts the summary to a **Discord channel** via webhook

## Screenshot

![Successful execution](./execution-screenshot.png)

*(Screenshot placeholder — replace with an actual screenshot after your first successful run.)*

## Setup (5 Steps)

### 1. Import the Workflow

In n8n, go to **Workflows → Import from File** and upload `weekly-dev-summary.json`.

### 2. Set GitHub Credentials

- Create a GitHub Personal Access Token with `repo` read scope.
- In n8n, set the environment variable `GITHUB_TOKEN` with your token (Settings → Environment Variables).
- In the **Set Config Variables** node, update `githubOwner` and `githubRepo` to your target repository (defaults: `claude-builders-bounty` / `claude-builders-bounty`).

### 3. Set Claude API Key

- Get an API key from [Anthropic Console](https://console.anthropic.com/).
- In the **Set Config Variables** node, paste your key into the `claudeApiKey` field.

### 4. Set Discord Webhook URL

- In your Discord server, go to **Channel Settings → Integrations → Webhooks → New Webhook**.
- Copy the webhook URL and paste it into the `discordWebhookUrl` field in the **Set Config Variables** node.

### 5. Activate the Workflow

Click the **Active** toggle in n8n. The workflow will run every Friday at 17:00. You can also click **Execute Workflow** to test it immediately.

## Configurable Variables

All configurable values live in the **Set Config Variables** node:

| Variable | Description | Default |
|---|---|---|
| `githubOwner` | GitHub repository owner | `claude-builders-bounty` |
| `githubRepo` | GitHub repository name | `claude-builders-bounty` |
| `discordWebhookUrl` | Discord webhook URL | *(empty — must set)* |
| `claudeApiKey` | Anthropic API key | *(empty — must set)* |
| `language` | Summary language (`EN` or `FR`) | `EN` |

## Nodes Overview

- **Cron Trigger** — Fires every Friday at 17:00
- **Set Config Variables** — Stores repo, API key, webhook URL, and language preference
- **GitHub Commits API** — `GET /repos/{owner}/{repo}/commits?since={lastWeek}`
- **GitHub Issues API (Closed)** — `GET /repos/{owner}/{repo}/issues?state=closed&since={lastWeek}`
- **GitHub PRs API (Merged)** — `GET /repos/{owner}/{repo}/pulls?state=closed&since={lastWeek}`
- **Merge GitHub Data** — Combines commits, issues, and PRs into a single data object
- **Format Prompt for Claude** — Assembles the merged data into a structured prompt
- **Claude API** — `POST https://api.anthropic.com/v1/messages` with model `claude-sonnet-4-20250514`
- **Discord Webhook** — Posts Claude's summary to your Discord channel
