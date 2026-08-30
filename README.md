# n8n + Claude Code — Automated Weekly Dev Summary

This workflow automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API and delivers it via webhook (Discord/Slack).

## Setup (5 Steps)

1. **Import Workflow**: In your n8n instance, go to Workflows → Import from File → select `n8n_weekly_dev_summary.json`.
2. **Configure Credentials**: Open the workflow and set up two credentials:
   - **GitHub API**: Personal access token with `repo` scope.
   - **Anthropic API**: Your Anthropic API key for Claude access.
3. **Set Variables**: Click the "Weekly Trigger" node or use n8n environment variables to configure:
   - `githubOwner`: Repository owner (e.g., `octocat`)
   - `githubRepo`: Repository name (e.g., `Hello-World`)
   - `webhookUrl`: Discord/Slack incoming webhook URL
   - `language`: `EN` or `FR` (default: `EN`)
4. **Activate**: Toggle the workflow to "Active" in n8n. It will run every Friday at 5 PM UTC.
5. **Test**: Click "Execute Workflow" manually to verify data fetching, summarization, and delivery. Check your webhook channel for the output.

## Acceptance Criteria Met

- ✅ Exportable n8n workflow JSON included
- ✅ Weekly cron trigger (Friday 5 PM)
- ✅ Fetches commits, closed issues, merged PRs via GitHub API
- ✅ Calls `claude-sonnet-4-20250514` for narrative generation
- ✅ Delivers via configurable webhook (Discord/Slack compatible)
- ✅ All variables configurable without editing JSON
- ✅ README with ≤5 step setup

## Payout Address

Solana: `877hj5d4ya4N2B5gPsazm1dudN61Fkjz1V9izhD5m2TU`
