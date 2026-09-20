# n8n + Claude Code Automated Weekly Development Summary

Implements **Opire Bounty #5 ($200 USD)** for `claude-builders-bounty`.

An exportable, turn-key n8n workflow that automatically runs on a Friday schedule, aggregates commits, closed issues, and merged PRs across the week, synthesizes an executive narrative report using the Claude API (`claude-sonnet-4-20250514`), and delivers the markdown report directly to Slack or Discord.

## Features
- **Automated Friday Trigger**: Scheduled cron (`0 17 * * 5` at 5:00 PM).
- **Dual Stream Ingestion**: Fetches both commit history (`/commits?since=...`) and closed issues / pull requests (`/issues?state=closed&since=...`).
- **Prompt Engineering**: Formats data into a structured narrative prompt for Claude.
- **Claude Synthesis**: Invokes Anthropic's Messages API with model `claude-sonnet-4-20250514`.
- **Multi-Channel Dispatch**: Out-of-the-box Slack / Discord webhook delivery.

## Import Instructions
1. In n8n, navigate to **Workflows** -> **Import from File...**
2. Select `workflows/weekly-dev-summary.json`.
3. Set environment variables or node configuration:
   - `GITHUB_OWNER`: Repository owner
   - `GITHUB_REPO`: Repository name
   - `ANTHROPIC_API_KEY`: Your Anthropic API Key
   - `SLACK_WEBHOOK_URL`: Slack Incoming Webhook URL

## Opire Bounty Payout Details
- **Bounty**: #5 ($200 USD)
- **Contributor**: @huyhoang2k5
- **USDC (Base / EVM)**: `0xa57a66df3c7053FDAb5fD1d72040bc0c5b3455F8`
- **PayPal**: `lnhhoang2k5@gmail.com`
