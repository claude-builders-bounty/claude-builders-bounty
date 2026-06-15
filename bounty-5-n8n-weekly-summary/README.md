# 📊 n8n Weekly Dev Summary — Powered by Claude API

**Bounty**: #5 | **Reward**: $200 | **Category**: Workflow Automation

A complete n8n workflow that automatically generates a narrative weekly development summary using the Claude API.

---

## 🚀 Quick Start (5 Steps)

### 1. Import the Workflow

1. Open your n8n instance (self-hosted or n8n.cloud)
2. Go to **Workflows** → **Import from File**
3. Upload `weekly-dev-summary.json`

### 2. Set Up GitHub Authentication

Create a GitHub Personal Access Token with `repo` scope:

1. Go to [GitHub Settings → Tokens](https://github.com/settings/tokens)
2. Generate a classic token with `repo` scope
3. In n8n, create a **Header Auth** credential:
   - **Name**: `GitHub Weekly Bot`
   - **Headers**: `Authorization: Bearer <your-token>`

Apply this credential to the three GitHub HTTP Request nodes:
- "🔧 GitHub: Get Commits"
- "🔧 GitHub: Get Closed Issues"
- "🔧 GitHub: Get Merged PRs"

### 3. Set Up Claude API Key

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. Create a **Header Auth** credential in n8n:
   - **Name**: `Claude API`
   - **Headers**: `x-api-key: <your-key>`
3. Apply it to the "🤖 Claude API: Generate Summary" node
4. The workflow uses `claude-sonnet-4-20250514` by default

### 4. Configure Variables

Edit the **"⚙️ Configure Variables"** node and fill in:

| Variable | Description | Example |
|----------|-------------|---------|
| `repoOwner` | GitHub org or username | `vercel` |
| `repoName` | Repository name | `next.js` |
| `language` | Output language | `EN` or `FR` |
| `githubToken` | Your GitHub token | `ghp_xxx` |
| `claudeApiKey` | Your Claude API key | `sk-ant-xxx` |
| `deliveryChannel` | Where to send | `slack`, `discord`, or `email` |
| `slackWebhookUrl` | Slack webhook (if using Slack) | `https://hooks.slack.com/...` |
| `discordWebhookUrl` | Discord webhook (if using Discord) | `https://discord.com/api/...` |

### 5. Activate the Workflow

1. Click **Save** in the top-right corner
2. Toggle the **Active** switch to enable weekly cron
3. The cron runs every **Friday at 5:00 PM** (Asia/Shanghai) — adjust in the Schedule Trigger node if needed
4. You can manually test by clicking **Execute Workflow**

---

## 🧠 How It Works

```
Weekly Cron (Fri 5pm)
        │
        ▼
  Calculate Date Range (previous Mon–Sun)
        │
        ▼
  ┌─────┼─────┐
  │     │     │
  ▼     ▼     ▼
Commits Issues PRs
  │     │     │
  └─────┼─────┘
        │
        ▼
  Build Summary Data
        │
        ▼
  Claude API → Narrative Summary
        │
        ▼
  Format & Route
        │
  ┌─────┼─────┐
  │     │     │
  ▼     ▼     ▼
Slack Discord Email
```

### What Claude Generates

- **Executive Summary** — 2–3 sentence overview of the week
- **Key Highlights** — Top 3 achievements
- **Stats at a Glance** — Commits, issues, PRs, lines changed
- **Categorized Changes** — Features, Bug Fixes, Refactoring, Documentation
- **Forward-Looking Note** — What's coming next week

---

## ⚙️ Customization

- **Cron Schedule**: Edit the Schedule Trigger node to change frequency
- **Language**: Set to `FR` for French output (extensible to any language)
- **Delivery**: Choose between Slack, Discord, or Email via the `deliveryChannel` variable
- **GitHub endpoints**: Stats can be extended to include releases, stars, or contributors

---

## ✅ Acceptance Checklist

- [x] Exportable n8n workflow (`weekly-dev-summary.json`)
- [x] Weekly cron trigger (Friday 5pm, configurable)
- [x] Fetches commits, closed issues, and merged PRs via GitHub API
- [x] Calls Claude API (`claude-sonnet-4-20250514`) for narrative summary
- [x] Slack webhook delivery (documented)
- [x] Discord webhook delivery (documented)
- [x] Email (SMTP) delivery (documented)
- [x] Configurable: repo, destination, language (EN/FR)
- [x] Tested on real n8n instance ✅ *(see screenshot below)*
- [x] README with 5-step setup

---

## 📸 Screenshot

*![n8n workflow execution](screenshot.png)*

---

## 📝 Notes

- n8n version used: **1.84+**
- All dependencies are built-in n8n nodes — no custom packages needed
- GitHub API has rate limits: 5,000 requests/hour (authenticated) — more than enough for this workflow
- Claude API costs vary; at ~$0.15 per summary, this is ~$0.60/month for weekly runs
