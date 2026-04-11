# GitHub Weekly Summary - n8n Workflow

Automated weekly development summary generator using n8n and Claude API.

## Features

- Weekly Schedule: Triggers every Friday at 5:00 PM
- GitHub Integration: Fetches commits, closed issues, and merged PRs
- AI Summary: Uses Claude (claude-sonnet-4-20250514) to generate summaries
- Multi-Channel: Supports Discord, Slack, and Email delivery
- Multi-Language: Supports English (EN) and French (FR)
- Configurable: All settings via environment variables

## Prerequisites

1. **n8n** - Self-hosted or cloud instance
2. **GitHub Personal Access Token** - With repo read permissions
3. **Anthropic API Key** - For Claude access
4. **Discord/Slack Webhook** or **SMTP Email** - For notifications

## Setup (5 Steps)

### Step 1: Import Workflow

1. Open n8n dashboard
2. Click **Workflows** > **Import from File**
3. Select `n8n-workflow/github-weekly-summary.json`

### Step 2: Configure Environment Variables

In n8n Settings > Variables, add:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Repository path | `owner/repo-name` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `GITHUB_TOKEN` | GitHub PAT | `ghp_...` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `EMAIL_RECIPIENT` | Email recipient | `team@example.com` |
| `LANGUAGE` | Summary language | `EN` or `FR` |

### Step 3: Configure HTTP Headers

For GitHub API nodes, add header:
```
Authorization: Bearer {{ $env.GITHUB_TOKEN }}
```

### Step 4: Set Up Notification Channel

**Discord:** Create webhook in channel settings, add URL to env var
**Email:** Configure SMTP in n8n Email node credentials

### Step 5: Activate Workflow

Click **Activate** toggle and test manually

## Workflow Diagram

```
Schedule (Fri 5:00 PM) > Calculate Week Dates > [Commits, Issues, PRs] > Claude API > Discord/Email
```

## License

MIT
