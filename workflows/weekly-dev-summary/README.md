# Weekly Dev Summary — n8n + Claude Code

An n8n workflow that generates a narrative weekly summary of your GitHub repo's activity using the Claude API, delivered to Slack (or Discord).

## How it works

Every Friday at 5pm, the workflow:
1. Fetches the past 7 days of commits, closed issues, and merged PRs from GitHub
2. Builds a structured prompt with the raw activity
3. Calls Claude (`claude-sonnet-4-20250514`) to write a narrative summary
4. Posts a formatted message to Slack

## Setup

**Step 1: Set environment variables in n8n**

| Variable | Description |
|---|---|
| `GITHUB_REPO` | `owner/repo` (e.g. `vercel/next.js`) |
| `SLACK_WEBHOOK_URL` | Your Slack incoming webhook URL |
| `SUMMARY_LANGUAGE` | `EN` (default) or `FR` |

**Step 2: Set credentials in n8n**

- `GitHub Token` — HTTP Header auth: key `Authorization`, value `token ghp_...`
- `Anthropic API Key` — HTTP Header auth: key `x-api-key`, value `sk-ant-...`

**Step 3: Import and activate**

1. In n8n: **Workflows → Import from file** → select `weekly-dev-summary.json`
2. Set credentials on the GitHub and Claude nodes
3. Set environment variables
4. Toggle workflow **Active**

The workflow runs automatically every Friday at 5pm. Use **Test workflow** to run immediately.

## Output example

```
📊 Weekly Dev Summary — vercel/next.js (April 4, 2026)
April 4, 2026 · 47 commits · 12 PRs · 8 issues closed

This week the Next.js team shipped a significant performance improvement to the
App Router's prefetching behavior, reducing unnecessary network requests by up
to 40% in typical SPAs. The bulk of commits focused on the new partial
prerendering improvements...
```

## Customization

- **Change schedule**: Edit the cron trigger node (`0 17 * * 5` = Fri 5pm UTC)
- **Discord instead of Slack**: Replace the final HTTP Request node with a Discord webhook call; update the format node to output `{"content": "..."}` instead of Slack blocks
- **Email delivery**: Replace the Slack node with n8n's Gmail or SMTP node
