# n8n Weekly Developer Summary

Import `weekly-dev-summary.workflow.json` into n8n to send a weekly narrative summary of GitHub repository activity through a Slack webhook.

## Setup

1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Set workflow variables: `githubOwner`, `githubRepo`, `language` (`EN` or `FR`), and `slackWebhookUrl`.
3. Add credentials or headers for `GITHUB_TOKEN` and `ANTHROPIC_API_KEY`.
4. Run the workflow once manually to verify the GitHub and Claude API responses.
5. Activate the workflow; it runs every Friday at 5pm.

## What It Fetches

- Commits from the last 7 days.
- Issues closed during the last 7 days.
- Pull requests merged during the last 7 days.

## Claude Model

The Anthropic request uses `claude-sonnet-4-20250514` and asks for a concise narrative summary in the configured language.

## Delivery

The final message is posted to Slack using the configured incoming webhook URL.
