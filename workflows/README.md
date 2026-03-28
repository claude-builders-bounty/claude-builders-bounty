# Weekly Dev Summary — n8n + Claude

n8n workflow that generates a weekly narrative summary of GitHub repo activity using the Claude API and delivers it via Discord/Slack webhook.

## What it does

Every Friday at 5pm:
1. Fetches commits, merged PRs, and closed issues from the last 7 days
2. Sends the activity data to Claude for a narrative summary
3. Posts the summary to a Discord or Slack channel via webhook

## Setup (5 steps)

1. Open n8n and import `weekly-dev-summary.json` via **Workflows → Import from File**

2. Set these environment variables in n8n (**Settings → Environment Variables**):

   | Variable | Example |
   |----------|---------|
   | `GITHUB_REPO` | `vercel/next.js` |
   | `GITHUB_TOKEN` | `ghp_xxxxxxxxxxxx` |
   | `ANTHROPIC_API_KEY` | `sk-ant-xxxxxxxxxxxx` |
   | `WEBHOOK_URL` | `https://discord.com/api/webhooks/...` |
   | `SUMMARY_LANGUAGE` | `EN` (or `FR`) |

3. Create a GitHub token at github.com/settings/tokens with `repo` scope

4. Create an Anthropic API key at console.anthropic.com

5. Activate the workflow — it runs every Friday at 5pm, or click **Execute Workflow** to test now

## Workflow Nodes

```
Schedule (Fri 5pm) → Config → [Commits, PRs, Issues] → Prepare Data → Claude API → Webhook
```

- **Config**: reads env vars, calculates 7-day lookback date
- **Get Commits/PRs/Issues**: parallel GitHub API calls
- **Prepare Data**: formats activity into a text summary for Claude
- **Claude Summary**: calls `claude-sonnet-4-20250514` for narrative generation
- **Send to Webhook**: posts to Discord/Slack

## Webhook Format

Works with Discord and Slack webhooks. The payload uses `content` field (Discord) — for Slack, change `content` to `text` in the final node.

## Customization

- **Schedule**: edit the Weekly Trigger node to change day/time
- **Language**: set `SUMMARY_LANGUAGE` to `FR` for French summaries
- **Delivery**: replace the webhook node with an email node (SMTP) if preferred
