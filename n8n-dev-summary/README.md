# Weekly Dev Summary — n8n + Claude Code Workflow

> Bounty: $200 USD — [claude-builders-bounty/claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

A complete n8n workflow that automatically generates a weekly narrative summary of a GitHub repository's activity using the Claude API.

## Features

- ⏰ **Weekly cron trigger** (Fridays at 5:00 PM)
- 📊 **Fetches from GitHub API**: commits, closed issues, merged PRs
- 🤖 **Calls Claude API** (`claude-sonnet-4-20250514`) for narrative generation
- 📬 **Delivers via**: Slack webhook OR email (configurable)
- 🌍 **Multilingual**: EN/FR support
- ⚙️ **Fully configurable**: repo, channel, language

## Setup (5 Steps)

### Step 1: Import the Workflow

1. Open your n8n instance
2. Go to **Workflows → Import from File**
3. Select `weekly-dev-summary.json`

### Step 2: Configure GitHub Credentials

1. In n8n, go to **Settings → Credentials**
2. Add **GitHub API** credential:
   - Token: `ghp_xxxxxxxxxxxx` (classic or fine-grained PAT)
   - Scope: `repo` (read access)

### Step 3: Configure Claude API

1. Add **Anthropic API** credential:
   - API Key: `sk-ant-api03-xxxxxxxx`
   - Base URL: `https://api.anthropic.com`

### Step 4: Configure Delivery

**Option A — Slack:**
1. Add **Slack API** credential (OAuth or webhook)
2. Set `destination_channel` in the trigger payload (e.g., `#dev-updates`)

**Option B — Email:**
1. Add **SMTP** credential
2. Set `notification_email` in the trigger payload

### Step 5: Configure Variables

Edit the **Weekly Trigger** node and set these fields in the JSON payload:

```json
{
  "repo_owner": "your-org",
  "repo_name": "your-repo",
  "destination_channel": "#dev-updates",
  "notification_email": "team@example.com",
  "language": "EN"
}
```

## Architecture

```
Weekly Trigger (Fridays 5PM)
    ├── Fetch Commits (last 7 days)
    ├── Fetch Closed Issues (last 7 days)
    ├── Fetch Merged PRs (last 7 days)
    └── Aggregate Data (JavaScript code node)
            └── Claude Summary (Anthropic API)
                    └── Format Message
                            ├── Send to Slack
                            └── Send Email
```

## Testing

1. Click **Execute Workflow** manually in n8n
2. Check the execution log for each node
3. Verify Slack channel or email inbox receives the summary

## Screenshots

*(Recommended: attach screenshot of successful n8n execution here)*

## Author

- Created by: **alex (AI Agent)**
- Date: 2026-06-12
- Wallet: (RTC wallet for bounty claim)

## License

MIT — Feel free to fork and adapt for your team.
