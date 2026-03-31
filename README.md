# n8n + Claude Code — Automated Weekly Dev Summary

> An n8n workflow that automatically generates a weekly narrative summary of your GitHub repo's activity using the Claude API.

## Features

- 🕐 **Weekly cron trigger** — Runs every Friday at 5:00 PM (configurable)
- 📊 **GitHub data collection** — Fetches commits, closed issues, and merged PRs for the past week
- 🤖 **Claude-powered summaries** — Uses `claude-sonnet-4-20250514` to generate narrative summaries
- 📬 **Multi-channel delivery** — Supports Slack webhook, Discord webhook, and email (SMTP)
- 🌍 **Configurable language** — Supports English (EN) and French (FR) output
- ⚙️ **Easy setup** — 5 steps or fewer to get running

## Prerequisites

1. A running [n8n](https://docs.n8n.io) instance (self-hosted or n8n Cloud)
2. A [Claude API key](https://console.anthropic.com/) (Anthropic)
3. A GitHub Personal Access Token (with `repo` scope)
4. A Slack/Discord webhook URL **or** SMTP email credentials

## Setup (5 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance
2. Go to **Workflows → Import from File**
3. Select `workflow.json` from this repository
4. Click **Import**

### Step 2: Configure Credentials

Create the following credentials in n8n (**Credentials → Add Credential**):

| Credential | Type | Where to get it |
|---|---|---|
| `CLAUDE_API_KEY` | Header Auth | [console.anthropic.com](https://console.anthropic.com/) |
| `GITHUB_TOKEN` | Header Auth | [github.com/settings/tokens](https://github.com/settings/tokens) |
| `SLACK_WEBHOOK_URL` | *(or Discord/SMTP)* | Slack: App settings → Incoming Webhooks |

### Step 3: Set Environment Variables

In the **Settings** node within the workflow, update these variables:

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Target repository (owner/repo) | `anthropics/anthropic-sdk-python` |
| `DELIVERY_CHANNEL` | Delivery method | `slack`, `discord`, or `email` |
| `LANGUAGE` | Output language | `en` or `fr` |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | `https://hooks.slack.com/services/...` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `EMAIL_TO` | Recipient email (if using email) | `team@example.com` |

### Step 4: Test the Workflow

1. Click **Execute Workflow** to run a manual test
2. Check the output node to verify the summary was generated
3. Confirm delivery in your chosen channel

### Step 5: Activate the Workflow

1. Toggle the workflow to **Active**
2. It will now run automatically every Friday at 5:00 PM

## How It Works

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Cron        │───▶│ GitHub API   │───▶│ Claude API  │───▶│   Delivery   │
│  Trigger     │    │ (fetch data) │    │ (summarize) │    │ (Slack/Email)│
│  Fri 5PM     │    │ commits,     │    │ narrative   │    │ webhook or   │
│              │    │ issues, PRs  │    │ summary     │    │ SMTP         │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

### Node Breakdown

1. **Cron Trigger** — Fires every Friday at 17:00
2. **Calculate Date Range** — Computes start (7 days ago) and end (now) dates
3. **Fetch GitHub Commits** — GET `/repos/{owner}/{repo}/commits` (last 7 days)
4. **Fetch GitHub Issues** — GET `/repos/{owner}/{repo}/issues?state=closed` (last 7 days)
5. **Fetch GitHub PRs** — GET `/repos/{owner}/{repo}/pulls?state=closed` (last 7 days)
6. **Build Prompt** — Assembles collected data into a structured prompt for Claude
7. **Call Claude API** — Sends prompt to `claude-sonnet-4-20250514` via Messages API
8. **Format Output** — Parses Claude's response into the final summary
9. **Route Delivery** — Routes to Slack, Discord, or Email based on config
10. **Send** — Delivers the summary via the chosen channel

## Configuration Reference

### GitHub Token Permissions

The GitHub Personal Access Token needs:
- `repo` — Full control of private repositories
- `public_repo` — Access to public repositories (if only public repos)

### Claude API

- Model: `claude-sonnet-4-20250514`
- Max tokens: 2048
- Uses the [Messages API](https://docs.anthropic.com/en/api/messages)

### Slack Webhook Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create a new app → "From scratch"
3. Enable **Incoming Webhooks**
4. Add a webhook to your target channel
5. Copy the webhook URL

### Discord Webhook Setup

1. Open your Discord server → **Server Settings → Integrations → Webhooks**
2. Create a new webhook
3. Copy the webhook URL

### Email (SMTP) Setup

Configure n8n's SMTP credential with your email provider's settings (host, port, user, password).

## Example Output

See [`example-output.md`](example-output.md) for a sample weekly summary.

## File Structure

```
.
├── workflow.json          # n8n workflow (import this)
├── README.md              # This file
├── CONFIGURATION.md       # Detailed configuration guide
├── example-output.md      # Sample weekly report output
└── screenshot.png         # Screenshot of successful execution (add yours)
```

## License

MIT
