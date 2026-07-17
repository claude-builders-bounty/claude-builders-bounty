# Weekly Dev Summary — n8n + Claude API

Automatically generate a weekly narrative summary of your GitHub repo's activity using n8n and the Claude API.

## What it does

Every Friday at 5pm, the workflow:
1. Fetches commits, closed issues, and merged PRs from your GitHub repo
2. Sends the data to Claude (`claude-sonnet-4-20250514`) to generate a narrative summary
3. Delivers the summary via **Discord webhook** or **email** (configurable)

## Setup (5 steps)

### Step 1: Prerequisites

- An [n8n](https://n8n.io) instance (self-hosted or cloud)
- A [GitHub personal access token](https://github.com/settings/tokens) (for private repos; public repos work without one)
- An [Anthropic API key](https://console.anthropic.com/)
- A Discord webhook URL **or** an email address for delivery

### Step 2: Import the workflow

1. Open n8n
2. Go to **Workflows → Import from File**
3. Select `weekly-dev-summary.json`

### Step 3: Configure the workflow

Edit the **"Set Configuration"** node with your values:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Repository to monitor | `owner/repo` |
| `GITHUB_TOKEN` | GitHub PAT (optional for public repos) | `ghp_xxx` |
| `CLAUDE_API_KEY` | Anthropic API key | `sk-ant-xxx` |
| `DELIVERY_METHOD` | `discord` or `email` | `discord` |
| `DISCORD_WEBHOOK_URL` | Discord webhook (if using Discord) | `https://discord.com/api/webhooks/...` |
| `EMAIL_TO` | Recipient email (if using email) | `team@example.com` |
| `LANGUAGE` | Summary language: `EN` or `FR` | `EN` |

### Step 4: Activate the workflow

Toggle the workflow to **Active**. It will run automatically every Friday at 5pm (adjust the cron in the trigger node if needed).

### Step 5: Test it

1. In n8n, click **Execute Workflow** to run it manually
2. Check that data is fetched and a summary is delivered to your channel

## Workflow architecture

```
Cron Trigger → Set Config → Fetch GitHub Data → Build Claude Prompt → Call Claude API → Parse Response → [Discord | Email] → Log Success
```

## File structure

```
weekly-dev-summary/
├── weekly-dev-summary.json   # n8n workflow (importable)
└── README.md                 # This file
```

## Customization

- **Schedule**: Change the cron expression in the trigger node (`0 17 * * 5` = Friday 5pm)
- **Language**: Set `LANGUAGE` to `FR` for French summaries
- **Delivery**: Switch between Discord and email by changing `DELIVERY_METHOD`
- **Claude model**: Update the model in the "Call Claude API" node if needed

## License

MIT
