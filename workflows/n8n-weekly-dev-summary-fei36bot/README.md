# Automated Weekly GitHub Dev Summary (`n8n` + `claude-sonnet-4-20250514`)

> **Submission for `claude-builders-bounty/claude-builders-bounty#5` (`$200` Bounty)**

An import-ready `n8n` workflow ([`weekly-dev-summary-n8n.json`](./weekly-dev-summary-n8n.json)) that triggers every **Friday at 17:00**, fetches the past 7 days of GitHub commits, closed issues, and merged PRs, synthesizes a human-friendly narrative engineering summary using **Claude (`claude-sonnet-4-20250514`)** in **English (`EN`) or French (`FR`)**, and delivers it directly to **Discord or Slack** via webhook.

---

## Setup in 5 Steps (Under 5 Minutes)

### Step 1: Import the Workflow into n8n
In your n8n dashboard, click **Workflows → Add Workflow → Import from File...** and select [`weekly-dev-summary-n8n.json`](./weekly-dev-summary-n8n.json).

### Step 2: Set Your Environment Variables (or Edit the Config Node)
Provide the following variables in your n8n environment (or directly in the **`Workflow Config (Repo, Language, Webhook)`** node):
- `GITHUB_REPO`: Target repository in `owner/repo` format (e.g., `vercel/next.js`).
- `GITHUB_TOKEN`: Personal Access Token (fine-grained `contents:read`, `pull_requests:read`, `issues:read`).
- `ANTHROPIC_API_KEY`: Your Anthropic API key (`sk-ant-...`).
- `WEBHOOK_URL`: Your Discord or Slack Incoming Webhook URL.
- `SUMMARY_LANGUAGE`: Set to `EN` (English) or `FR` (French).

### Step 3: Verify the Cron Schedule
Open the **`Weekly Cron (Friday 17:00)`** node. By default, it runs on cron expression `0 17 * * 5` (every Friday at 5:00 PM in your n8n instance timezone).

### Step 4: Click "Test Workflow"
Click **Test workflow** in the n8n canvas to run an immediate live pass: the 3 GitHub HTTP nodes fetch commits, closed issues, and merged PRs from the last 7 days, merge them in **`Aggregate GitHub Activity & Build Prompt`**, call `claude-sonnet-4-20250514`, and post the formatted digest to your webhook.

### Step 5: Activate the Workflow
Toggle the workflow switch in the top-right corner from **Inactive** to **Active**.

