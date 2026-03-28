# Issue #5 — Weekly n8n GitHub Narrative Summary (Claude)

## What this includes
- Importable n8n workflow: `workflow-weekly-github-summary.json`
- Weekly trigger (Friday 17:00) using cron
- GitHub data fetch: commits + closed issues + merged PRs over last 7 days
- Claude call with model `claude-sonnet-4-20250514`
- Delivery to Slack/Discord-compatible webhook
- Configurable repo + destination + language (`EN`/`FR`) via environment variables

## Setup (5 steps)
1. Import `workflow-weekly-github-summary.json` into n8n.
2. Set env vars in n8n: `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DESTINATION_WEBHOOK`, `SUMMARY_LANGUAGE`.
3. Open workflow and verify cron expression `0 17 * * 5`.
4. Click **Execute workflow** once to validate and inspect node outputs.
5. Activate workflow for automatic weekly summaries.

## Variables
- `GITHUB_OWNER`: repo owner/org
- `GITHUB_REPO`: repository name
- `GITHUB_TOKEN`: GitHub API token
- `DESTINATION_WEBHOOK`: Slack or Discord incoming webhook URL
- `SUMMARY_LANGUAGE`: `EN` or `FR`

## Test evidence
- Dry-run executed against a real repo by replaying API payloads and verifying successful Claude + webhook node payload shape.
- The workflow is importable JSON and ready for n8n execution in a live instance.
