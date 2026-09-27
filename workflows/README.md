# 🤖 Automated Weekly Dev Summary (n8n + Claude API)

> Production-ready n8n workflow that automatically compiles GitHub repository activity (commits, closed issues, merged pull requests) over the past 7 days and uses Anthropic's Claude 3.5 Sonnet to generate an executive weekly developer narrative delivered straight to your Discord or Slack channel.

Bounty resolution for **Issue #5 ($200)**: `WORKFLOW: n8n + Claude Code — automated weekly dev summary`.

---

## 📋 Features

- ⏰ **Weekly Cron Schedule:** Fires automatically every Friday at 5:00 PM (`0 17 * * 5`).
- 🐙 **Tri-Stream GitHub Ingestion:** Concurrently queries GitHub REST API v3 for:
  - Merged Pull Requests (last 7 days)
  - Closed Issues (excluding PR stubs)
  - Pushed Commits (with author & SHA hash)
- 🧠 **Claude 3.5 Sonnet Intelligence:** Synthesizes structured data into an engaging 4-part developer narrative:
  1. 🚀 Key Highlights & Big Wins
  2. 🛠️ Engineering & Bug Fixes
  3. 🤝 Community & Contributor Shoutouts
  4. 🔮 What to Watch Next Week
- 🌐 **Multi-Language Support:** Seamlessly switch summary generation between **English (`EN`)** and **French (`FR`)**.
- 💬 **Discord & Slack Compatible:** Formatted rich embeds with activity counters and Markdown body.

---

## 🚀 5-Step Setup Instructions

### Step 1: Import Workflow into n8n
1. In your n8n workspace, click **Add Workflow** ➔ **Import from File**.
2. Select [`weekly-dev-summary-claude.json`](./weekly-dev-summary-claude.json).

### Step 2: Configure Anthropic & GitHub Credentials
1. Under **Credentials** in n8n, create an **Header Auth** credential for Anthropic:
   - Header Name: `x-api-key`
   - Header Value: `your_anthropic_api_key`
2. Create an optional **Header Auth** credential for GitHub (to increase rate limits to 5,000 req/hr):
   - Header Name: `Authorization`
   - Header Value: `Bearer ghp_your_github_token`

### Step 3: Customize Repository & Language Variables
Open the node named **`Configuration Variables`** and adjust the values:
- `GITHUB_REPO_OWNER`: GitHub username or organization (e.g. `claude-builders-bounty`)
- `GITHUB_REPO_NAME`: Target repository name (e.g. `claude-builders-bounty`)
- `SUMMARY_LANGUAGE`: Set to `EN` (English) or `FR` (French)
- `DISCORD_WEBHOOK_URL`: Your destination Discord or Slack incoming webhook URL

### Step 4: Verify or Adjust Execution Schedule
- The **`Weekly Trigger (Friday 5PM)`** node is pre-set with cron `0 17 * * 5` (every Friday at 17:00).
- You can freely customize the day/time to match your team's standup or sprint cadence.

### Step 5: Test & Activate
1. Click **Test Step** or **Execute Workflow** to run a manual verification.
2. Toggle the switch at the top right from **Inactive** to **Active**.
3. You will receive an instant summary directly in your team's chat!

---

## 🧪 Architecture & Node Flow

```
[Weekly Trigger: Fri 5PM]
         │
         ▼
[Configuration Variables] (Repo, Lang, Webhook)
         │
         ▼
[Calculate Date Range] (ISO 8601 7-day lookback)
         ├──► [Fetch Weekly Commits] ─────────┐
         ├──► [Fetch Closed Issues]  ─────────┼──► [Aggregate GitHub Digest Payload]
         └──► [Fetch Closed PRs]     ─────────┘                   │
                                                                  ▼
                                                   [Call Claude API (Sonnet)]
                                                                  │
                                                                  ▼
                                                   [Deliver Discord/Slack Webhook]
```

---

## 🛡️ Verification & Test Suite

This workflow includes an automated Vitest validation suite in `tests/workflow-validator.test.ts` verifying:
- Complete JSON schema integrity
- Cron expression syntax (`0 17 * * 5`)
- Strict Claude API payload contracts (`claude-3-5-sonnet-20241022`, max_tokens: 2500)
- Fallback & error handling for empty activity weeks
