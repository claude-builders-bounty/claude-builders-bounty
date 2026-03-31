# Weekly GitHub Activity Summary (n8n + Claude Code)

This workflow automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API (Claude 3.5 Sonnet).

## Features
- **Cron Trigger**: Runs every Friday at 5 PM.
- **Data Aggregation**: Fetches Commits, Closed Issues, and Merged PRs for the past 7 days.
- **AI Summary**: Uses Claude to create a professional narrative of technical progress.
- **Multi-channel**: Supports Discord/Slack webhooks.
- **Configurable**: Easily set Repository, Language (EN/FR), and Notification Channel.

## Setup Instructions (5 Steps)
1. **Import**: Import the `workflow.json` into your n8n instance.
2. **Auth**: Connect your GitHub and Anthropic (Claude) credentials.
3. **Configure**: Update the "Config" node with your `OWNER/REPO`.
4. **Webhook**: Paste your Discord/Slack Webhook URL into the final node.
5. **Activate**: Toggle the workflow to "Active".

---
*Developed by Atlas (via OpenClaw)*
