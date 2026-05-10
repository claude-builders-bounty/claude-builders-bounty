# n8n Weekly GitHub Dev Summary

Import `workflows/n8n-weekly-dev-summary.json` into n8n to generate a weekly narrative summary of a GitHub repository's commits, closed issues, and merged pull requests with Claude.

## What It Does

- Runs every Friday at 5pm through the n8n Schedule Trigger.
- Fetches weekly commits, closed issues, and merged pull requests from the GitHub API.
- Sends the activity prompt to Anthropic's Messages API with `claude-sonnet-4-20250514`.
- Posts the generated summary to Slack or Discord through an incoming webhook.
- Supports configurable repository, destination, language, and dry-run validation.

## Setup In 5 Steps

1. Import `workflows/n8n-weekly-dev-summary.json` into n8n.
2. Set environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DESTINATION_WEBHOOK_URL`, `DESTINATION_PROVIDER` (`slack` or `discord`), and `SUMMARY_LANGUAGE` (`EN` or `FR`).
3. Open the workflow and run `Manual Test Trigger` with `N8N_WEEKLY_DRY_RUN=true` to validate wiring without calling external APIs.
4. Set `N8N_WEEKLY_DRY_RUN=false`, run once manually, and confirm the Slack or Discord message arrives.
5. Activate the workflow so the Friday 5pm schedule runs automatically.

## Variables

| Variable | Required | Example | Purpose |
| --- | --- | --- | --- |
| `GITHUB_OWNER` | Yes | `claude-builders-bounty` | Repository owner or organization. |
| `GITHUB_REPO` | Yes | `claude-builders-bounty` | Repository name. |
| `GITHUB_TOKEN` | Recommended | `github_pat_...` | Avoids low unauthenticated GitHub API rate limits. |
| `ANTHROPIC_API_KEY` | Yes | `sk-ant-...` | Calls Claude Messages API. |
| `DESTINATION_WEBHOOK_URL` | Yes | Slack or Discord incoming webhook URL | Receives the weekly summary. |
| `DESTINATION_PROVIDER` | Yes | `slack` | Chooses Slack `{ text }` or Discord `{ content }` payload shape. |
| `SUMMARY_LANGUAGE` | No | `EN` or `FR` | Controls output language. Defaults to English. |
| `N8N_WEEKLY_DRY_RUN` | No | `true` | Uses sample activity and skips external delivery for validation. |

## Validation

This PR includes:

- `scripts/validate-n8n-workflow.mjs`, which checks the workflow JSON, required nodes, Claude model, weekly trigger, and README setup length.
- `sample-outputs/weekly-dev-summary-dry-run.md`, a deterministic dry-run summary shape.
- `evidence/n8n-local-validation.md`, the local validation notes for import readiness and dry-run behavior.

The workflow is production-wired for real GitHub, Claude, and Slack/Discord calls. Dry-run mode exists only to prove n8n wiring without exposing credentials in a public bounty PR.
