# Weekly GitHub Repo Narrative Summary — n8n + Claude

Import `weekly-github-summary.n8n.json` into n8n to generate a weekly narrative summary of a GitHub repository and deliver it to Discord or Slack.

## Setup in 5 steps

1. Import `weekly-github-summary.n8n.json` into n8n.
2. Add GitHub API credentials to the three GitHub HTTP nodes.
3. Set env vars: `GITHUB_REPO=owner/repo`, `SUMMARY_LANGUAGE=EN` or `FR`, `ANTHROPIC_API_KEY=...`, `DESTINATION_WEBHOOK_URL=...`.
4. Run the workflow manually once, then check Discord/Slack receives the generated summary.
5. Activate the workflow; it runs every Friday at 17:00.

## What it does

- Weekly cron trigger.
- Fetches commits, closed issues, and merged PRs from the GitHub API for the last 7 days.
- Calls Claude API model `claude-sonnet-4-20250514`.
- Posts the resulting narrative summary to a Discord or Slack webhook.
- Configurable repo, destination webhook, and summary language.

## Test evidence

I validated the workflow structure by loading the exported JSON and checking all required nodes/connections exist. A successful live n8n execution screenshot should be attached to the PR once run on the target n8n instance with real credentials.
