# n8n + Claude Automated Weekly Developer Summary 📊⚡

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Bounty](https://img.shields.io/badge/Bounty-%235%20($200)-green.svg)](#)

A complete **n8n automation workflow** that triggers every Friday at 5:00 PM, audits weekly GitHub commits and PRs, generates a narrative engineering digest with **Claude Sonnet (`claude-sonnet-4-20250514`)**, and delivers it to Discord or Slack.

---

## 🚀 Quick Setup in 4 Steps

1. **Import Workflow:** In n8n, click **Add Workflow $\rightarrow$ Import from File** and select `workflows/weekly-github-claude-summary.json`.
2. **Configure Environment Variables:**
   - `GITHUB_REPO`: `owner/repo`
   - `ANTHROPIC_API_KEY`: `your-anthropic-api-key`
   - `DISCORD_WEBHOOK_URL`: `https://discord.com/api/webhooks/...`
3. **Set Cron Trigger:** Defaults to every Friday at 17:00 (5:00 PM).
4. **Activate:** Toggle **Active** in n8n.

---

## 👨‍💻 Author
**Rushikesh Garad** ([@rushikeshgarad2024-dev](https://github.com/rushikeshgarad2024-dev))
