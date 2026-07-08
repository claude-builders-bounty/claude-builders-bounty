# n8n Weekly Dev Summary

This workflow generates a weekly narrative summary of a GitHub repository using Claude and sends it to Slack.

## Setup

1. Import `n8n-weekly-dev-summary.json` into n8n.
2. Add a GitHub credential for the HTTP Request nodes.
3. Set environment variables: `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE` (`EN` or `FR`).
4. Run the workflow manually once to confirm GitHub and Slack access.
5. Activate the workflow; it runs every Friday at 17:00.

## What It Does

- Fetches commits from the last seven days.
- Fetches closed issues from the last seven days.
- Fetches recently closed pull requests and keeps merged PRs.
- Calls Claude with `claude-sonnet-4-20250514`.
- Sends the generated summary to Slack through a webhook.

## Configurable Variables

- `GITHUB_REPO_OWNER`: repository owner.
- `GITHUB_REPO_NAME`: repository name.
- `SUMMARY_LANGUAGE`: `EN` by default, set to `FR` for French output.
- `ANTHROPIC_API_KEY`: Claude API key.
- `SLACK_WEBHOOK_URL`: Slack incoming webhook URL.

## Validation Notes

The JSON is valid and importable as an n8n workflow export. The workflow keeps delivery to Slack so there is only one required destination credential after GitHub and Anthropic are configured.
