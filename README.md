# Weekly GitHub Dev Summary (n8n + Claude)

A complete n8n workflow that automatically generates a weekly narrative
summary of a GitHub repo's activity using the Claude API.

## What it does

Every **Friday at 5pm**, the workflow:

1. **Fetches** the last 7 days of GitHub activity (commits, merged PRs, closed issues)
2. **Formats** a compact digest
3. **Calls** Claude (`claude-sonnet-4-20250514`) to generate a narrative summary
4. **Delivers** the summary via Discord/Slack/Slack-compatible webhook

## Setup (5 steps)

### 1. Import the workflow

In n8n:
- Go to **Workflows** → **Import from File**
- Upload `weekly-github-summary.json`

### 2. Configure credentials

Set these environment variables in your n8n instance:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...         # Get from https://console.anthropic.com/

# Optional (have defaults)
GITHUB_REPO=owner/repo                # default: owner/repo
DESTINATION_WEBHOOK=https://discord.com/api/webhooks/...  # your webhook URL
SUMMARY_LANGUAGE=en                   # en or fr
```

In n8n cloud: Settings → Variables
In self-hosted: add to your `.env` file or set in process env

### 3. Create a webhook destination

Pick one:

**Discord**:
- Server Settings → Integrations → Webhooks → New Webhook
- Copy the webhook URL into `DESTINATION_WEBHOOK`

**Slack** (using incoming webhook app):
- https://api.slack.com/messaging/webhooks
- Copy webhook URL

**Custom**: any HTTP endpoint that accepts JSON POST

### 4. Set the schedule (optional)

Default: Friday 5pm. To change:
- Open the workflow
- Click the "Weekly Trigger (Fri 5pm)" node
- Change the cron expression (5-field cron format)

Examples:
- `0 9 * * 1` = Monday 9am
- `0 17 * * 5` = Friday 5pm (default)
- `0 9 * * 1-5` = weekdays 9am

### 5. Activate

- Toggle the **Active** switch (top right)
- The workflow will run on schedule

## What the output looks like

```markdown
📊 **Weekly Summary (2026-05-30 → 2026-06-05)**

This week the team shipped 23 commits, 5 merged PRs, and closed 8 issues.

**Highlights**:
- PR #13109: Add emoji reactions bounty (merged by @akuraposo)
- PR #13110: Code review bounty (merged by @akuraposo)

**Contributor shoutouts**: @akuraposo, @scottcjn

**Next week**: focus on bounty payouts, agent improvements, and n8n workflow automation.

---
📈 *Stats: 23 commits, 5 PRs, 8 issues*
```

## Tested

- n8n 1.x with default HTTP Request + Code nodes
- Claude API via `claude-sonnet-4-20250514`
- Discord webhook delivery (verified by [screenshot in PR])

## Customization

Edit the **"Format Digest"** Code node to change:
- Commit count limit (default: 50)
- PR limit (default: 30)
- Date format

Edit the **"Call Claude API"** node to change:
- The prompt (default tone: friendly but concise)
- Model (e.g. swap to `claude-opus-4-20250514` for higher quality)
- Max tokens (default: 2000)

## Rate limits

- GitHub API: 60 req/hr unauthenticated, 5000/hr with token (not needed here, 3 reqs/week)
- Claude API: depends on tier; weekly summary is ~5K tokens so very cheap

## Troubleshooting

**"No commits"** — Check the repo is public, or add a `GITHUB_TOKEN` header to the HTTP nodes for private repos.

**"Anthropic 401"** — Verify `ANTHROPIC_API_KEY` is set correctly.

**"Webhook 400"** — Test the URL with curl first. Discord/Slack webhooks expect specific JSON shape; for custom endpoints, the workflow sends `{ text: "..." }`.

## License

MIT — use, modify, and redistribute freely.
