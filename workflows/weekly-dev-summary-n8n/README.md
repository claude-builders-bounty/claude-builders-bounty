# n8n Weekly Dev Summary Workflow

This bounty deliverable provides an importable n8n workflow that builds a weekly narrative summary for a GitHub repository with Claude.

## Setup

1. Import `weekly-dev-summary.workflow.json` into n8n.
2. Set these n8n environment variables: `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `SUMMARY_LANGUAGE`, and `DISCORD_WEBHOOK_URL`.
3. Open the `Build Weekly Window` node and adjust the fallback values if you do not use environment variables.
4. Enable the workflow; it runs every Friday at 17:00 UTC.
5. Use `Execute workflow` once to verify the Discord message for the target repository.

## What It Fetches

- Commits merged during the previous seven days.
- Closed issues updated during the previous seven days.
- Merged pull requests updated during the previous seven days.

## Configurable Variables

| Variable | Purpose | Example |
| --- | --- | --- |
| `GITHUB_REPO_OWNER` | GitHub owner or organization | `n8n-io` |
| `GITHUB_REPO_NAME` | Repository name | `n8n` |
| `SUMMARY_LANGUAGE` | Output language, `EN` or `FR` | `EN` |
| `DISCORD_WEBHOOK_URL` | Discord incoming webhook URL | `https://discord.com/api/webhooks/...` |
| `GITHUB_TOKEN` | GitHub API token with public repo read access | `ghp_...` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |

## Delivery Choice

The workflow sends the summary to Discord because incoming webhooks are easy to configure and do not require maintaining SMTP credentials inside n8n.

## Test Evidence

See `test-evidence.md` for local JSON validation and the manual n8n execution checklist. A sample generated Discord-ready summary is included in `sample-output.md`.
