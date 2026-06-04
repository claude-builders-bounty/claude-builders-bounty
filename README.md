# n8n Weekly Dev Summary

Generates a weekly dev summary using Claude + n8n.

## Setup
1. Import weekly-summary.json into n8n
2. Set GitHub credentials (token)
3. Set Anthropic API key (HTTP Header Auth, header: x-api-key)
4. Set Slack webhook channel
5. Configure owner/repo in GitHub nodes

## How it works
- Cron: Friday 5pm
- Fetches commits + merged PRs (7 days)
- Claude generates summary
- Delivered to Slack

## Configuration
Edit nodes: Cron Trigger (schedule), GitHub nodes (owner/repo), Claude (model), Slack (channel)
