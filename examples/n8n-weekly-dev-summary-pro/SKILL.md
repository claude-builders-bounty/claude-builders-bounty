# Weekly Dev Summary — n8n + Claude Code

Automates a weekly GitHub activity digest using n8n and the Claude API. Runs every Monday at 9 AM, fetches commits and PRs from the past 7 days, and delivers a structured Markdown summary via email or Slack.

## Trigger

- Schedule: Every Monday 09:00 (cron: `0 9 * * 1`)
- Manual: via n8n UI or `node generate.js`

## Setup

1. Import `workflow.json` into your n8n instance
2. Set environment variables:
   - `ANTHROPIC_API_KEY` — your Claude API key
   - `GITHUB_TOKEN` — personal access token (repo scope)
   - `GITHUB_REPO` — target repo e.g. `owner/repo`
   - `NOTIFY_EMAIL` — delivery address (or set Slack webhook)
3. Activate the workflow

## Files

| File | Description |
|------|-------------|
| `workflow.json` | Importable n8n workflow |
| `generate.js` | Standalone Node.js CLI (no n8n required) |
| `README.md` | Full setup and configuration guide |
| `sample-output.md` | Example generated summary |
| `execution-log.md` | Verified test run log |

## Model

Uses `claude-sonnet-4-20250514` via the Anthropic Messages API.

## Example Output

See `sample-output.md` for a real generated weekly summary.
