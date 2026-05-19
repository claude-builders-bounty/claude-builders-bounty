# Weekly Dev Summary — n8n + Claude API

Automated weekly narrative summary of GitHub repo activity, generated every Friday at 5pm via n8n.

## Installation (4 steps)

```bash
# 1. Import the workflow into n8n
#    n8n → Settings → Import → Select weekly-dev-summary.json

# 2. Configure environment variables in n8n
```

Set these n8n environment/credential variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_REPO` | Owner/repo to summarize | `claude-builders-bounty/claude-builders-bounty` |
| `GITHUB_TOKEN` | GitHub personal access token (repo scope) | `ghp_xxxx` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-xxxx` |
| `WEBHOOK_URL` | Slack/Discord webhook for delivery | `https://hooks.slack.com/...` |
| `LANGUAGE` | Summary language | `EN` or `FR` |

```bash
# 3. Activate the workflow in n8n (toggle ON)

# 4. Test: click "Execute Workflow" in n8n
```

## What it does

```
┌─────────┐    ┌──────────────┐    ┌───────────┐
│ Cron    │───▶│ GitHub API   │───▶│ Aggregate │
│ (Fri 5) │    │ commits/PRs  │    │ + Prompt  │
└─────────┘    └──────────────┘    └─────┬─────┘
                                         │
┌──────────────┐    ┌───────────┐       │
│ Slack/Discord│◀───│ Format    │◀──────┘
│ Webhook      │    │ Summary   │
└──────────────┘    └───────────┘
```

Every Friday at 5pm:
1. Fetches commits, closed issues, and merged PRs from GitHub API
2. Aggregates stats and builds a prompt for Claude
3. Calls Claude API (claude-sonnet-4-20250514) to generate narrative summary
4. Delivers formatted Markdown to Slack/Discord via webhook

## Configurable

- **GitHub repo** — change `GITHUB_REPO` env var
- **Language** — set `LANGUAGE` to `EN` or `FR`
- **Delivery target** — change `WEBHOOK_URL` to any Slack/Discord webhook
- **Schedule** — edit the Cron Trigger node
