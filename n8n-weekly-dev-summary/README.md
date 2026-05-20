# n8n Weekly Dev Summary

Importable n8n workflow that fetches weekly GitHub activity, asks Claude to write a narrative summary, and sends it to Discord.

## Setup

1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Set environment variables: `GITHUB_REPO=owner/repo`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, and optional `SUMMARY_LANGUAGE=EN` or `FR`.
3. Open the workflow and run `Manual Test Trigger` once.
4. Publish the workflow so the Friday 17:00 UTC schedule runs automatically.
5. Adjust the workflow timezone if Friday 17:00 should use a local timezone instead of UTC.

## What It Does

- Runs weekly on Friday at 17:00 UTC using n8n's Schedule Trigger.
- Fetches commits, closed issues, and merged PRs for the last 7 days from the GitHub API.
- Calls the Anthropic Messages API with `claude-sonnet-4-20250514`.
- Sends the generated summary to Discord through `DISCORD_WEBHOOK_URL`.
- Supports English and French with `SUMMARY_LANGUAGE=EN` or `SUMMARY_LANGUAGE=FR`.

## Notes

The workflow includes a Manual Trigger so it can be tested before publishing. The Code node throws explicit errors when required environment variables are missing.
