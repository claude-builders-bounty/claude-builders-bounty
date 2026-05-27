# n8n Weekly Dev Summary Workflow

Automatically generates a narrative summary of your GitHub repo's weekly activity using Claude API, delivered via Discord/Slack webhook.

## Setup (5 Steps)

1. **Import** — In n8n, go to **Workflows → Import from File** and select `weekly-dev-summary.json`

2. **Create Credentials**
   - **GitHub**: Personal Access Token with `repo` scope
   - **Claude**: API Key from [console.anthropic.com](https://console.anthropic.com)
   - **Webhook URL**: Discord/Slack incoming webhook URL

3. **Configure Variables** — Double-click the **Config Variables** node and set:
   - `repo`: `owner/repo` (the GitHub repo to summarize)
   - `language`: `EN` or `FR`
   - `webhook_url`: Your Discord/Slack webhook URL
   - `delivery_method`: `discord` or `slack`
   
   Alternatively, set these as n8n environment variables: `GITHUB_REPO`, `DISCORD_WEBHOOK_URL`, `SLACK_WEBHOOK_URL`

4. **Activate** — Toggle the workflow **Active** button to enable the weekly cron trigger (Friday at 5PM)

5. **Test** — Click **Execute Workflow** to run a manual test. Check your Discord/Slack channel for the summary.

## Workflow Architecture

- **Parallel Data Fetching**: Commits, merged PRs, and closed issues are fetched concurrently from the GitHub API
- **Claude Sonnet Summary**: All data is merged and sent to `claude-sonnet-4-20250514` for a narrative summary
- **Discord Embed Delivery**: Summary is formatted as a rich Discord embed with color, timestamp, and footer

## Features

- Weekly cron trigger (configurable in Schedule node)
- Supports English and French output
- Discord rich embed with formatted sections (TL;DR, Commits, PRs, Issues, Stats, Looking Ahead)
- Configurable via n8n variables or environment variables
- Error handler node for graceful failure reporting

## Verification

This workflow was tested on a running n8n instance with a sample GitHub repo. The parallel GitHub API fetches return up to 50 commits and 30 PRs/issues. The Claude API generates a structured 6-section narrative summary.
