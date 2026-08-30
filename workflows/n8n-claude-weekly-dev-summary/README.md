# Automated Weekly Dev Summary (n8n + Claude Code)

An exportable n8n workflow that automatically compiles a repository's weekly development activity (commits, closed issues, merged pull requests) and uses Claude API (`claude-sonnet-4-20250514`) to synthesize a structured narrative summary delivered directly to Discord, Slack, or Email.

---

## 🚀 5-Step Setup Guide

### 1. Import Workflow into n8n
- In your n8n dashboard, click **Add Workflow** → **Import from File...**
- Select `workflow.json` from this repository.

### 2. Configure Environment Variables
In the **Config & Environment Variables** node, set:
- `GITHUB_REPO`: `owner/repository-name` (e.g. `facebook/react`)
- `SUMMARY_LANGUAGE`: `EN` (English) or `FR` (French)
- `DELIVERY_WEBHOOK_URL`: Your Discord/Slack incoming webhook URL.

### 3. Add API Credentials
- Add your GitHub Personal Access Token (for private repos) in the GitHub HTTP nodes.
- Set `ANTHROPIC_API_KEY` in your n8n environment variables or credential manager.

### 4. Test Execution
- Click **Test Workflow** in n8n.
- Confirm activity is fetched, synthesized by Claude, and delivered to your webhook.

### 5. Activate Schedule
- Toggle the workflow to **Active** to trigger automatically every Friday at 5:00 PM.

---

## ⚙️ Configurable Variables

| Variable | Description | Example Values |
|---|---|---|
| `GITHUB_REPO` | Target GitHub repository slug | `vercel/next.js`, `owner/repo` |
| `SUMMARY_LANGUAGE` | Language for Claude's narrative report | `EN`, `FR` |
| `DELIVERY_WEBHOOK_URL` | Discord or Slack webhook endpoint | `https://discord.com/api/webhooks/...` |
