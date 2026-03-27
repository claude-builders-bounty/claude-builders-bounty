# n8n Weekly Dev Summary Workflow

Automated weekly development summary powered by GitHub API and Claude AI. Fetches commits, closed issues, and merged PRs from the past 7 days, generates a narrative summary using Claude (`claude-sonnet-4-20250514`), and delivers it to a Discord channel via webhook.

## Workflow Overview

```
[Cron: Friday 5 PM] -> [Config Variables] -> [GitHub API x3] -> [Merge Data] -> [Claude API] -> [Discord Webhook]
```

**Nodes:**
- **Every Friday 5 PM** -- Schedule trigger (cron), fires weekly
- **Config Variables** -- All configurable settings in one place (repo, language, webhook URL, API keys)
- **Get Commits / Issues / PRs** -- Three parallel GitHub API calls for the last 7 days
- **Merge & Format Data** -- Code node that combines and structures all GitHub data
- **Claude API** -- Sends structured data to Claude to generate a narrative summary
- **Format for Discord** -- Trims output to fit Discord's 2000-char limit
- **Send to Discord** -- Posts the summary via webhook

## Setup (5 steps)

### 1. Import the workflow

Open your n8n instance, go to **Workflows > Import from File**, and select `weekly-dev-summary.json`.

### 2. Set your API keys

In n8n, go to **Settings > Environment Variables** and add:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (starts with `sk-ant-`) |
| `GITHUB_TOKEN` | A GitHub personal access token with `repo` scope |

Alternatively, paste the keys directly into the **Config Variables** node.

### 3. Configure the target repository

Open the **Config Variables** node and edit:

| Field | Default | Description |
|---|---|---|
| `GITHUB_OWNER` | `claude-builders-bounty` | GitHub org or username |
| `GITHUB_REPO` | `claude-builders-bounty` | Repository name |
| `LANGUAGE` | `EN` | Summary language: `EN` (English) or `FR` (French) |

### 4. Set your Discord webhook URL

1. In Discord, go to your channel > **Settings > Integrations > Webhooks > New Webhook**
2. Copy the webhook URL
3. Paste it into the `DISCORD_WEBHOOK_URL` field in the **Config Variables** node

### 5. Activate the workflow

Toggle the workflow to **Active** in the top-right corner. It will run every Friday at 5:00 PM (server timezone). You can also click **Test Workflow** to run it immediately.

## Configuration Reference

All settings are in the **Config Variables** node (second node in the workflow):

| Variable | Required | Description |
|---|---|---|
| `GITHUB_OWNER` | Yes | Repository owner (org or user) |
| `GITHUB_REPO` | Yes | Repository name |
| `LANGUAGE` | Yes | `EN` for English, `FR` for French |
| `DISCORD_WEBHOOK_URL` | Yes | Discord channel webhook URL |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `GITHUB_TOKEN` | Yes | GitHub PAT with `repo` scope |

## Delivery Options

**Discord** (default): The workflow ships with Discord webhook delivery out of the box.

**Slack**: Replace the **Send to Discord** node with an HTTP Request node pointing to your Slack Incoming Webhook URL. The payload format is:
```json
{
  "text": "{{ $json.message }}"
}
```

**Email**: Replace the **Send to Discord** node with n8n's built-in **Send Email** node. Connect your SMTP credentials in n8n and map `{{ $json.message }}` to the email body.

## Requirements

- n8n v1.0+ (self-hosted or cloud)
- Anthropic API key with access to `claude-sonnet-4-20250514`
- GitHub personal access token (PAT) with `repo` read scope
- Discord webhook URL (or Slack/email for alternative delivery)

## License

MIT
