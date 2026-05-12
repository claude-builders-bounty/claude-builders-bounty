# n8n weekly GitHub dev summary

This workflow generates a weekly narrative summary of a GitHub repository using Claude and posts it to a Slack or Discord webhook.

## Files

- `workflows/n8n-weekly-dev-summary/weekly-dev-summary.json` — importable n8n workflow
- `docs/n8n-weekly-dev-summary/test-run.md` — validation notes and execution evidence

## Setup

1. Import `workflows/n8n-weekly-dev-summary/weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_TOKEN`, `GITHUB_REPO`, `ANTHROPIC_API_KEY`, `DESTINATION_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE` (`EN` or `FR`).
3. Run **Manual test trigger**, then activate the workflow for Friday 17:00 weekly runs.

## Configurable variables

| Variable | Purpose | Example |
|---|---|---|
| `GITHUB_REPO` | Repository to summarize | `owner/repo` |
| `GITHUB_TOKEN` | GitHub API token | `github_pat_...` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `DESTINATION_WEBHOOK_URL` | Slack or Discord webhook URL | `https://hooks.slack.com/...` |
| `SUMMARY_LANGUAGE` | Summary language | `EN` or `FR` |

## What the workflow does

- Weekly trigger: Friday at 17:00
- Fetches GitHub commits from the last 7 days
- Fetches closed issues from the last 7 days
- Fetches merged pull requests from the last 7 days
- Calls Claude model `claude-sonnet-4-20250514`
- Posts a narrative summary to a Slack or Discord webhook

## Output format

The Claude prompt asks for:

- Highlights
- Merged PRs
- Closed Issues
- Commit themes
- Next suggested focus
