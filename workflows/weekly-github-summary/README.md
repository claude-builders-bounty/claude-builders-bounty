# Automated Weekly Dev Summary with n8n + Claude Code 📊

An enterprise-ready n8n workflow that automatically compiles a narrative summary of weekly GitHub development activity using the **Anthropic Claude API** (`claude-sonnet-4-20250514`) and dispatches it via **Discord Webhook** or **Email**.

---

## 🎯 Acceptance Criteria Satisfied

- [x] **Exportable n8n workflow**: Complete, clean, JSON file ready to import (`weekly-github-dev-summary.json`).
- [x] **Weekly cron schedule trigger**: Set to run automatically every **Friday at 5:00 PM** (`0 17 * * 5`).
- [x] **GitHub API Integration**: Fetches commits, closed issues, and merged Pull Requests from the last 7 days.
- [x] **Anthropic Claude API**: Integrates Claude Sonnet (`claude-sonnet-4-20250514`) to synthesize technical narrative updates.
- [x] **Multi-Channel Delivery**: Delivers via Discord/Slack webhook or Email notification with automated routing.
- [x] **Configurable Variables**: Easily switch `GITHUB_REPO`, `LANGUAGE` (`EN` or `FR`), and `DELIVERY_CHANNEL` in a single node.
- [x] **Automated Test Matrix**: Python verification suite (`tests/test_workflow.py`) validating graph connectivity and criteria.

---

## 🚀 Setup Instructions (4 Steps)

### Step 1: Import the Workflow into n8n
1. In your n8n dashboard, click **Workflows** > **Add Workflow** > **Import from File**.
2. Select `workflows/weekly-github-summary/weekly-github-dev-summary.json`.

### Step 2: Configure Environment Credentials
Ensure the following credentials / environment variables are set in your n8n environment:
- `ANTHROPIC_API_KEY`: Your Anthropic API key.
- `GITHUB_TOKEN` *(Optional for higher rate limits)*: GitHub Personal Access Token.

### Step 3: Customize Workflow Configuration
Double-click the **Workflow Configuration** node and set:
- `GITHUB_REPO`: Your repository (`owner/repo`).
- `LANGUAGE`: `EN` (English) or `FR` (French).
- `DELIVERY_CHANNEL`: `discord` or `email`.
- `WEBHOOK_URL`: Your Discord/Slack channel webhook URL.
- `EMAIL_RECIPIENT`: Your team mailing list or notification email.

### Step 4: Activate the Workflow
Toggle the **Active** switch in the top-right corner. The workflow will now trigger every Friday at 5:00 PM and broadcast your weekly developer accomplishments!

---

## 🧪 Testing & Verification

Run the automated specification test suite:

```bash
python3 workflows/weekly-github-summary/tests/test_workflow.py
```
