# Automated Weekly Dev Summary via Claude API (n8n Workflow)

An automated n8n workflow that triggers every Friday at 5 PM to fetch weekly commits, merged PRs, and closed issues from any GitHub repository, summarizes the development activity using the Anthropic Claude API (`claude-sonnet-4-20250514`), and sends an executive narrative summary straight to your team's Slack or Discord channel.

---

## ⚡ Quickstart Setup (5 Steps)

1. **Import Workflow into n8n**  
   Open your n8n dashboard, click **Workflows** → **Import from File**, and select [`workflows/weekly-summary/workflow.json`](workflow.json).

2. **Set Environment Variables in n8n**  
   Ensure `ANTHROPIC_API_KEY` is set in your n8n environment variables (or configured under Credentials for the Anthropic API node).

3. **Configure Target Repository & Language**  
   Open the **Set Workflow Config** node in n8n and set your desired parameters:
   - `GITHUB_OWNER`: GitHub username or organization (e.g., `claude-builders-bounty`)
   - `GITHUB_REPO`: Repository name (e.g., `claude-builders-bounty`)
   - `SUMMARY_LANGUAGE`: Target summary language (`EN` for English, `FR` for French)
   - `DELIVERY_WEBHOOK_URL`: Your Slack or Discord incoming webhook URL

4. **Test Run Workflow**  
   Click **Execute Workflow** in n8n to test fetching GitHub activity, calling Claude API, and dispatching the summary webhook.

5. **Activate Weekly Schedule**  
   Toggle the workflow to **Active** (Top Right in n8n) to run automatically every Friday at 5:00 PM.

---

## 🛠️ Architecture Overview

```
[Weekly Cron Trigger (Fri 5PM)]
          │
          ▼
[Set Workflow Config Variables]
          │
  ┌───────┼───────┐
  ▼       ▼       ▼
[Commits] [PRs] [Issues]
  └───────┬───────┘
          ▼
[Format Claude Prompt (EN/FR)]
          │
          ▼
[Call Claude API (claude-sonnet-4-20250514)]
          │
          ▼
[Deliver Summary via Webhook (Slack/Discord)]
```

---

## 📄 License

SPDX-License-Identifier: MIT  
Copyright (c) 2026 claude-builders-bounty
