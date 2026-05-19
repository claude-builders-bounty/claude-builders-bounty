# Weekly GitHub Summary Workflow (n8n)

This workflow automatically generates a narrative summary of a GitHub repository's activity over the past week using the Claude API and delivers it via a Discord Webhook.

## Features
- **Trigger**: Weekly cron job (Fridays at 5 PM).
- **Data Collection**: Fetches commits, closed issues, and merged PRs from the GitHub API.
- **AI Analysis**: Uses `claude-sonnet-4-20250514` to synthesize activity into a readable narrative.
- **Multilingual**: Supports English and French.
- **Delivery**: Posts the summary to a Discord channel via Webhook.

## Setup Instructions (5 Steps)

1. **Import Workflow**: Open n8n and import the `workflow.json` file.
2. **Configure Credentials**: 
   - Add your **GitHub PAT** (with `repo` scope).
   - Add your **Anthropic API Key**.
3. **Set Variables**: In the "Set Variables" node, update:
   - `REPO_OWNER`: The owner of the repo.
   - `REPO_NAME`: The name of the repo.
   - `LANGUAGE`: `EN` or `FR`.
   - `DISCORD_WEBHOOK_URL`: Your Discord channel webhook.
4. **Test Connection**: Manually trigger the "GitHub Commits" node to ensure your PAT is working.
5. **Enable Workflow**: Toggle the workflow to "Active".

## Configuration Variables
| Variable | Description |
| --- | --- |
| `REPO_OWNER` | GitHub username or organization name. |
| `REPO_NAME` | Repository name. |
| `LANGUAGE` | Language for the summary (`EN` or `FR`). |
| `DISCORD_WEBHOOK_URL` | The URL for Discord/Slack webhook delivery. |
