# GitHub Weekly Dev Summary — n8n Workflow

Automated weekly narrative summary of your GitHub repo's activity, powered by Claude API.

## Setup (5 Steps)

1. **Import the workflow**: In n8n, click **Workflow** → **Import from File** → Select `github-weekly-summary.json`

2. **Set environment variables**:
   ```bash
   GITHUB_OWNER=your-org          # GitHub organization or user
   GITHUB_REPO=your-repo          # Repository name
   ANTHROPIC_API_KEY=sk-xxx       # Claude API key
   DISCORD_WEBHOOK=https://...    # Or SLACK_WEBHOOK
   SLACK_CHANNEL=#dev-updates     # If using Slack
   LANGUAGE=EN                    # EN or FR
   ```

3. **Configure credentials**: In n8n, add your Anthropic API credential and Discord/Slack credential

4. **Activate the workflow**: Toggle the workflow to **Active** in n8n

5. **Test**: Click **Execute Workflow** — you'll get your first summary immediately

## How It Works

Every Friday at 5 PM:
- Fetches commits, closed issues, and merged PRs from the past 7 days
- Sends data to Claude Sonnet 4-20250514 for narrative generation
- Delivers the summary via Discord webhook or Slack

## Features

- 🕐 Cron schedule: configurable day/time
- 🌐 Language: EN or FR via environment variable
- 🔗 GitHub API: no token needed for public repos
- 🤖 Claude AI: natural language summaries
- 📤 Dual delivery: Discord + Slack support

## Files

- `github-weekly-summary.json` — Main n8n workflow (importable)
- `README.md` — This file

---
*Created by 01号机 (AI Finance Butler) for claude-builders-bounty*
