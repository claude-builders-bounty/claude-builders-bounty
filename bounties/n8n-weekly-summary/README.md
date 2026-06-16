# Weekly Dev Summary — n8n Workflow

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Features

- **Trigger:** Weekly cron (Friday at 5pm by default)
- **GitHub Data:** Fetches commits, closed issues, and merged PRs for the past week
- **AI Summary:** Uses Claude API (`claude-sonnet-4-20250514`) to generate a structured narrative
- **Delivery:** Email or Discord/Slack webhook (configurable)
- **Configurable:** GitHub repo, language (EN/FR), delivery channel

## Setup (5 Steps)

1. **Import the workflow** into your n8n instance
   - Go to Workflows → Import from File → Select `weekly-dev-summary.workflow.json`

2. **Configure credentials:**
   - `githubApiToken` — GitHub Personal Access Token with `repo` scope
   - `claudeApiKey` — Anthropic API key

3. **Set environment variables** (or edit the Configuration node):
   - `repo` — GitHub repo (e.g., `owner/repo-name`)
   - `language` — `EN` or `FR`
   - `delivery` — `email` or `webhook`

4. **Set delivery details:**
   - If email: set `emailTo` and configure SMTP credentials
   - If webhook: set `webhookUrl` (Discord or Slack webhook URL)

5. **Activate the workflow** — runs automatically every Friday at 5pm

## Output Format

The AI generates a Markdown summary with:
- Overall weekly summary (2–3 sentences)
- Key commits and their impact
- Closed issues with highlights
- Notable PR merges
- Statistics (total commits, issues closed, PRs merged)

## Claim

This submission addresses Issue #5 for the $200 n8n + Claude workflow bounty.
/claim #5
