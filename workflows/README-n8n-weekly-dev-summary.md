# n8n weekly GitHub dev summary

This workflow sends a Friday summary of one GitHub repo to Discord. It looks at the last seven days, pulls commits, closed issues, and merged PRs from the GitHub API, then asks Claude Sonnet 4 to turn that activity into a short team update.

## Setup

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Set these n8n environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, and optionally `GITHUB_TOKEN`.
3. Set `SUMMARY_LANGUAGE` to `EN` or `FR`.
4. Run the workflow once manually to check the Discord post.
5. Activate it. The trigger runs every Friday at 5pm.

## What it does

- Uses a weekly cron trigger.
- Fetches commits, closed issues, and merged PRs for the last seven days.
- Calls `claude-sonnet-4-20250514`.
- Posts the final summary to Discord.
- Keeps repo, destination, and language configurable through environment variables.

## Validation

The workflow JSON was checked locally with Node JSON parsing. A full n8n execution needs live `ANTHROPIC_API_KEY` and `DISCORD_WEBHOOK_URL` values, so those should be added in the target n8n instance before the first manual run.
