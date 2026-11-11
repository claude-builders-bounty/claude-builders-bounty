# Weekly GitHub Narrative Summary Workflow with Claude & n8n

Production-ready, exportable [n8n](https://n8n.io) workflow that schedules a weekly engineering summary from GitHub activity (commits, closed issues, merged PRs) and synthesizes a narrative report using Claude (`claude-sonnet-4-20250514`), delivered via Discord / Slack webhook.

## 5-Step Setup

1. **Import Workflow**: In your n8n workspace, navigate to **Workflows → Import from File** and select `workflows/weekly-github-summary.json`.
2. **Configure Variables**: In node `Set Config Variables`, set:
   - `GITHUB_REPO_OWNER`: e.g. `facebook`
   - `GITHUB_REPO_NAME`: e.g. `react`
   - `SUMMARY_LANGUAGE`: `EN` or `FR`
   - `DESTINATION_WEBHOOK_URL`: Your Discord/Slack incoming webhook URL.
3. **Set GitHub Header Credential**: Add header credential `Authorization: Bearer <GITHUB_TOKEN>` to `Fetch Weekly Commits` and `Fetch Closed Issues`.
4. **Set Anthropic Credential**: In `Call Claude Sonnet 4 API`, add header credential `x-api-key: <ANTHROPIC_API_KEY>`.
5. **Activate Workflow**: Toggle the workflow switch to **Active**. The schedule trigger will fire every Friday at 17:00 UTC (or test manually with **Test Workflow**).
