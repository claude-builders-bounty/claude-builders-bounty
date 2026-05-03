# n8n + Claude Weekly Dev Summary

Import `weekly-dev-summary-n8n.json` into n8n to send a weekly narrative summary of a GitHub repository.

## Setup (5 steps)

1. Import `weekly-dev-summary-n8n.json` in n8n.
2. Create credentials: GitHub API, Anthropic header auth (`x-api-key`), and SMTP/email.
3. Set environment variables: `GITHUB_REPO=owner/repo`, `DESTINATION_EMAIL=team@example.com`, `SUMMARY_LANGUAGE=EN` or `FR`.
4. Open the workflow and run **Execute workflow** once to validate the GitHub, Claude, and email nodes.
5. Activate the workflow; it runs every Friday at 17:00.

## What it does

- Weekly cron trigger, Friday 17:00.
- Fetches commits, closed issues, and merged PRs from GitHub API for the last 7 days.
- Calls Anthropic Messages API with `claude-sonnet-4-20250514`.
- Sends the generated narrative via email.
- Supports configurable repo, destination, and language via env vars.

## Test evidence

I validated the exported JSON structure locally with Python and checked that required node names/types, model name, schedule trigger, GitHub fetches, and email delivery node are present. A live n8n screenshot requires an n8n instance with real GitHub/Anthropic/SMTP credentials, so the workflow is designed to import without editing secrets into the file.
