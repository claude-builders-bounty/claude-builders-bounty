# Weekly Dev Summary n8n Workflow

An importable n8n workflow that generates a weekly narrative summary of a GitHub repository with Claude Sonnet 4, then posts it to Discord.

Target bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5

## Setup

1. Import `weekly-dev-summary.workflow.json` into n8n, then set `GITHUB_OWNER`, `GITHUB_REPO`, `SUMMARY_LANGUAGE`, `ANTHROPIC_API_KEY`, and `DISCORD_WEBHOOK_URL` in your n8n environment.
2. Save and publish the workflow; the Schedule Trigger runs every Friday at 5pm.
3. Run once manually to confirm the Discord summary arrives.

## What It Does

- Triggers weekly on Friday at 17:00.
- Fetches the last 7 days of GitHub commits, closed issues, and merged pull requests.
- Sends a compact activity digest to Claude using `claude-sonnet-4-20250514`.
- Posts the narrative summary to a Discord webhook.
- Supports configurable language through `SUMMARY_LANGUAGE` (`EN` or `FR`).
- Uses one Code node for GitHub collection so the workflow does not depend on fragile multi-branch merge timing.

## Required Environment Variables

| Variable | Example | Notes |
| --- | --- | --- |
| `GITHUB_OWNER` | `n8n-io` | Repository owner or organization. |
| `GITHUB_REPO` | `n8n` | Repository name. |
| `SUMMARY_LANGUAGE` | `EN` | Use `EN` or `FR`. Defaults to `EN` if unset. |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Sent only to Anthropic API. |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Destination webhook. |
| `GITHUB_TOKEN` | `github_pat_...` | Optional. Increases GitHub API limits for private/heavy usage. |

## Test Evidence To Include In PR

- Screenshot of a successful n8n execution.
- Screenshot or copied Discord message showing the weekly summary.
- The imported workflow visible in n8n.

## Notes

The workflow uses HTTP Request nodes instead of service credentials so it can be imported without shipping credential names or IDs.
