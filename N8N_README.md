# Weekly Dev Summary — n8n + Claude API

Automated weekly narrative summary of GitHub repo activity.

## Install (4 steps)

```bash
# 1. Import workflow: n8n → Import → weekly-dev-summary.json
# 2. Set env vars in n8n:
```

| Variable | Description |
|----------|-------------|
| `GITHUB_REPO` | owner/repo to monitor |
| `GITHUB_TOKEN` | API token (repo scope) |
| `ANTHROPIC_API_KEY` | Claude API key |
| `WEBHOOK_URL` | Slack/Discord webhook URL |
| `LANGUAGE` | `EN` or `FR` |

```bash
# 3. Activate workflow (toggle ON in n8n)
# 4. Test: click "Execute Workflow"
```

## Pipeline

Every Friday 5pm: Fetch commits/issues/PRs → Aggregate stats → Claude generates narrative → Deliver via webhook.

7 nodes: Cron → GitHub(3x) → Aggregate → Claude API → Format → Webhook
