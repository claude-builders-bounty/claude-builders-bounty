# Weekly Dev Summary — n8n Workflow

Automated weekly narrative summary of GitHub repo activity, powered by Claude API.

## Quick Setup (5 steps)

### 1. Import the workflow
Open your n8n instance → **Workflows** → **Import from File** → select `workflows/weekly-dev-summary.json`

### 2. Configure environment variables
Set these in your n8n environment (`.env` file or Docker env):

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | ✅ | GitHub PAT with repo access |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `GITHUB_REPO` | ✅ | Target repo in `owner/repo` format |
| `LANGUAGE` | ❌ | `EN` (default) or `FR` |
| `SLACK_WEBHOOK_URL` | ❌* | Slack incoming webhook URL |
| `DISCORD_WEBHOOK_URL` | ❌* | Discord webhook URL |
| `EMAIL_FROM` | ❌* | Sender email address |
| `EMAIL_TO` | ❌* | Recipient email address |

*\*At least one delivery channel (Slack/Discord webhook OR email) must be configured.*

### 3. Test manually
Click **Execute Workflow** in n8n to run it once. Verify the summary appears in your chosen delivery channel.

### 4. Activate the workflow
Toggle the workflow to **Active**. It will run every **Friday at 5:00 PM** automatically.

### 5. Verify
Check your Slack/Discord/email after the next Friday 5pm run for the first automated summary.

## How It Works

```
Friday 5pm Cron → Set Config → Fetch GitHub Data → Aggregate & Build Prompt
                                                                  ↓
                    Slack/Discord ← Format ← Claude API ← Generate Summary
                    Email
```

1. **Cron Trigger** — Fires every Friday at 17:00
2. **GitHub API** — Fetches commits, closed issues, and merged PRs from the past 7 days
3. **Data Aggregation** — Merges all data into a structured prompt (supports EN/FR)
4. **Claude API** — Calls `claude-sonnet-4-20250514` to generate a professional narrative
5. **Delivery** — Sends the summary via Slack/Discord webhook and/or email

## Output Example

> **Weekly Dev Summary for owner/repo** (2026-06-05)
>
> This week saw significant progress on the authentication module...

## Requirements

- n8n version 1.0+
- GitHub Personal Access Token with `repo` scope
- Anthropic API key with Claude Sonnet access
- At least one delivery channel configured

## License

MIT
