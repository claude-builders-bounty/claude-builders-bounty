# Weekly Dev Summary Workflow

An n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API.

## Setup (5 steps)

1. **Import the workflow** — In n8n, go to Workflows → Import and upload `workflows/weekly-dev-summary.json`
2. **Configure credentials** — Add HTTP Header Auth credentials for `GitHub Token`, `Anthropic API Key`, and `Slack Webhook`
3. **Set variables** — Edit the Config node to set `githubRepo`, `destinationChannel`, `language` (EN/FR), and your Slack/email webhook URLs
4. **Activate** — Toggle the workflow to active. It runs every Friday at 5pm UTC
5. **Verify** — Check your Slack channel or email for the first weekly summary

## What it does

- Fetches commits, closed issues, and merged PRs from the GitHub API for the past week
- Sends the data to Claude Sonnet 4 for a narrative summary
- Delivers the summary to Slack or email (configurable)

## Files

- `workflows/weekly-dev-summary.json` — Importable n8n workflow
- `README.md` — This file