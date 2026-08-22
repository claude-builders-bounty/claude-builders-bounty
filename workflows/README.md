# Weekly GitHub Dev Summary via n8n + Claude API

Automated n8n workflow that fetches GitHub repository activity every Friday, summarizes progress using `claude-sonnet-4-20250514`, and dispatches the narrative report via Discord/Slack webhook.

## Quick Setup (5 Steps)

1. **Import Workflow:** Open n8n, click **Workflows** → **Import from File**, and select `workflows/weekly_dev_summary.json`.
2. **Set Variables:** In the `Config Variables` node, configure:
   - `GITHUB_REPO`: `your-org/your-repo`
   - `LANGUAGE`: `EN` or `FR`
   - `DISCORD_WEBHOOK_URL`: Your target webhook endpoint.
3. **Add Credentials:** Add a Header Auth credential for GitHub with header `Authorization: Bearer <GITHUB_TOKEN>`.
4. **Set Anthropic API Key:** Provide `ANTHROPIC_API_KEY` in your n8n environment or HTTP node header.
5. **Activate Workflow:** Toggle the workflow to **Active** to start automatic execution every Friday at 5:00 PM.
