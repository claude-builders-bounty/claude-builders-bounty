# 🚀 Automated Weekly Dev Summary: n8n + Claude Code Workflow
> Built for [GitHub Issue #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) — **$200 Bounty (Powered by Opire)**.

An end-to-end, zero-maintenance **n8n workflow** that automatically compiles a repository's weekly activity (commits, merged PRs, and closed issues) and uses **Claude Sonnet** to author an engaging, narrative executive summary delivered directly to Discord, Slack, or Email every Friday afternoon.

---

## 🌟 Key Features

* ⏱️ **Zero-Touch Automation**: Triggers on a weekly schedule (Default: Friday at 5:00 PM).
* 📊 **Multi-Vector Activity Ingestion**: Pulls raw commits, merged PRs, and resolved issues from GitHub's REST API.
* 🧠 **Claude Sonnet Narrative Engine**: Synthesizes dry git diffs into executive themes, shipped highlights, bug fixes, and contributor shoutouts.
* 🌍 **Bilingual Support (EN / FR)**: Configurable variable to output native English or French digests.
* 📢 **Multi-Channel Dispatch**: Drop-in compatible with Discord Webhooks, Slack Incoming Webhooks, or SMTP Email.

---

## ⚡ 5-Step Setup Instructions

### Step 1: Import the Workflow
1. Open your self-hosted or cloud **n8n** instance (`http://localhost:5678`).
2. Go to **Workflows** → Click **Add Workflow** (or `Cmd+O`).
3. Click the top-right **`...` menu** → Select **Import from File**.
4. Choose [`workflows/weekly_dev_summary_claude.json`](./workflows/weekly_dev_summary_claude.json).

### Step 2: Configure Environment Variables
Set your Anthropic API Key in your n8n environment or as an HTTP Header credential:
* Variable name: `ANTHROPIC_API_KEY`
* Value: `sk-ant-api03-...`

*(Optional)* If accessing private GitHub repos, add a GitHub Personal Access Token (`GH_TOKEN`) with `repo` scope to the GitHub HTTP nodes.

### Step 3: Customize Repository & Target Variables
Double-click the **`Configurable Variables`** node and adjust the values:
* `repo_owner`: Target GitHub organization or username (e.g. `claude-builders-bounty`)
* `repo_name`: Target repository name
* `summary_language`: Set to `EN` (English) or `FR` (French)
* `destination_webhook_url`: Paste your Discord or Slack Webhook URL.

### Step 4: Test Execution (Manual Trigger)
Click **`Test workflow`** at the bottom of the canvas.
1. The workflow will query GitHub for the last 7 days of activity.
2. The Code Aggregator formats the markdown prompt.
3. Claude Sonnet processes the context and returns the narrative summary.
4. Your webhook channel will receive the formatted announcement immediately!

### Step 5: Activate the Schedule
Toggle the **Active** switch at the top-right of the workflow to `ON`.
The cron schedule will now execute automatically every Friday at 17:00 UTC.

---

## 📄 Pull Request & Payout Verification
* **Bounty Issuer**: [Opire.dev](https://opire.dev)
* **Target Issue**: `#5`
* **Recipient Wallet / Address**: Linked to author GitHub account upon PR merge.
