# GitHub Weekly Summary - n8n Workflow

Bounty #212 - $200

## Overview

Automated weekly GitHub development summary powered by n8n + Claude API. Delivers a narrative summary of commits, issues, and PRs to Discord every Friday.

## Features

- ✅ **Weekly cron trigger** - Fridays at 5:00 PM UTC
- ✅ **GitHub API integration** - Fetches commits, closed issues, merged PRs (last 7 days)
- ✅ **Claude AI summarization** - Generates narrative summary using Claude Sonnet
- ✅ **Discord delivery** - Sends formatted embed to Discord webhook
- ✅ **Configurable** - Environment variables for all settings
- ✅ **Multi-language** - Supports EN/FR summaries

## Quick Setup (5 Steps)

### 1. Import Workflow

1. Open n8n
2. Go to **Workflows** → **Import from File**
3. Select `github-weekly-summary.workflow.json`

### 2. Set Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_OWNER` | GitHub org/user | `my-org` |
| `GITHUB_REPO` | Repository name | `my-repo` |
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_xxx` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-xxx` |
| `DISCORD_WEBHOOK_URL` | Discord webhook | `https://discord.com/api/webhooks/...` |
| `LANGUAGE` | Summary language (optional) | `en` or `fr` |

### 3. Configure Credentials

In n8n:
- **GitHub API**: Add your GitHub token
- **Anthropic API**: Add your Claude API key

### 4. Activate Workflow

Toggle the workflow to **Active**

### 5. Test

Click **Execute Workflow** on the Schedule Trigger node to test immediately.

## Expected Output

Discord message example:
```
📊 Weekly GitHub Summary (Mar 22-29, 2026)

This week saw 47 commits across 3 branches, with 12 issues closed and 8 PRs merged. 
Key highlights include the new authentication system deployment and performance 
optimizations to the API layer...
```

## Customization

### Change Schedule

Edit the Schedule Trigger node:
- Default: Every Friday at 5:00 PM UTC
- Cron: `0 17 * * 5`

### Slack Integration

Replace Discord Webhook node with Slack node:
1. Add Slack app to your workspace
2. Create incoming webhook
3. Use Slack node instead of Webhook

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No data fetched | Check GITHUB_TOKEN permissions (repo scope) |
| Claude API error | Verify ANTHROPIC_API_KEY is valid |
| Discord not receiving | Test webhook URL with curl |

## License

MIT - Created for claude-builders-bounty #212
