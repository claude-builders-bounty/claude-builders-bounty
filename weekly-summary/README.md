# n8n Weekly GitHub Summary Workflow

This n8n workflow automates a weekly summary of your GitHub repository's activity. Every Friday at 5 PM, it fetches the week's commits, closed issues, and merged pull requests, asks Claude to generate an engaging narrative summary, and posts it to a Discord channel via webhook.

## Setup in 5 Steps

1. **Import the Workflow**: In your n8n instance, click "Add workflow" -> "Import from File" and select `workflow.json`.
2. **Set GitHub Credentials**: Open any of the "Fetch..." nodes, click to add new credentials for `GitHub Token`, and provide your GitHub Personal Access Token.
3. **Set Anthropic Credentials**: Open the "Claude API" node, click to add new credentials for `Anthropic API`, and provide your Anthropic API Key.
4. **Set Discord Webhook**: Open the "Discord Webhook" node, click to add new credentials for `Discord Webhook URL`, and provide the webhook URL for your target channel.
5. **Activate**: Toggle the workflow switch at the top right from "Inactive" to "Active" to enable the cron schedule!

## Requirements
- n8n instance (Cloud or Self-Hosted)
- GitHub Personal Access Token
- Anthropic API Key
- Discord Webhook URL
