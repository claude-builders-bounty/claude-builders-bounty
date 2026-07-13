# 📊 Weekly Dev Summary — n8n + Claude Automation

> Automatically generate beautiful weekly development summaries for any GitHub repository using Claude AI, delivered to Discord, Slack, or Email.

![Workflow Topology](assets/workflow-diagram.svg)

---

## ✨ Features

- **🤖 AI-Powered Summaries** — Claude claude-sonnet-4-20250514 generates narrative reports, not just data dumps
- **📡 3 Delivery Channels** — Discord webhook, Slack webhook, or Email (SMTP)
- **🌍 Multi-Language** — English, French, or Chinese summaries (`EN` / `FR` / `ZH`)
- **📊 Rich Analytics** — Contributor leaderboard, code change stats, activity scores
- **⚡ Parallel API Calls** — Fetches commits, issues, and PRs simultaneously
- **🛡️ Error Handling** — Graceful fallback with error notification on API failures
- **⚙️ Fully Configurable** — All settings via n8n variables (no code changes needed)
- **📅 Cron Scheduled** — Runs every Friday at 5:00 PM UTC (customizable)

---

## 🚀 5-Step Installation Guide

### Step 1: Import the Workflow

1. Open your n8n instance (self-hosted or n8n.cloud)
2. Go to **Workflows** → **Import from File**
3. Select `weekly-dev-summary.json`
4. The workflow will appear with all 14 nodes pre-configured

### Step 2: Set Up Credentials

Create two **Header Auth** credentials in n8n:

| Credential Name | Header Name | Header Value |
|-----------------|-------------|--------------|
| **GitHub Token** | `Authorization` | `Bearer ghp_YOUR_GITHUB_TOKEN` |
| **Anthropic API Key** | `x-api-key` | `sk-ant-YOUR_ANTHROPIC_KEY` |

**Optional** (for email delivery):
- Create an **SMTP** credential with your email server details

**How to create credentials:**
1. Go to **Settings** → **Credentials** → **Add Credential**
2. Select **Header Auth**
3. Enter the name, header name, and value as shown above
4. Click **Save**

### Step 3: Configure Variables

Go to **Settings** → **Variables** and create:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_OWNER` | Repository owner/org | `anthropics` |
| `GITHUB_REPO` | Repository name | `anthropic-cookbook` |
| `SUMMARY_LANGUAGE` | Report language: `EN`, `FR`, or `ZH` | `EN` |
| `DELIVERY_METHOD` | Channel: `discord`, `slack`, or `email` | `discord` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | `https://hooks.slack.com/services/...` |
| `EMAIL_TO` | Recipient email address | `team@example.com` |
| `EMAIL_FROM` | Sender email address | `noreply@example.com` |

> 💡 Only configure the delivery channel you plan to use.

### Step 4: Test the Workflow

1. Click **Execute Workflow** (▶️ button) to run manually
2. Check each node's output by clicking on it
3. Verify the summary appears in your chosen delivery channel
4. Review the Claude-generated summary for quality

### Step 5: Activate

1. Toggle the **Active** switch to ON (top-right corner)
2. The workflow will now run automatically every Friday at 5:00 PM UTC
3. To change the schedule, edit the **Weekly Schedule** node's cron expression

---

## 🏗️ Workflow Architecture

```
┌──────────────┐    ┌────────────┐    ┌─────────────┐
│  ⏰ Schedule  │───▶│  ⚙️ Config  │───▶│  📅 Dates   │
│  Fri 17:00   │    │  Variables  │    │  7d lookback│
└──────────────┘    └────────────┘    └──────┬──────┘
                                             │
                          ┌──────────────────┼──────────────────┐
                          ▼                  ▼                  ▼
                   ┌────────────┐    ┌─────────────┐    ┌────────────┐
                   │  📝 Commits │    │  🐛 Issues   │    │  🔀 PRs    │
                   │  GitHub API│    │  GitHub API  │    │  GitHub API│
                   └──────┬─────┘    └──────┬──────┘    └──────┬─────┘
                          │                 │                  │
                          └─────────────────┼──────────────────┘
                                            ▼
                                   ┌────────────────┐
                                   │  🔗 Aggregate   │
                                   │  Merge + Stats  │
                                   └───────┬────────┘
                                           ▼
                                   ┌────────────────┐
                                   │  🤖 Claude API  │
                                   │  Generate Report│
                                   └───────┬────────┘
                                           ▼
                                   ┌────────────────┐
                                   │  📤 Extract     │
                                   │  Parse Response │
                                   └───────┬────────┘
                                           ▼
                                   ┌────────────────┐
                                   │  🔀 Router      │
                                   │  Switch Channel │
                                   └──┬─────┬─────┬─┘
                                      ▼     ▼     ▼
                                  Discord Slack  Email
```

### Node Details (14 total)

| # | Node | Type | Purpose |
|---|------|------|---------|
| 1 | Weekly Schedule | `scheduleTrigger` | Cron trigger: `0 17 * * 5` (Fri 5PM) |
| 2 | Set Config | `set` | Load repo, language, delivery from variables |
| 3 | Calculate Dates | `code` | Compute 7-day lookback window |
| 4 | Fetch Commits | `httpRequest` | `GET /repos/{owner}/{repo}/commits?since=...` |
| 5 | Fetch Closed Issues | `httpRequest` | `GET /repos/{owner}/{repo}/issues?state=closed` |
| 6 | Fetch Merged PRs | `httpRequest` | `GET /repos/{owner}/{repo}/pulls?state=closed` |
| 7 | Aggregate Data | `code` | Merge results, compute contributor stats |
| 8 | Claude API | `httpRequest` | POST to Anthropic Messages API |
| 9 | Extract Summary | `code` | Parse Claude response, add header |
| 10 | Delivery Router | `switch` | Route to Discord / Slack / Email |
| 11 | Send to Discord | `httpRequest` | Discord webhook with embed |
| 12 | Send to Slack | `httpRequest` | Slack webhook with blocks |
| 13 | Send Email | `emailSend` | SMTP email delivery |
| 14 | Error Handler | `code` | Fallback error notification |

---

## 🌍 Language Support

Set `SUMMARY_LANGUAGE` variable to change the report language:

| Value | Language | Example Section Header |
|-------|----------|----------------------|
| `EN` | English | "## ⭐ Key Highlights" |
| `FR` | French | "## ⭐ Points Clés" |
| `ZH` | Chinese | "## ⭐ 重点亮点" |

Claude generates the entire report in the chosen language, including section headers, descriptions, and analysis.

---

## 📋 Configuration Reference

### Cron Schedule

Edit the **Weekly Schedule** node to change timing:

| Expression | Schedule |
|-----------|----------|
| `0 17 * * 5` | Friday 5:00 PM (default) |
| `0 9 * * 1` | Monday 9:00 AM |
| `0 12 * * 3,5` | Wed & Fri at noon |
| `0 0 1 * *` | 1st of each month |

### GitHub Token Permissions

The GitHub personal access token needs these scopes:
- `repo` (for private repos) or `public_repo` (for public repos only)

### Claude API Model

The workflow uses `claude-sonnet-4-20250514`. To change the model, edit the **Generate Summary with Claude** node's JSON body and update the `model` field.

---

## 📄 Sample Output

See [sample-output.md](sample-output.md) for a full example of a generated weekly summary.

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| GitHub API 401 | Check your GitHub token credential in n8n |
| Claude API 401 | Verify Anthropic API key is correct |
| Empty commits/PRs | Ensure the repo had activity in the last 7 days |
| Discord 400 error | Verify webhook URL is valid and not expired |
| Email not sent | Check SMTP credentials and recipient address |
| Rate limiting (429) | GitHub allows 5000 req/hr with auth; Claude has per-org limits |

---

## 📁 Project Structure

```
n8n-weekly-summary/
├── README.md                    # This file
├── weekly-dev-summary.json      # n8n workflow (import this)
├── sample-output.md             # Example generated report
└── assets/
    └── workflow-diagram.svg     # Visual workflow topology
```

---

## 📜 License

MIT — Use freely, modify as needed, contributions welcome.

---

*Built for the [Claude Builders Bounty](https://github.com/anthropics/claude-builders-bounty) Issue #5 — n8n + Claude Weekly Report Automation ($200)*
