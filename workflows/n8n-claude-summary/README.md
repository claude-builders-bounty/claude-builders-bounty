# n8n + Claude Code: Automated Weekly Dev Summary 🤖

An automated n8n workflow that fetches commits and pull requests from GitHub every week, sends them to Anthropic's Claude API (`claude-sonnet-4-20250514`), and publishes a narrative summary to Discord, Slack, or Email.

---

## ⚡ Quick Setup (5 Steps)

### Step 1: Import Workflow into n8n
In your n8n dashboard, click **Add Workflow** ➔ **Import from File** ➔ Select [`weekly_dev_summary.n8n.json`](./weekly_dev_summary.n8n.json).

### Step 2: Configure Environment Variables
In the **Workflow Config** node, set:
- `GITHUB_REPO_OWNER`: Your GitHub organization or username.
- `GITHUB_REPO_NAME`: Your target repository name.
- `SUMMARY_LANGUAGE`: `EN` or `FR`.
- `NOTIFICATION_CHANNEL`: `discord` or `slack`.

### Step 3: Add Credentials
- **GitHub Header Auth**: Header `Authorization`, Value `token ghp_your_github_token`.
- **Claude Header Auth**: Header `x-api-key`, Value `sk-ant-your_claude_key`.

### Step 4: Set Webhook Destination
In the **Send Discord / Slack Webhook** node, paste your target webhook URL.

### Step 5: Activate Workflow
Toggle the workflow switch to **Active**. It will automatically trigger every Friday at 5:00 PM and broadcast the executive engineering summary!

---

## 🧪 Testing & Validation

```bash
node --test workflows/n8n-claude-summary/validate_workflow.js
```
