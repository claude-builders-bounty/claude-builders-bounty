# 🔄 n8n + Claude — Automated Weekly Dev Summary

A complete n8n workflow that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API, delivered via Discord webhook.

> Bounty submission for [Issue #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

## ⚡ Setup (5 steps)

### 1. Import the workflow
Open your n8n instance → **Workflows** → **Import from File** → select `weekly-dev-summary.workflow.json`

### 2. Set environment variables
In n8n → **Settings** → **Variables**, add:

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub Personal Access Token with `repo` scope |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

### 3. Configure the workflow
Open the **Config** node and update:

| Field | Description | Default |
|-------|-------------|---------|
| `repoOwner` | GitHub org/user | `owner` |
| `repoName` | Repository name | `repo` |
| `destinationWebhookUrl` | Discord webhook URL | `https://discord.com/api/webhooks/REPLACE_ME` |
| `language` | Summary language | `EN` (supports `EN`, `FR`, `VI`, etc.) |

### 4. Test the workflow
Click **Execute Workflow** manually to verify everything works.

### 5. Activate
Toggle the workflow **Active** — it will run automatically every Friday at 5pm.

## 🏗️ Workflow Architecture

```
┌─────────────┐    ┌────────┐    ┌──────────────────┐
│  Weekly      │───▶│ Config │───▶│ Compute Week     │
│  Schedule    │    │        │    │ Range             │
│  (Fri 5pm)  │    │        │    │                   │
└─────────────┘    └────────┘    └────────┬──────────┘
                                          │
                    ┌─────────────────────┬┴──────────────────┐
                    ▼                     ▼                    ▼
             ┌──────────┐         ┌────────────┐      ┌──────────────┐
             │  Get      │         │ Get Closed │      │ Get Merged   │
             │  Commits  │         │ Issues     │      │ Pull Requests│
             └─────┬─────┘        └──────┬─────┘      └──────┬───────┘
                    │                     │                    │
                    └─────────────────────┼────────────────────┘
                                          ▼
                                   ┌──────────────┐
                                   │ Aggregate    │
                                   │ GitHub Data  │
                                   └──────┬───────┘
                                          ▼
                                   ┌──────────────┐
                                   │ Claude API   │
                                   │ (Sonnet 4)   │
                                   └──────┬───────┘
                                          ▼
                                   ┌──────────────┐
                                   │ Discord      │
                                   │ Webhook      │
                                   └──────────────┘
```

## 📋 Features

- **Weekly cron trigger** — Runs every Friday at 5pm (configurable)
- **GitHub API integration** — Fetches commits, closed issues, merged PRs for the past 7 days
- **Claude API (claude-sonnet-4-20250514)** — Generates a narrative summary in natural language
- **Discord delivery** — Sends formatted summary via webhook
- **Configurable language** — `EN`, `FR`, or any language code
- **Configurable repo** — Change target repo in the Config node
- **Error handling** — Graceful fallback if GitHub returns empty data

## 📄 License

MIT
