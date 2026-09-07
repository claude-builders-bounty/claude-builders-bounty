# Weekly GitHub Dev Summary (n8n + Claude)

Importable n8n workflow that runs **every Friday at 17:00**, pulls the last week of GitHub activity (commits, closed issues, merged PRs), asks **Claude (`claude-sonnet-4-20250514`)** for a narrative summary, and posts it to a **Discord webhook**.

## Setup (5 steps)

1. **Import** `weekly-github-dev-summary.json` into n8n (Workflows → Import from File).
2. **Create Header Auth credential** named like “GitHub Token”: header `Authorization` = `Bearer <YOUR_GH_TOKEN>` (repo read access). Attach it to the three GitHub HTTP nodes if prompted.
3. **Set environment variables** (n8n Settings → Variables / env):
   - `GITHUB_REPO` — e.g. `owner/name`
   - `SUMMARY_LANGUAGE` — `EN` or `FR`
   - `DISCORD_WEBHOOK_URL` — Discord channel webhook
   - `ANTHROPIC_API_KEY` — Anthropic API key
4. **Activate** the workflow (toggle Active). Cron: `0 17 * * 5` (Friday 17:00 server time).
5. **Test** with “Execute workflow” (or temporarily replace the Schedule node with a Manual Trigger). Confirm Discord receives the summary.

## Configurable variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `GITHUB_REPO` | `owner/repo` to summarize | `claude-builders-bounty/claude-builders-bounty` |
| `SUMMARY_LANGUAGE` | `EN` or `FR` narrative | `EN` |
| `DISCORD_WEBHOOK_URL` | Delivery channel | _(required)_ |
| `ANTHROPIC_API_KEY` | Claude Messages API | _(required)_ |

## Delivery choice

**Discord webhook** (documented above). Swap the final HTTP node for Slack Incoming Webhook or an Email Send node if you prefer — payload is plain text in `content`.

## Test evidence

See `TEST.md` for a dry-run / execution checklist and captured run notes. Replace the placeholder screenshot path after you execute once on your n8n instance:

`docs/execution-success.png`
