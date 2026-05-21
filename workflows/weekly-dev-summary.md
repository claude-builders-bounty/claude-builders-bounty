# Weekly GitHub Dev Summary Workflow

This submission implements issue #5: an importable n8n workflow that runs every Friday at 5pm, collects the past week's GitHub activity, asks Claude Sonnet 4 to write a narrative summary, and posts it to Discord.

## Setup

1. Import `workflows/weekly-dev-summary.workflow.json` into n8n.
2. Set n8n environment variables: `GITHUB_TOKEN` and `ANTHROPIC_API_KEY`.
3. Open the `Configuration` node and set `githubRepo`, `language` (`EN` or `FR`), and `discordWebhookUrl`.
4. Run the workflow manually once and confirm the Discord message is delivered.
5. Activate the workflow so the weekly schedule runs automatically.

## What It Fetches

- Commits from the last 7 days via the GitHub commits API.
- Closed issues from the last 7 days via the GitHub Search API.
- Merged pull requests from the last 7 days via the GitHub Search API.

## Claude Prompting

The workflow uses `claude-sonnet-4-20250514` through Anthropic's Messages API. The prompt asks Claude to produce a stakeholder-friendly narrative summary with these sections:

- Overview
- Highlights
- Merged Pull Requests
- Closed Issues
- Notable Commits
- Next Week Signals

## Delivery

Discord is used as the documented delivery target because a webhook URL can be configured directly in n8n without additional SMTP credentials.

## Test Evidence

Before merge, run the workflow in a real n8n instance using a test repository and attach a screenshot of the successful execution plus the delivered Discord message to the pull request.
