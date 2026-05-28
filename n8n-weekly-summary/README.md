# 📅 Weekly Dev Summary — n8n + Claude

An **n8n workflow** that automatically generates a weekly narrative summary of a GitHub repo's activity using the Claude API, delivered to Discord.

## 📋 Overview

```
┌─────────────┐    ┌────────────┐    ┌───────────────┐
│  Cron Timer  │───▶│  Set Date  │───▶│ Fetch Commits │
│ (Fri 5pm)    │    │  Range     │    │ + Issues + PRs│
└─────────────┘    └────────────┘    └───────┬───────┘
                                            ▼
                                    ┌───────────────┐
                                    │  Merge Data   │
                                    └───────┬───────┘
                                            ▼
                                    ┌───────────────┐
                                    │ Build Prompt  │
                                    └───────┬───────┘
                                            ▼
                                    ┌───────────────┐
                                    │  Claude API   │
                                    │  (sonnet-4)   │
                                    └───────┬───────┘
                                            ▼
                                    ┌───────────────┐
                                    │  Discord/Slack│
                                    │   Webhook     │
                                    └───────────────┘
```

## 🚀 Quick Start (5 steps)

### 1. Import the workflow
- Open n8n → **Workflows** → **Import from File**
- Select `weekly-dev-summary.json`

### 2. Set up environment variables in n8n
| Variable | Description | Where to get |
|----------|-------------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token | https://github.com/settings/tokens |
| `ANTHROPIC_API_KEY` | Claude API key | https://console.anthropic.com |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | Discord channel → Integrations → Webhooks |

### 3. Configure the GitHub repo
Open the **Set Date Range** node and update the `repo` value:
```
owner/repo-name
```

### 4. Activate
Click **Active** toggle on the workflow.

### 5. Test
Click **Execute Workflow** to run immediately. You should receive a summary like this:

```
## Weekly Dev Summary 🚀

**What happened this week:** Shipped user authentication with OAuth
providers. The team focused on cleaning up technical debt in the API layer.

**Bug fixes & maintenance:** Fixed 3 critical bugs in payment processing.

**Looking ahead:** Next week focuses on the dashboard redesign.

**Shout-outs:** Thanks to @alice for the auth implementation!
```

## ⚙️ Configuration

### Trigger
| Setting | Value |
|---------|-------|
| Schedule | Every Friday at 5:00 PM |
| Timezone | Configurable in n8n settings |

### Data Sources
- GitHub Commits API (last 7 days)
- GitHub Issues API (closed this week)
- GitHub Pulls API (merged this week)

### AI Model
- **Model:** `claude-sonnet-4-20250514`
- **Max tokens:** 2,048
- **Prompt:** Narrative style, 3-5 paragraphs

### Delivery
- **Discord webhook** (default)
- **Customizable** — swap the Discord node for Slack, email, or Telegram

## 🧪 Test Output

```
📅 Weekly Dev Summary — 2026-05-22 to 2026-05-28

What happened this week:
The main focus was on the v2 API migration. Major changes include:
- feat: add cursor-based pagination to list endpoints
- feat: implement rate limiting middleware
- refactor: extract validation logic to shared module

Bug fixes & maintenance:
- fix: resolve WebSocket reconnection loop
- fix: correct timezone handling in scheduled tasks
- chore: update dependencies

Looking ahead:
The team is starting work on the notification system, expected to ship next week.

Shout-outs:
Special thanks to @bob for catching the WebSocket regression before it hit production!
```

## 📦 Files

| File | Description |
|------|-------------|
| `weekly-dev-summary.json` | n8n workflow (importable) |
| `README.md` | Setup instructions |
