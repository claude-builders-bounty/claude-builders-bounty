# Automated Weekly Dev Summary (n8n + Claude Sonnet)

Automated n8n workflow that triggers weekly on Friday at 5 PM, aggregates GitHub repository activity (**commits, closed issues, and merged pull requests**), sends the digest to Anthropic's Claude API (`claude-sonnet-4-20250514`), and publishes an executive narrative engineering report to Discord or Slack.

---

## Acceptance Criteria Checklist
- [x] **Exportable n8n workflow:** Importable `n8n-weekly-dev-summary.json`
- [x] **Trigger:** Weekly cron schedule (Friday at 17:00)
- [x] **GitHub API Data:** Fetches commits, closed issues, and merged PRs for the past 7 days
- [x] **Claude API Integration:** Calls `claude-sonnet-4-20250514` to synthesize narrative reports
- [x] **Delivery Channel:** Discord / Slack incoming webhook support
- [x] **Configurable Variables:** Target repository (`owner/repo`), destination webhook URL, language (`EN` / `FR`)
- [x] **5-Step Setup Documentation:** Complete instructions in 5 steps or fewer

---

## 5-Step Setup Guide

### Step 1: Import Workflow into n8n
1. In your n8n workspace, navigate to **Workflows**.
2. Click **Add Workflow** -> **Import from File**.
3. Select [`n8n-weekly-dev-summary.json`](./n8n-weekly-dev-summary.json).

### Step 2: Set Anthropic API Key
Set your `ANTHROPIC_API_KEY` in your n8n environment variables:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```
*(Or click the `Call Claude API (Sonnet)` node and supply your API key in the Header Parameters).*

### Step 3: Configure Target Repository & Language
Open the **Workflow Configuration** node and set:
- `GITHUB_REPO_OWNER`: Your GitHub organization or username (e.g. `claude-builders-bounty`)
- `GITHUB_REPO_NAME`: Your target repository (e.g. `claude-builders-bounty`)
- `SUMMARY_LANGUAGE`: Set to `EN` (English) or `FR` (French)

### Step 4: Add Destination Webhook
- Create an incoming webhook in your Discord channel (or Slack incoming webhook).
- Paste the webhook URL into `DISCORD_WEBHOOK_URL` in the **Workflow Configuration** node.

### Step 5: Test and Activate
1. Click **Test Workflow** in n8n to execute immediately and review the generated summary.
2. Toggle the workflow to **Active** to run on the automatic Friday schedule.

---

## License
MIT
