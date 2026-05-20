# Weekly Dev Summary Workflow — n8n + Claude Code

**Bounty Issue #5 | $200 | claude-builders-bounty**

## Features
- ✅ Weekly cron trigger (configurable, default Friday 5pm)
- ✅ Fetches commits, closed issues, merged PRs via GitHub API
- ✅ Claude API generates narrative summary (3-paragraph format)
- ✅ Delivers via Discord/Slack webhook or Email

## Setup (5 steps)

### Step 1 — Get API keys
- GitHub token: https://github.com/settings/tokens (scope: `repo`)
- Anthropic API key: https://console.anthropic.com/settings/keys
- Discord webhook: Discord channel → Integrations → Webhooks

### Step 2 — Import workflow
1. Open your n8n instance
2. **Workflows** → **Import from JSON**
3. Paste `weekly-dev-summary.json`

### Step 3 — Configure variables
| Variable | Example |
|---|---|
| `GITHUB_REPO` | `anthropic/claude-code` |
| `GITHUB_TOKEN` | `ghp_xxxxxxxxxxxxx` |
| `ANTHROPIC_API_KEY` | `sk-ant-xxxxxxxxxxxxx` |
| `LANGUAGE` | `EN` or `FR` |
| `WEBHOOK_URL` | `https://discord.com/api/webhooks/xxx/xxx` |

### Step 4 — Test
Click **Test Workflow** to trigger manually. Check your Discord/Slack.

### Step 5 — Activate
Toggle workflow **ON**. Runs every Friday 5pm automatically.

## Architecture
```
Schedule (Fri 5pm) → [Fetch Commits + Issues + PRs] → Aggregate → Claude API → Webhook
```

## Sample Output
3-paragraph narrative summary covering:
1. Overall week summary (PRs, commits, issues)
2. Technical highlights and notable changes
3. Infrastructure, fixes, and developer velocity insights

MIT License
