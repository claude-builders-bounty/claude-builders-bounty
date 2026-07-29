# n8n + Claude Code: Weekly Dev Summary

This workflow fetches the last 7 days of closed issues/PRs from a GitHub repository, summarizes the activity into a narrative using Anthropic's Claude 3.5 Sonnet, and posts the summary to a Discord webhook channel. It runs automatically every Friday at 5 PM.

## Setup Instructions (5 steps)

1. **Import Workflow**: Open your n8n instance, click "Add Workflow", then select "Import from File" and upload `weekly-dev-summary.json`.
2. **Set Environment Variables**: Ensure your n8n environment variables include `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `SUMMARY_LANGUAGE` (e.g., `EN` or `FR`), `DISCORD_WEBHOOK_URL`, and `ANTHROPIC_API_KEY`.
3. **Configure GitHub Auth**: Open the "GitHub (Get Activity)" node and set up or select your GitHub OAuth2 credentials.
4. **Test the Workflow**: Click "Test Workflow" to run a manual execution and verify that a summary is posted to your Discord channel.
5. **Activate**: Toggle the workflow switch to "Active" in the top right corner so the cron schedule (Fridays at 5 PM) takes effect.

*Tested successfully on n8n v1.30.0.*