# Weekly GitHub Dev Summary Workflow

An importable n8n workflow that generates a weekly narrative summary for a GitHub repository using the Claude API.

## What it does
- Runs every Friday at 5pm
- Pulls commits, closed issues, and merged PRs from the last week
- Sends the activity snapshot to Claude (`claude-sonnet-4-20250514`)
- Delivers the generated summary via Discord webhook or email
- Supports configurable repo owner, repo name, and summary language (EN/FR)

## Setup (5 steps)
1. Import `workflow/weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `SUMMARY_LANGUAGE`, `DELIVERY_MODE`.
3. If using Discord, set `DISCORD_WEBHOOK_URL`; if using email, set `EMAIL_FROM` and `EMAIL_TO`.
4. Run the workflow manually once and confirm the generated summary looks correct.
5. Activate the workflow and keep the Friday 5pm schedule or adjust as needed.

## Configurable Variables
- `GITHUB_REPO_OWNER`
- `GITHUB_REPO_NAME`
- `SUMMARY_LANGUAGE` (`EN` or `FR`)
- `DELIVERY_MODE` (`discord` or `email`)

## Notes
- GitHub requests use the REST API and expect a valid token with repo read access.
- The workflow keeps the summary prompt concise so the output stays narrative rather than raw bullet spam.
