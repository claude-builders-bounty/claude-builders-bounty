# Weekly GitHub Activity Summary (n8n + Claude API)

Automated n8n workflow that fetches weekly commits, closed issues, and merged PRs from GitHub, summarizes them with `claude-sonnet-4-20250514`, and posts the narrative summary to Discord or Slack every Friday at 5:00 PM.

## Setup (5 Steps)

1. Open n8n and choose **Workflows -> Import from File**, then select `weekly-github-claude-summary.json`.
2. Add `ANTHROPIC_API_KEY` to your n8n environment variables.
3. Open **Config Variables (Repo / Channel / EN-FR)** and set `githubRepo`, `destinationWebhook` (Discord or Slack incoming webhook URL), and `language` (`EN` or `FR`).
4. Click **Test workflow** to trigger a manual execution against the target repository.
5. Toggle the workflow **Active** so the Friday 5:00 PM cron schedule runs automatically every week.
