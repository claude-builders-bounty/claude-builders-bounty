# 📊 Weekly GitHub Dev Summary — n8n + Claude AI

> **Bounty #5** — $200 automated weekly dev summary workflow

A complete n8n workflow that automatically generates a weekly narrative summary of your GitHub repository's activity using Claude API, then delivers it via Discord, Slack, or Email.

## ✨ Features

- ⏰ **Weekly cron trigger** — runs every Friday at 5 PM
- 📡 **GitHub API integration** — fetches commits, closed issues, and merged PRs from the past 7 days
- 🤖 **Claude AI summary** — uses `claude-sonnet-4-20250514` to generate a narrative summary
- 📬 **Multi-channel delivery** — Discord webhook, Slack webhook, or Email (SMTP)
- 🌐 **Language support** — configurable EN/FR output
- ⚙️ **Fully configurable** — repo, destination, language all in one config node

## 📋 Setup (5 Steps)

### 1. Import the Workflow

In your n8n instance:
- Go to **Workflows → Import**
- Upload `weekly-github-summary-claude.json`

### 2. Configure Variables

Open the **⚙️ Configuration** node and set:

| Variable | Description | Example |
|----------|-------------|---------|
| `github_repo` | Repository to track | `nousresearch/hermes-agent` |
| `delivery_method` | Where to send | `discord`, `slack`, or `email` |
| `discord_webhook_url` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `slack_webhook_url` | Slack webhook URL | `https://hooks.slack.com/services/...` |
| `email_to` | Recipient email | `team@example.com` |
| `language` | Summary language | `EN` or `FR` |
| `anthropic_api_key` | Your Claude API key | `sk-ant-...` |

### 3. Configure Email (if using email delivery)

Set SMTP credentials in the **📧 Send via Email** node or in n8n's global email settings.

### 4. Test the Workflow

- Click **Execute Workflow** to run manually
- Verify you receive the summary on your chosen channel

### 5. Activate

- Toggle **Active** switch ON
- The workflow will now run every Friday at 5 PM automatically

## 🔄 Workflow Structure

```
⏰ Cron (Fri 5PM)
  ↓
⚙️ Config (repo, channel, lang, API key)
  ↓
📅 Calculate date range (past 7 days)
  ↓
┌────────────┬────────────────┬──────────────┐
│ 📝 Commits  │ 🐛 Issues      │ 🔄 PRs       │
│ GitHub API  │ GitHub API     │ GitHub API   │
└────────────┴────────────────┴──────────────┘
  ↓
🧠 Format data + build Claude prompt
  ↓
🤖 Claude API (claude-sonnet-4-20250514)
  ↓
📄 Extract summary text
  ↓
🚚 Route by delivery_method
  ↓
┌─────────┬─────────┬─────────┐
│ Discord  │ Slack   │ Email   │
└─────────┴─────────┴─────────┘
```

## 📸 Testing

Tested on n8n v1.x. The workflow handles:
- ✅ Empty repos (graceful "No commits/issues/PRs found")
- ✅ Large repos (paginated GitHub API, limits to 100 items per call)
- ✅ API errors (timeout handling, error messages in output)
- ✅ Missing config (fails with clear error in execution log)

## 🔧 Requirements

- **n8n** — self-hosted or n8n Cloud
- **Claude API key** — from [console.anthropic.com](https://console.anthropic.com/)
- **GitHub** — public repos (no token needed for read-only access)
- **Delivery target** — Discord/Slack webhook or SMTP email account

## 📄 License

MIT — same as parent repository.
