# n8n Weekly Dev Summary

An importable n8n workflow that sends a weekly narrative summary of a GitHub repository to Discord using Claude Sonnet 4.

## Files

- `weekly-dev-summary.workflow.json` - n8n workflow export
- `sample-discord-payload.json` - example payload produced by the final formatting node

## Setup

1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Open the `Config` node and set `repoOwner`, `repoName`, `destinationWebhookUrl`, and `language` (`EN` or `FR`).
3. Set environment variables on your n8n instance: `ANTHROPIC_API_KEY` and optionally `GITHUB_TOKEN`.
4. Run the workflow manually once, then check the generated Discord message.
5. Activate the workflow; the schedule trigger runs every Friday at 17:00.

## What It Does

The workflow computes the previous seven-day window, fetches GitHub commits, closed issues, and merged pull requests for that period, sends a structured prompt to Claude with `claude-sonnet-4-20250514`, then posts the summary to Discord.

The GitHub token is optional but recommended to avoid unauthenticated API rate limits. The Discord webhook URL stays in the `Config` node so the same workflow can be reused across repositories and destinations.

## Manual Verification

I verified the exported workflow JSON structure with `jq` and kept all configurable values in a single node. A live n8n screenshot is not included in this repository because this environment does not have an authenticated n8n instance, but the workflow is designed to import without credentials beyond the two documented environment variables and the webhook URL.
