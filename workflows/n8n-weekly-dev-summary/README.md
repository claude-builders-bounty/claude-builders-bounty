# Automated Weekly Dev Summary with n8n & Claude Sonnet 4

A production-grade n8n automation workflow that aggregates weekly GitHub commits, closed issues, and merged pull requests, passes them to **Claude Sonnet 4** (`claude-sonnet-4-20250514`), and broadcasts a polished narrative summary to **Discord**, **Slack**, or **Email**.

![Execution Success](execution-success.svg)

---

## 🚀 Setup Instructions in 5 Steps

### Step 1: Import Workflow into n8n
1. Open your self-hosted or cloud **n8n** instance.
2. Click **Add Workflow** > **Import from File...** and select [`weekly_dev_summary_n8n.json`](weekly_dev_summary_n8n.json).

### Step 2: Configure Environment Credentials
Set your Anthropic API Key in your n8n environment or global credentials:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-your-anthropic-key"
```
*(Optionally provide `GITHUB_TOKEN` if monitoring private repositories with high rate-limits).*

### Step 3: Customize Config Variables Node
Open the **Config Variables** node inside the canvas and configure your targets:
- `GITHUB_OWNER`: Your GitHub username or organization (e.g. `claude-builders-bounty`).
- `GITHUB_REPO`: Target repository name.
- `OUTPUT_CHANNEL`: Select `discord`, `slack`, or `email`.
- `LANGUAGE`: Set to `EN` (English) or `FR` (French).
- `WEBHOOK_URL`: Your destination Discord/Slack incoming webhook URL.

### Step 4: Test Workflow Execution
Click **Test Workflow** in the n8n canvas. Inspect the green execution markers across all 10 nodes and verify the rich embed in your chosen Discord or Slack channel.

### Step 5: Activate Weekly Schedule Trigger
Toggle the workflow switch to **Active**. The schedule trigger automatically executes every **Friday at 5:00 PM UTC** (`0 17 * * 5`) over a rolling 7-day window.

---

## 🧪 Automated Workflow Validation
```bash
python workflows/n8n-weekly-dev-summary/test_n8n_workflow.py
```
- ✅ Validates n8n JSON schema & 10-node DAG connectivity
- ✅ Confirms cron trigger: Friday 5pm (`0 17 * * 5`)
- ✅ Confirms Anthropic model: `claude-sonnet-4-20250514`
- ✅ Confirms multi-channel (Discord/Slack/Email) & multi-language (EN/FR) logic
