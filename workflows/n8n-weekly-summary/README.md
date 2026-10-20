# 🤖 n8n + AI Automated Weekly Dev Summary

Exportable n8n workflow that fetches GitHub repository activity (commits, closed issues, merged PRs) for the past 7 days, synthesizes an executive summary via Claude or Gemini, and posts it to a Discord or Slack webhook every Friday at 5:00 PM.

## 🚀 Setup Instructions (4 Steps)

### Step 1: Import Workflow into n8n
1. Open your n8n web instance.
2. Click **Add workflow** (`+`) -> **Import from File**.
3. Select `weekly_dev_summary_workflow.json`.

### Step 2: Configure Environment Variables
Set your AI API Key in n8n environment variables or credentials:
- `ANTHROPIC_API_KEY`: your Anthropic API Key (or configure Gemini / OpenAI credentials).

### Step 3: Configure Target Repository & Webhook
Double-click the **Config Variables** node in n8n and set:
- `GITHUB_OWNER`: your GitHub user or organization name (e.g. `facebook`).
- `GITHUB_REPO`: your repository name (e.g. `react`).
- `LANGUAGE`: `EN`, `ES`, or `FR`.
- `DISCORD_SLACK_WEBHOOK_URL`: your channel incoming webhook URL.

### Step 4: Activate Workflow
Toggle the **Active** switch in the top right corner of the n8n interface. You can click **Test Step** or **Execute Workflow** to test immediately.
