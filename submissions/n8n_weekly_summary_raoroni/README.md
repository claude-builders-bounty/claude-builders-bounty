# Automated Weekly GitHub Dev Summary — n8n + Claude API Workflow

An importable n8n workflow (`weekly_dev_summary_workflow.json`) that runs every Friday at 17:00, fetches the last 7 days of commits, closed issues, and merged PRs from GitHub, generates a narrative engineering summary via `claude-sonnet-4-20250514`, and posts it to your Discord/Slack webhook.

## Setup in 4 Steps

1. **Import Workflow:** In n8n, click **Workflows → Import from File** and select `weekly_dev_summary_workflow.json`.
2. **Set Environment Variables (or edit the `Configurable Variables` node):**
   - `GITHUB_REPO` (e.g. `owner/repository`)
   - `SUMMARY_LANGUAGE` (`EN` or `FR`)
   - `DESTINATION_WEBHOOK_URL` (Discord or Slack incoming webhook URL)
   - `ANTHROPIC_API_KEY` (your API key for `claude-sonnet-4-20250514`)
3. **Test Execution:** Click **Test Workflow** in the n8n canvas to trigger an immediate summary delivery.
4. **Activate:** Toggle the workflow status to **Active** in the top-right corner so the Friday 17:00 cron (`0 17 * * 5`) runs automatically.

