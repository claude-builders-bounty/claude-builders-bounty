# 🤖 Weekly Dev Summary — n8n + Claude Workflow

> **Bounty #5** — Resolves [Issue #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

A production-ready n8n workflow that generates an automated, AI-written weekly narrative summary of your GitHub repository's development activity and delivers it to Discord or Slack.

---

## 📋 Features

- ⏰ **Automatic trigger** — Runs every Friday at 5 PM (configurable cron)
- 📦 **Fetches 3 data sources** — Commits, closed issues, and merged PRs from the last 7 days
- 🤖 **Claude-powered narrative** — Uses `claude-sonnet-4-20250514` to generate a professional 3-5 paragraph summary
- 📣 **Delivery** — Sends formatted Markdown to Discord or Slack webhook
- 🌍 **Multilingual** — Set `SUMMARY_LANGUAGE` to `EN` (default) or `FR`
- 🔧 **Configurable** — All settings via n8n Variables (no code changes needed)

---

## ⚡ Setup (5 Steps)

### Step 1 — Import the Workflow

1. Open your n8n instance
2. Click **"+"** → **"Import from file"**
3. Select `workflows/weekly-dev-summary.workflow.json`

### Step 2 — Configure n8n Variables

Go to **Settings → Variables** and add:

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Target repository (owner/repo) | `vercel/next.js` |
| `ANTHROPIC_API_KEY` | Your Claude API key | `sk-ant-...` |
| `WEBHOOK_URL` | Discord or Slack webhook URL | `https://discord.com/api/webhooks/...` |
| `SUMMARY_LANGUAGE` | Language: `EN` or `FR` | `EN` |

### Step 3 — Set GitHub Credentials

1. Go to **Credentials** → **New** → **GitHub API**
2. Enter your GitHub Personal Access Token (needs `repo` scope)
3. The workflow's `Fetch Commits`, `Fetch Closed Issues`, and `Fetch Merged PRs` nodes will use this automatically

### Step 4 — Activate the Workflow

Toggle the workflow to **Active** — it will fire automatically every Friday at 5 PM.

### Step 5 — Test Manually (Optional)

Click **"Execute Workflow"** in the editor to run it immediately and verify the output in the final node's output panel.

---

## 🔄 Workflow Architecture

```
[Cron: Fri 5pm]
       │
       ├──► [Fetch Commits (last 7d)]
       ├──► [Fetch Closed Issues (last 7d)]
       └──► [Fetch Merged PRs (last 7d)]
                    │
             [Build Claude Prompt]
                    │
            [Call Claude API]
             (claude-sonnet-4-20250514)
                    │
             [Format Summary]
                    │
          [Send to Discord/Slack Webhook]
```

---

## 📄 Example Output

```
**Weekly Dev Summary — vercel/next.js**

📊 Stats: 47 commits, 12 issues closed, 8 PRs merged

This week saw significant progress across the Next.js project...
[AI narrative continues...]
```

---

## 🛠️ Customization

- **Change schedule**: Edit the cron expression in the `Weekly Cron` node (`0 17 * * 5` = Fri 5pm UTC)
- **Different delivery**: Replace the `Send to Discord/Slack` node with Email, Telegram, or any n8n-supported channel
- **More data**: Add additional GitHub API calls (releases, stars, etc.) before `Build Claude Prompt`
