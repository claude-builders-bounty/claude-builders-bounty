# Weekly Dev Summary — n8n + Claude Workflow

> Automated weekly development summary for any GitHub repo, powered by Claude.

## What it does

Every Friday at 5 PM, this workflow:
1. Fetches the week's commits, closed issues, and merged PRs from your GitHub repo
2. Sends them to Claude API to generate a narrative summary
3. Posts the summary to Slack and/or Discord

## Setup (5 steps)

### 1. Start n8n

```bash
npx n8n
# or: docker run -p 5678:5678 n8nio/n8n
```

Open http://localhost:5678

### 2. Import the workflow

- Settings → Import from File → select `weekly-dev-summary.json`
- Or: drag and drop the JSON file into the n8n editor

### 3. Configure variables

Open the **Configuration** node and fill in:

| Variable | Example | Required |
|----------|---------|----------|
| `repo_owner` | `claude-builders-bounty` | ✅ |
| `repo_name` | `claude-builders-bounty` | ✅ |
| `language` | `EN` or `FR` | ✅ |
| `slack_webhook_url` | `https://hooks.slack.com/...` | ❌ |
| `discord_webhook_url` | `https://discord.com/api/webhooks/...` | ❌ |
| `github_token` | `ghp_xxx` | ✅ (for private repos) |
| `anthropic_api_key` | `sk-ant-xxx` | ✅ |

### 4. Set API credentials

In each **HTTP Request** node (Fetch Commits, Issues, PRs):
- Auth → Header Auth → add `Authorization: Bearer {{ $('Configuration').item.json.github_token }}`

In the **Call Claude API** node:
- The `x-api-key` header is already configured to read from Configuration

### 5. Activate

Toggle the workflow to **Active** (top-right switch).

Done! Next Friday at 5 PM, your first summary will arrive.

## Testing

To test immediately instead of waiting for Friday:

1. Open the **Weekly Trigger** node
2. Change cron to `*/2 * * * *` (every 2 minutes)
3. Activate the workflow
4. After the first run, change back to `0 17 * * 5`

Or use **Execute Node** (right-click → Execute) to test individual nodes.

## Customizing the schedule

The cron expression `0 17 * * 5` means "Friday at 5 PM UTC".

| Schedule | Cron |
|----------|------|
| Every Monday 9 AM | `0 9 * * 1` |
| Every weekday 5 PM | `0 17 * * 1-5` |
| Every day 8 AM | `0 8 * * *` |
| First of month | `0 9 1 * *` |

## Output Example

```markdown
📊 Weekly Dev Summary: claude-builders-bounty/claude-builders-bounty
May 19 → May 26 | ⚡ by Claude + n8n

### 📊 Weekly Overview
This was a busy week with 23 commits across 4 contributors. The main
focus was on adding new bounty solutions, with 3 new tools submitted...

### 🚀 Highlights
- New pre-tool-use hook blocks 10 types of destructive bash commands
- CLAUDE.md template now covers full Next.js SaaS stack
- PR review agent now supports GitHub Actions integration

...
---
📝 23 commits · 🔧 5 issues · 🔀 3 PRs merged
```

## Requirements

- n8n (self-hosted or cloud)
- GitHub token (public repos don't need one for reading)
- Anthropic API key (Claude API access)
- Slack or Discord webhook URL (for delivery)
