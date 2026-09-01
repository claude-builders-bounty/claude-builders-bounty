# 🚀 Automated Weekly Dev Summary: n8n + Claude Code

An end-to-end autonomous n8n workflow that aggregates weekly GitHub repository activity (merged PRs, closed issues, commits), synthesizes a structured executive narrative via **Claude Messages API**, and delivers formatted markdown digest updates to **Discord, Slack, or custom webhooks**.

---

## 📋 Features
- ⏰ **Automated Weekly Schedule**: Configurable cron trigger (default: Fridays 5:00 PM UTC).
- 🐙 **GitHub REST API Integration**: Queries commits, merged pull requests, and closed issues for the past 7 days.
- 🧠 **Claude API Synthesis**: Employs Anthropic's Claude API to generate structured, stakeholder-ready changelogs and velocity insights.
- 📢 **Multi-Channel Dispatch**: Out-of-the-box payload formatting for Discord, Slack, and generic webhooks.
- ⚡ **Zero Heavy Dependencies**: Pure JSON workflow ready to import into any n8n instance (Cloud or Self-Hosted).

---

## 🛠️ Quick Setup (5 Steps)

### Step 1: Import Workflow into n8n
1. Open your **n8n instance** (Self-hosted or n8n Cloud).
2. Click **Add workflow** `+` > select `...` in top-right > **Import from File**.
3. Select `n8n_github_weekly_summary.json`.

### Step 2: Configure Credentials in n8n
In n8n **Credentials**:
- **Anthropic Claude API**: Create a `Header Auth` credential with:
  - Name: `x-api-key`
  - Value: `YOUR_ANTHROPIC_API_KEY` (from [console.anthropic.com](https://console.anthropic.com/))
- *(Optional)* **GitHub API**: For private repos or higher rate limits, add a `Header Auth` credential:
  - Name: `Authorization`
  - Value: `token YOUR_GITHUB_PAT`

### Step 3: Set Workflow Parameters
Open the **`Workflow Configuration`** node and configure:
- `GITHUB_OWNER`: Repository owner/organization (e.g., `claude-builders-bounty`)
- `GITHUB_REPO`: Repository name (e.g., `claude-builders-bounty`)
- `LOOKBACK_DAYS`: `7`
- `DELIVERY_CHANNEL`: `DISCORD` or `SLACK`
- `WEBHOOK_URL`: Your target webhook endpoint URL
- `CLAUDE_MODEL`: `claude-sonnet-4-20250514` (or `claude-opus-5`)
- `TARGET_LANGUAGE`: `EN` (or `PT-BR`, `ES`, `FR`)

### Step 4: Test & Verify
1. Click **Test Workflow** in the n8n UI canvas.
2. Verify that GitHub metrics are collected, Claude generates the summary digest, and the payload is successfully dispatched to your webhook.

### Step 5: Activate Workflow
Toggle the workflow status from **Inactive** to **Active** in the top-right corner to enable the weekly automated schedule.

---

## 📊 Summary Output Structure
Every week, Claude delivers a structured summary formatted as:
1. 🚀 **Executive Headline & Key Highlights**
2. 🛠️ **Major Features & Merged PRs** (with direct PR links and authors)
3. 🐛 **Bug Fixes & Resolved Issues**
4. 📊 **Activity Velocity Summary** (Total Commits, Merged PRs, Issues closed)
5. 🎯 **Next Week Outlook**

---

## 🧪 Validation & Linting
To validate workflow schema syntax and node integrity locally:
```bash
python3 validate_workflow.py
```
