# Weekly Dev Summary — n8n + Claude Code Workflow

An importable n8n workflow that automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## Setup (5 steps or fewer)

1. **Import the workflow** into your n8n instance:
   ```bash
   # In n8n UI: Workflows → Import from File → select workflows/weekly-dev-summary.json
   ```
2. **Configure environment variables** in n8n:
   - `GITHUB_REPO`: `owner/repo` (e.g., `claude-builders-bounty/claude-builders-bounty`)
   - `GITHUB_TOKEN`: A GitHub Personal Access Token with `repo` scope
   - `ANTHROPIC_API_KEY`: Your Claude API key
   - `DELIVERY_WEBHOOK`: Discord/Slack webhook URL (or email SMTP settings)
   - `SUMMARY_LANGUAGE`: `EN` or `FR` (optional, defaults to `EN`)
3. **Add credentials** in n8n:
   - Create an HTTP Header Auth credential named `GitHub Header` with header `Authorization: token {{ $env.GITHUB_TOKEN }}`
   - Create an HTTP Header Auth credential named `Anthropic Header` with header `x-api-key: {{ $env.ANTHROPIC_API_KEY }}` and `anthropic-version: 2023-06-01`
4. **Activate the workflow** and ensure the Weekly Trigger (Friday 5pm cron) is enabled.
5. **Verify delivery** by manually executing the workflow once and checking your webhook/channel.

## What it does

- **Triggers** every Friday at 5pm (configurable cron).
- **Fetches** commits, closed issues, and merged/closed PRs from the past week via GitHub API.
- **Generates** a 3–5 sentence narrative summary using Claude Sonnet (`claude-sonnet-4-20250514`).
- **Delivers** the summary to your configured Discord/Slack webhook or email endpoint.

## Customization

- Change the cron schedule by editing the `Weekly Trigger` node expression (default: `0 17 * * 5` = Friday 5pm).
- Adjust the Claude prompt inside the `Generate Summary` node to change tone, length, or focus.
- Replace `Deliver via Webhook` with an n8n `Send Email` node if you prefer email delivery.

## Bounty

Bounty #5 — powered by [Opire](https://opire.dev).
