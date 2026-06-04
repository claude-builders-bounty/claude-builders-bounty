# Weekly Dev Summary — n8n Workflow

Automatically generates a narrative summary of your GitHub repo's weekly activity using Claude, and delivers it to Slack.

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub API token (public repo access: no token needed; private repos: `repo` scope)
- Anthropic API key (`claude-sonnet-4-20250514` access)
- Slack webhook URL (create in Slack: Apps → Incoming Webhooks)

## Setup (5 steps)

1. **Import the workflow** — In n8n, go to **Workflows → Add → Import from File** and select `weekly-dev-summary.json`.

2. **Set environment variables** — In n8n's **Settings → Environment Variables**, add:
   - `REPO` — GitHub repo (`owner/repo`, e.g. `my-org/my-project`)
   - `GITHUB_TOKEN` — GitHub personal access token (optional for public repos)
   - `CLAUDE_API_KEY` — Anthropic API key
   - `SLACK_WEBHOOK` — Slack Incoming Webhook URL
   - `CHANNEL` — Channel name for the message context (default: `#dev-updates`)
   - `LANGUAGE` — `EN` (default) or `FR`

3. **Or configure per-node** — Open the **Configuration** node and set values directly instead of env vars.

4. **Activate** — Toggle the workflow to **Active**. It runs every Friday at 5pm UTC by default.

5. **Test manually** — Click **Execute Workflow** to run immediately and verify the output.

## How It Works

```
Cron (Fri 5pm) → Set Variables → Collect GitHub Activity (Code) → Build Prompt (Code) → Claude API → Extract Summary (Code) → Slack Webhook
```

- Collects commits, closed issues, and merged PRs from the past 7 days.
- Calls `claude-sonnet-4-20250514` with a structured prompt.
- Posts a narrative summary to the configured Slack channel.
