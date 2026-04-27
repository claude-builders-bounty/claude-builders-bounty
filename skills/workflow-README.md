# Weekly Dev Summary — n8n Workflow

Automatically generates a narrative weekly summary of your GitHub repo's activity
using the Claude API, and delivers it via Slack/Discord webhook or email.

## Setup (5 Steps)

### 1. Enable Credentials

Create these credentials in n8n:
- **GitHub**: Personal Access Token with `repo` scope
- **Claude API**: API key from [console.anthropic.com](https://console.anthropic.com)
- **n8n Email**: SMTP credentials (optional, for email delivery)
- **HTTP Header Auth**: For Claude API key header

### 2. Configure Environment Variables

In n8n, set these variables:

| Variable | Example | Purpose |
|----------|---------|---------|
| `GITHUB_OWNER` | `my-org` | Repository owner |
| `GITHUB_REPO` | `my-project` | Repository name |
| `CLAUDE_API_KEY` | `sk-ant-...` | Anthropic API key |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/...` | Delivery channel |
| _OR_ `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Delivery channel |
| `EMAIL_TO` | `team@example.com` | Email fallback |
| `LANGUAGE` | `EN` | Language (EN/FR/ES/JA/ZH) |

### 3. Import Workflow

1. In n8n, go to **Workflows > Add Workflow > Import from File**
2. Select `skills/weekly-dev-summary.workflow.json`
3. Map all credential fields

### 4. Activate

Toggle the workflow to **Active** status.
It will run every Friday at 5 PM by default.

### 5. Verify

After the first scheduled run, check your delivery channel for the summary.

## Customization

- **Schedule**: Edit the Cron Trigger node to change frequency
- **Language**: Set `LANGUAGE=FR` for French, `LANGUAGE=ZH` for Chinese
- **Repo focus**: Change `GITHUB_OWNER`/`GITHUB_REPO` to any repo

## Architecture

```
Cron (Fri 5PM)
  ├─▶ GitHub API: Commits this week
  ├─▶ GitHub API: Closed issues this week
  └─▶ GitHub API: Merged PRs this week
       └─▶ Merge & Format Data
            └─▶ Claude API → Narrative Summary
                 └─▶ Slack / Discord / Email
```
