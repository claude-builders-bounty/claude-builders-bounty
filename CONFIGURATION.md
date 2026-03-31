# Configuration Guide

## Environment Variables / n8n Variables

Set these in your n8n instance under **Settings → Variables** or directly in the workflow's variables.

### Required Variables

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Repository in `owner/repo` format | `anthropics/anthropic-sdk-python` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxx` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxxxxxxxxxxx` |
| `DELIVERY_CHANNEL` | Where to send the report: `slack`, `discord`, or `email` | `slack` |

### Conditional Variables (based on DELIVERY_CHANNEL)

| Variable | Required When | Description |
|---|---|---|
| `SLACK_WEBHOOK_URL` | `DELIVERY_CHANNEL=slack` | Slack incoming webhook URL |
| `DISCORD_WEBHOOK_URL` | `DELIVERY_CHANNEL=discord` | Discord webhook URL |
| `EMAIL_TO` | `DELIVERY_CHANNEL=email` | Recipient email address |

### Optional Variables

| Variable | Default | Description |
|---|---|---|
| `LANGUAGE` | `en` | Output language: `en` (English) or `fr` (French) |

## GitHub Token Setup

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `public_repo` (Access public repositories)
4. Copy the token and save it as `GITHUB_TOKEN` in n8n

## Claude API Key Setup

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Navigate to **API Keys**
3. Click **Create Key**
4. Copy the key and save it as `CLAUDE_API_KEY` in n8n

## Slack Webhook Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App → From scratch**
3. Name your app (e.g., "Dev Summary Bot")
4. Select your workspace
5. Go to **Incoming Webhooks** → Toggle ON
6. Click **Add New Webhook to Workspace**
7. Select the target channel
8. Copy the webhook URL → Save as `SLACK_WEBHOOK_URL`

## Discord Webhook Setup

1. Open your Discord server
2. Go to **Server Settings → Integrations → Webhooks**
3. Click **New Webhook**
4. Name it and select the target channel
5. Click **Copy Webhook URL** → Save as `DISCORD_WEBHOOK_URL`

## Email (SMTP) Setup

1. In n8n, go to **Credentials → Add Credential → SMTP**
2. Configure your SMTP settings:
   - Host: `smtp.gmail.com` (for Gmail)
   - Port: `465` (SSL) or `587` (TLS)
   - User: your email
   - Password: app password (not your regular password for Gmail)
3. In the workflow's "Send Email" node, update the `fromEmail` field

## Cron Schedule

The default schedule is **every Friday at 5:00 PM** (cron: `0 17 * * 5`).

To change it, edit the Cron node in the workflow:
- `0 17 * * 5` — Friday 5 PM
- `0 9 * * 1` — Monday 9 AM
- `0 10 * * 1,5` — Monday and Friday 10 AM

## Model Configuration

The workflow uses `claude-sonnet-4-20250514` by default. To change:

1. Open the "Call Claude API" node
2. Edit the JSON body
3. Change `"model"` to your preferred model

Available models:
- `claude-sonnet-4-20250514` (default, balanced)
- `claude-haiku-4-20250514` (faster, cheaper)
- `claude-opus-4-20250514` (most capable)
