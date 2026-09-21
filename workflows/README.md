# Weekly Dev Summary Workflow (n8n + Claude Code)

An automated n8n workflow that collects GitHub commits, closed issues, and merged PRs for the past week, summarizes them into a structured narrative using Claude API (`claude-sonnet-4-20250514`), and delivers the weekly summary via a Discord or Slack webhook every Friday at 5:00 PM.

---

## 🚀 Setup Instructions (5 Steps)

1. **Import Workflow**: Open your n8n instance, click **Workflows** > **Import from File**, and select `workflows/weekly_dev_summary.json`.
2. **Configure Variables**: Open the **Set Configuration** node in n8n and set your parameters:
   - `GITHUB_OWNER`: Your GitHub username/org (e.g. `claude-builders-bounty`)
   - `GITHUB_REPO`: Your repository name (e.g. `claude-builders-bounty`)
   - `WEBHOOK_URL`: Your Discord or Slack incoming webhook URL
   - `ANTHROPIC_API_KEY`: Your Anthropic API key (`sk-ant-...`)
   - `LANGUAGE`: `"EN"` (English) or `"FR"` (French)
3. **Set Schedule**: Confirm the **Schedule Trigger** node is configured to fire weekly on **Friday at 17:00 (5 PM)**.
4. **Test Workflow**: Click **Execute Workflow** to verify GitHub API retrieval, Claude API summarization, and webhook delivery to your Discord/Slack channel.
5. **Activate**: Toggle the workflow status switch to **Active** to enable automated weekly summaries.

---

## 📋 Features

- ⏰ **Automated Weekly Schedule**: Triggered every Friday at 5:00 PM.
- 📊 **GitHub Activity Aggregation**: Fetches commits, closed issues, and merged PRs for the previous 7 days.
- 🤖 **Claude 4 Intelligence**: Generates a narrative summary using `claude-sonnet-4-20250514`.
- 🌐 **Multi-Language Support**: Supports English (`EN`) and French (`FR`).
- 💬 **Universal Webhook Delivery**: Compatible with both Discord and Slack webhooks.

---

## 🖼️ Execution Proof

Below is a verified execution trace showing successful node executions (HTTP 200 OK) across all pipeline stages:

![n8n Weekly Dev Summary Workflow Execution](./n8n_execution_screenshot.jpg)
