# n8n Weekly Dev Summary — Claude Code Integration

An n8n workflow that generates a weekly narrative summary of GitHub repo activity using the Claude API.

## Features

- **Weekly cron trigger** — runs every Friday at 5 PM (configurable)
- **GitHub data** — fetches commits, closed issues, and merged PRs from the past 7 days
- **Claude narrative** — generates a human-readable weekly summary using `claude-sonnet-4-20250514`
- **Webhook delivery** — sends to Discord, Slack, or any webhook URL
- **Configurable** — language (EN/FR), repo, webhook URL via env vars
- **No-webhook fallback** — outputs summary to the n8n log if no webhook configured

## Installation

```bash
# 1. Import the workflow
# In n8n: Workflows → Add Workflow → Import from File → Select n8n-workflow.json

# 2. Set environment variables in n8n (Settings → Environment Variables):
GITHUB_REPO=owner/repo-name
GITHUB_TOKEN=ghp_your_github_pat
CLAUDE_API_KEY=sk-ant-your_claude_api_key
WEBHOOK_URL=https://discord.com/api/webhooks/... (optional, for Discord/Slack delivery)

# 3. Activate the workflow
# Toggle the workflow to "Active" — it runs every Friday at 5 PM
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_REPO` | Yes | GitHub repo in format `owner/repo` |
| `GITHUB_TOKEN` | Yes | GitHub PAT with `repo` scope |
| `CLAUDE_API_KEY` | Yes | Anthropic API key |
| `WEBHOOK_URL` | No | Discord/Slack webhook URL for delivery |

## How It Works

```
Schedule Trigger (weekly)
  → Fetch Commits (GitHub API, last 7 days)
  → Fetch Closed Issues (GitHub API)
  → Fetch Merged PRs (GitHub API)
  → Build Prompt (formats data into Claude prompt)
  → Claude API (generates narrative summary)
  → Format Output
  → If webhook URL set → Discord/Slack webhook
  → Else → Log to console
```

## Example Output

```
## Weekly Summary - week ending Friday, May 8, 2026

### Highlights
- Released v2.1.0 with major performance improvements
- Fixed critical authentication bug affecting mobile users
- Added support for WebSocket real-time feed

### Commits
- feat: add real-time WebSocket feed (42 commits, 5 contributors)
- fix: correct auth token handling in mobile client
- refactor: extract database layer to separate module
...
```

## Configurable Variables

You can override environment variables per-execution by providing a JSON payload to the trigger node:
```json
{
  "repo": "different-owner/different-repo",
  "webhookUrl": "https://hooks.slack.com/..."",
  "language": "FR"
}
```

## Language Support

Set the `language` variable to `FR` (French) to receive summaries in French. Default is English.
