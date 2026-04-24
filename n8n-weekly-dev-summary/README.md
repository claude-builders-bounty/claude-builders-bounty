# 📊 Weekly Dev Summary — n8n + Claude Workflow

An n8n workflow that automatically generates a weekly narrative summary of your GitHub repository's activity using the Claude API (`claude-sonnet-4-20250514`).

## Features

- **Automated weekly trigger** — Runs every Friday at 5 PM (configurable)
- **Full GitHub activity** — Fetches commits, closed issues, and merged PRs from the past 7 days
- **AI-powered narrative** — Claude generates an engaging, structured summary with actionable insights
- **Multi-language** — Supports English (EN) and French (FR)
- **Flexible delivery** — Sends via Discord webhook, Slack webhook, or both
- **Configurable** — All settings via environment variables (no workflow editing needed)

## Setup (5 Steps)

### 1. Import the workflow

Open your n8n instance → **Workflows** → **Import from File** → Select `weekly-dev-summary.json`.

### 2. Set environment variables

Go to **Settings** → **Environment Variables** and add:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITHUB_REPO` | ✅ | Target repo (owner/name) | `vercel/next.js` |
| `GITHUB_TOKEN` | ✅ | GitHub PAT with `repo` scope | `ghp_xxxx...` |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key | `sk-ant-xxxx...` |
| `DISCORD_WEBHOOK_URL` | ✅* | Discord channel webhook URL | `https://discord.com/api/webhooks/...` |
| `SLACK_WEBHOOK_URL` | ✅* | Slack incoming webhook URL | `https://hooks.slack.com/services/...` |
| `SUMMARY_LANGUAGE` | ❌ | `EN` (default) or `FR` | `FR` |

\* At least one of Discord or Slack webhook is required.

### 3. Create your webhook

**Discord:** Server Settings → Integrations → Webhooks → New Webhook → Copy URL  
**Slack:** [Create an Incoming Webhook](https://api.slack.com/messaging/webhooks) → Copy URL

### 4. Test the workflow

Click **Execute Workflow** manually to verify everything works. You should see:
- GitHub data fetched (3 parallel HTTP requests)
- Data aggregated into a structured payload
- Claude generates a narrative summary
- Summary posted to your channel

### 5. Activate

Toggle the workflow **Active** switch. It will now run automatically every Friday at 5 PM.

## Workflow Architecture

```
┌─────────────────┐
│  Cron Trigger    │  Every Friday 5PM
│  (Schedule)      │
└────────┬────────┘
         │
┌────────▼────────┐
│  Set Variables   │  Repo, language, date range
└────────┬────────┘
         │
    ┌────┼────┐
    │    │    │         3 parallel GitHub API calls
┌───▼┐ ┌─▼─┐ ┌▼──┐
│ C  │ │ I │ │PR │    Commits / Issues / Pull Requests
└──┬─┘ └─┬─┘ └┬──┘
   └──┬──┘────┘
┌─────▼───────────┐
│  Merge + Code    │  Aggregate into structured text
└────────┬────────┘
         │
┌────────▼────────┐
│  Claude API      │  claude-sonnet-4-20250514
│  (HTTP Request)  │  Generates narrative summary
└────────┬────────┘
         │
┌────────▼────────┐
│  Format Output   │  Add header, stats, emoji
└────────┬────────┘
         │
┌────────▼────────┐
│  Webhook POST    │  Discord / Slack
└─────────────────┘
```

## Sample Output

> 📊 **Weekly Dev Summary — vercel/next.js**  
> 📅 2026-04-17 → 2026-04-24  
> 📈 47 commits · 12 issues closed · 8 PRs merged
>
> ## Overview
> This was a productive week focused on performance improvements and bug fixes...
>
> ## Key Achievements  
> - Shipped the new streaming SSR pipeline (#4521)  
> - Resolved 3 critical memory leak issues  
> ...
>
> ## Suggested Focus for Next Week  
> - Address the 4 remaining P0 bugs in the router...

## Customization

### Change the schedule
Edit the **Weekly Trigger** node → modify the cron expression:
- `0 17 * * 5` = Friday 5 PM
- `0 9 * * 1` = Monday 9 AM
- `0 17 * * 1-5` = Every weekday 5 PM

### Change the AI model
Edit the **Generate Summary (Claude)** node → change `model` in the JSON body.

### Add email delivery
Add an **Send Email** node after **Format Output** using n8n's built-in SMTP node.

### Monitor multiple repos
Duplicate the workflow and change `GITHUB_REPO` per instance, or modify the **Set Variables** node to loop over a list.

## Requirements

- n8n v1.30+ (self-hosted or cloud)
- GitHub Personal Access Token (PAT) with `repo` scope
- Anthropic API key with access to `claude-sonnet-4-20250514`
- Discord or Slack webhook URL

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "401 Unauthorized" from GitHub | Check your `GITHUB_TOKEN` has `repo` scope |
| "401" from Claude API | Verify `ANTHROPIC_API_KEY` is valid |
| No data returned | Ensure the repo had activity in the past 7 days |
| Webhook fails | Verify the webhook URL is correct and the channel exists |
| French output not working | Set `SUMMARY_LANGUAGE` to exactly `FR` (uppercase) |

## License

MIT
