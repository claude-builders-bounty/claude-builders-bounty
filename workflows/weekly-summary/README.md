# Automated Weekly Dev Summary: n8n + Claude Code

A complete, production-ready **n8n workflow** that automatically aggregates weekly GitHub activity (commits, closed issues, merged pull requests) and leverages **Anthropic's Claude API (`claude-sonnet-4-20250514`)** to craft a concise, executive-ready narrative summary delivered directly to **Discord / Slack webhooks** or **Email**.

---

## ⚡ Quick Setup in 5 Steps

### Step 1: Import Workflow into n8n
1. Open your n8n workspace (self-hosted or n8n cloud).
2. Click **Add workflow** > **Import from File...** and select `workflows/weekly-summary/weekly_dev_summary.json` (or copy-paste the JSON).

### Step 2: Configure Workflow Variables
Open the **`Set Config Variables`** node and configure your preferences:
* `GITHUB_OWNER`: GitHub organization or username (e.g. `claude-builders-bounty`)
* `GITHUB_REPO`: Repository name (e.g. `claude-builders-bounty`)
* `SUMMARY_LANGUAGE`: Report language — set to `EN` (English) or `FR` (French)
* `DELIVERY_CHANNEL`: Set to `webhook` (default Discord / Slack) or `email`
* `DISCORD_SLACK_WEBHOOK_URL`: Your destination webhook URL
* `EMAIL_RECIPIENT`: Destination email address (if using email delivery)
* `CLAUDE_MODEL`: Defaults to `claude-sonnet-4-20250514`

### Step 3: Add Credentials
* **GitHub Header Auth**: Under credentials, create a `Header Auth` named `GitHub API Token` with:
  * Name: `Authorization`
  * Value: `Bearer <YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>`
* **Anthropic Claude Header Auth**: Create a `Header Auth` named `Anthropic Claude API` with:
  * Name: `x-api-key`
  * Value: `<YOUR_ANTHROPIC_API_KEY>`
* *(Optional)* **SMTP Credentials**: Required only if `DELIVERY_CHANNEL` is set to `email`.

### Step 4: Test Manual Execution
Click **Test step** or **Execute workflow** in n8n. Verify that commits, merged PRs, and closed issues are retrieved, summarized by Claude, and posted to your target webhook/channel.

### Step 5: Activate Schedule Trigger
Toggle the workflow switch from **Inactive** to **Active**. The cron schedule will automatically run every **Friday at 5:00 PM** (`0 17 * * 5`).

---

## 🛠️ Architecture & Data Flow

```text
[Cron Trigger: Friday 5PM]
           │
           ▼
[Set Config Variables]
           │
           ▼
[Calculate Date Window (Past 7 Days)]
           │
   ┌───────┼───────┐
   ▼       ▼       ▼
[Commits] [PRs] [Issues]
   └───────┬───────┘
           ▼
[Aggregate & Format Prompt]
           │
           ▼
[Call Claude API (claude-sonnet-4-20250514)]
           │
           ▼
[Format Multi-Channel Payloads]
           │
           ▼
[Route Delivery Channel (If/Else)]
       ├── Webhook ──► [Discord / Slack Webhook]
       └── Email   ──► [SMTP Email Notification]
```

---

## 📁 Repository Structure
```text
├── workflows/weekly-summary/
│   ├── weekly_dev_summary.json     # Importable n8n workflow file
│   ├── workflow.json               # Compatible mirror
│   ├── README.md                   # Detailed setup and configuration guide
│   └── sample_execution_output.md  # Real generated markdown sample report (EN & FR)
├── tests/
│   ├── validate_workflow.py        # Python automated schema & node connection validation
│   └── validate_workflow.js        # Node.js workflow validation suite
└── weekly_dev_summary.json         # Root-level importable workflow symlink/mirror
```

---

## 🧪 Automated Testing & Validation

Run the test suite to verify workflow JSON schema integrity, node graph connections, and cron trigger rules:

```bash
# Python validation test
python3 tests/validate_workflow.py

# Node.js validation test
node tests/validate_workflow.js
```
