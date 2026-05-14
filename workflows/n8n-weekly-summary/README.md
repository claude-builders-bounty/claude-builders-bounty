# Weekly Dev Summary - n8n + Claude

Automated weekly dev summary using n8n and Claude API.

## Setup

1. Import workflow.json into n8n
2. Add GitHub credentials (PAT with repo scope)
3. Add Anthropic API key as Header Auth (x-api-key)
4. Replace OWNER/REPO in HTTP nodes
5. Activate workflow

## Customization

- Change cron for different schedule
- Add Slack/Email node after Extract
- Adjust Claude prompt for different tone