# Weekly Dev Summary — n8n + Claude API

Automated workflow that generates a narrative weekly summary of your GitHub repo's activity using Claude.

## Setup (5 steps)

1. Import `weekly-dev-summary.json` into n8n
2. Set environment variables:
   - `GITHUB_REPO` — `owner/repo` format (e.g., `vercel/next.js`)
   - `LANGUAGE` — `English` or `French` (default: English)
   - `WEBHOOK_URL` — Discord or Slack webhook URL
3. Add GitHub credential (HTTP Header Auth: `Authorization: Bearer ghp_...`)
4. Add Anthropic credential (HTTP Header Auth: `x-api-key: sk-ant-...` + `anthropic-version: 2023-06-01`)
5. Activate the workflow

## How It Works

1. **Trigger**: Fires every Friday at 5pm (configurable cron)
2. **Fetch**: Gets commits, closed issues, and merged PRs from the last 7 days via GitHub API
3. **Merge**: Combines all data into a structured prompt
4. **Summarize**: Claude (`claude-sonnet-4-20250514`) generates a narrative summary
5. **Deliver**: Posts to Discord/Slack via webhook

## Configurable Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Target repository | `facebook/react` |
| `LANGUAGE` | Summary language | `English`, `French` |
| `WEBHOOK_URL` | Delivery webhook | Discord/Slack URL |

## Output Example

> This week saw 23 commits, 5 issues closed, and 3 PRs merged. The highlight was PR #142 which added...
