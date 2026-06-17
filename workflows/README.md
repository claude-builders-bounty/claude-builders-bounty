# n8n Weekly Dev Summary Workflow

Automatically generates a weekly narrative summary of a GitHub repo's activity using Claude API.

## Setup (5 steps)

1. **Import the workflow** into n8n:
   - Go to n8n → Workflows → Import from File
   - Select `workflows/weekly-dev-summary.json`

2. **Set environment variables**:
   ```
   GITHUB_REPO=owner/repo
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   CLAUDE_API_KEY=sk-ant-...
   ```

3. **Configure language** (optional):
   - Edit the Claude node → change `LANGUAGE` to `EN` or `FR`

4. **Activate the workflow** (toggle in top-right)

5. **Test** with the manual trigger button

## What it does

Every Friday at 5pm:
1. Fetches commits, closed issues, and merged PRs from GitHub API
2. Sends the data to Claude API for narrative summarization
3. Delivers the summary via Discord webhook

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub personal access token (for API)
- Claude API key (from Anthropic)
- Discord webhook URL (for delivery)
