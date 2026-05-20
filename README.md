# n8n Weekly Dev Summary Workflow

Automated weekly GitHub activity summary powered by Claude AI.

## What it does

Every Friday at 5 PM, this workflow:
1. Fetches the week's commits, closed issues, and merged PRs from your GitHub repo
2. Sends the data to Claude (claude-sonnet-4-20250514) to generate a narrative summary
3. Posts the summary to your Discord or Slack channel via webhook

## Setup (5 steps)

### 1. Import the workflow
In your n8n instance, go to **Workflows → Import from File** and select `n8n-weekly-summary.json`.

### 2. Configure GitHub credentials
Create a **GitHub Repo Config** node (or use n8n's built-in variables):
- `repoUrl`: `https://api.github.com/repos/OWNER/REPO`
- `repoName`: Your repository name (for display)
- `githubToken`: GitHub personal access token with `repo` scope

### 3. Configure Claude API key
In the same config:
- `claudeApiKey`: Your Anthropic API key
- `language`: `EN` for English or `FR` for French

### 4. Set your webhook URL
- `webhookUrl`: Your Discord/Slack incoming webhook URL
  - Discord: `https://discord.com/api/webhooks/...`
  - Slack: `https://hooks.slack.com/services/...`

### 5. Activate the workflow
Toggle the **Active** switch (top-right). The workflow runs every Friday at 5 PM automatically.

## Customization

- **Schedule**: Edit the "Weekly Trigger" node → change cron expression
- **Summary style**: Edit the "Merge GitHub Data" node → modify the prompt in `context`
- **Delivery**: Replace the webhook node with Email/Slack/Discord n8n native nodes

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub repo with activity
- Anthropic API key (Claude access)
- Discord/Slack webhook URL
