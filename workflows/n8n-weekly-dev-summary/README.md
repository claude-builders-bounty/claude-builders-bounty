# 🤖 Automated Weekly Dev Summary (n8n + Claude Code)

An enterprise-ready, fully exportable **n8n workflow** that automatically compiles a weekly narrative summary of GitHub repository activity (commits, closed issues, merged PRs) using the Anthropic Claude API (`claude-sonnet-4-20250514`), delivering the report via Discord/Slack webhooks or email.

---

## 🌟 Features

- **Automated Trigger**: Weekly cron schedule (Default: Friday at 5:00 PM).
- **Parallel GitHub Ingestion**: Fetches commits, closed issues, and merged PRs for the trailing 7-day period.
- **Claude Sonnet Narrative Engine**: Generates high-signal executive summaries with highlights, bug fixes, and contributor acknowledgments.
- **Configurable Options**:
  - `REPO_OWNER` & `REPO_NAME`: Target repository.
  - `SUMMARY_LANGUAGE`: Supports `EN` (English) and `FR` (French).
  - `DELIVERY_CHANNEL`: Choose between `webhook` (Discord/Slack) or `email`.
- **Zero-Token Deduplication & Noise Filtering**: Excludes pull requests from issue streams and only processes merged PRs.

---

## 🚀 Setup Instructions (5 Steps)

### Step 1: Import the Workflow into n8n
1. Open your n8n workspace (self-hosted or n8n cloud).
2. Click **Add workflow** -> **Import from JSON**.
3. Select `weekly-dev-summary.json` from this repository.

### Step 2: Set Anthropic API Key
- In the node **Generate Narrative via Claude API**, configure header `x-api-key` with your Anthropic API key (`sk-ant-...`) or set the environment variable `ANTHROPIC_API_KEY`.

### Step 3: Configure Target Repository & Language
Double-click the **Workflow Configuration** node and set:
- `REPO_OWNER`: (e.g. `your-org`)
- `REPO_NAME`: (e.g. `your-repo`)
- `SUMMARY_LANGUAGE`: `EN` or `FR`
- `DELIVERY_CHANNEL`: `webhook` or `email`

### Step 4: Configure Delivery Destination
- **If using Discord / Slack Webhook**: Paste your webhook URL into `NOTIFICATION_WEBHOOK_URL`.
- **If using Email**: Configure SMTP credentials in the **Send Email Notification** node and set `EMAIL_RECIPIENT`.

### Step 5: Test and Activate
1. Click **Test Workflow** in n8n to execute an instant test run.
2. Toggle the workflow to **Active** to enable the weekly Friday schedule.

---

## 📊 Sample Output

```markdown
# 🚀 Weekly Engineering Digest: anthropics/anthropic-sdk-python
*Period: 2026-09-16 to 2026-09-23*

### 🌟 Executive Highlights
- Shipped streaming improvements with SSE chunk reconnection.
- Merged 8 pull requests and resolved 5 critical community issues.

### 🛠️ Key PRs Merged
- **#142**: Add support for Claude 4 model family endpoints.
- **#145**: Optimize JSON schema validation in tool execution harness.

### 🐛 Bug Fixes
- Fixed retry backoff exponential clamp on HTTP 429 rate limit errors.

### 👥 Top Contributors
Kudos to @johndoe, @alexsmith for active reviews and contributions this week!
```

---

## 📜 License
MIT License. Created for the Claude Builders Bounty Program.
