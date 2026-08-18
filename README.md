# Automated Weekly Dev Summary via n8n & Claude API

An exportable **n8n workflow** that automatically aggregates GitHub activity (commits, closed issues, merged PRs) on a weekly cron schedule, calls the Claude API (`claude-3-7-sonnet-20250219`), and delivers a formatted summary to Discord or Slack.

## 🚀 Quick Setup (4 Steps)

### Step 1: Import Workflow into n8n
In your n8n UI, navigate to **Workflows -> Import from File** and select `src/n8n_weekly_dev_summary.json`.

### Step 2: Configure Environment Variables
Set your Anthropic API Key in your n8n credentials store:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Step 3: Configure Target Repository & Webhook
In the **Set Workflow Variables** node, update:
- `GITHUB_OWNER`: Target GitHub account/organization
- `GITHUB_REPO`: Target repository name
- `SUMMARY_LANGUAGE`: `EN` or `FR`
- `DISCORD_WEBHOOK_URL`: Target Discord / Slack webhook endpoint

### Step 4: Validate Workflow
Run the automated Python test runner:
```bash
python tests/test_workflow_validator.py
```
Outputs: `2/2 PASSED`
