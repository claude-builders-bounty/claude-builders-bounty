# Weekly GitHub Activity Summary with Claude

Import `weekly-github-claude-summary.json` into n8n to post a weekly Discord summary of a GitHub repository's commits, closed issues, and merged PRs.

## Setup

1. Import `workflows/weekly-github-claude-summary.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN=ghp_...`, `ANTHROPIC_API_KEY=sk-ant-...`, `DESTINATION_WEBHOOK_URL=https://discord.com/api/webhooks/...`, and optional `SUMMARY_LANGUAGE=EN` or `FR`.
3. Open the workflow, run it once manually, then activate it.
4. Confirm the Discord message appears and keep the default Friday 5pm weekly cron.

## Configuration

- `GITHUB_REPO`: required repository in `owner/repo` form.
- `GITHUB_TOKEN`: optional for public repositories, recommended to avoid rate limits.
- `ANTHROPIC_API_KEY`: required for Claude.
- `ANTHROPIC_BASE_URL`: optional override for test proxies; defaults to `https://api.anthropic.com/v1/messages`.
- `DESTINATION_WEBHOOK_URL`: required Discord webhook URL.
- `SUMMARY_LANGUAGE`: optional, `EN` by default; set `FR` for French.

## What It Does

The workflow runs every Friday at 17:00, fetches the last seven days of GitHub commits, closed issues, and merged pull requests, sends the activity bundle to `claude-sonnet-4-20250514`, and posts the narrative summary to Discord.

## Validation

I validated that the workflow JSON is syntactically valid, all required nodes are connected, the Claude request uses `claude-sonnet-4-20250514`, and required configuration variables are referenced. Full live execution requires real n8n, Anthropic, GitHub, and Discord credentials.
