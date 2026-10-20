# n8n + Claude Code (`claude-sonnet-4-20250514`) Automated Weekly Dev Summary (Bounty #5)

## Setup in 4 Steps
1. Open n8n and click **Import from File** → select `workflows/n8n-weekly-dev-summary/workflow.json`.
2. Set environment variables `GITHUB_REPO` (e.g. `owner/repo`), `SUMMARY_LANGUAGE` (`EN` or `FR`), `ANTHROPIC_API_KEY`, and `DESTINATION_WEBHOOK_URL` (Discord or Slack webhook URL).
3. Test-execute the workflow using **Test workflow** in n8n.
4. Toggle **Active** to run every Friday at 17:00 (`0 17 * * 5`).
