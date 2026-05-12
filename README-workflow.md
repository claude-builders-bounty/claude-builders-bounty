# Weekly GitHub Dev Summary n8n Workflow

Automatically generates a narrative weekly summary of GitHub repository activity using Claude API and delivers it to Discord/Slack.

## Setup Instructions

1.  **Import Workflow**: Copy the content of `weekly-summary-workflow.json` and paste it into your n8n canvas.
2.  **GitHub Credentials**: Configure a GitHub Personal Access Token (PAT) in the GitHub nodes.
3.  **Claude API**: Add your Anthropic API key to the "Claude Sonnet" node.
4.  **Set Variables**: Update the "Variables" node with your:
    - `REPO_OWNER`
    - `REPO_NAME`
    - `LANGUAGE` (EN or FR)
    - `DISCORD_WEBHOOK_URL`
5.  **Enable**: Activate the workflow. It will run every Friday at 5pm.

## Acceptance Criteria Met
- [x] Exportable `.json` workflow.
- [x] Weekly cron trigger (Friday 5pm).
- [x] Fetches commits, closed issues, and merged PRs for the week.
- [x] Uses `claude-sonnet-4-20250514`.
- [x] Delivers via Discord webhook.
- [x] Configurable repo, destination, and language.
