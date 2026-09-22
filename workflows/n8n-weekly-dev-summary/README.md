# n8n + Claude API — Automated Weekly Developer Summary 📊

An automated n8n workflow that triggers every Friday at 5:00 PM, aggregates the past 7 days of GitHub repository activity (commits, closed issues, merged PRs), sends the structured data to the **Claude API** (`claude-3-7-sonnet-20250219`), and delivers a clean executive narrative digest to your team's **Discord or Slack channel**.

---

## Workflow Diagram

```text
[Cron: Fri 5:00 PM] ──▶ [Configure Variables] ──▶ [Calculate 7-Day Window]
                                                          │
                             ┌────────────────────────────┴────────────────────────────┐
                             ▼                                                         ▼
                  [GitHub: Fetch Commits]                                   [GitHub: Fetch Closed Issues & PRs]
                             │                                                         │
                             └────────────────────────────┬────────────────────────────┘
                                                          ▼
                                            [Aggregate Metrics & Prompt]
                                                          │
                                                          ▼
                                            [Claude API: Generate Digest]
                                                          │
                                                          ▼
                                            [Discord / Slack Webhook Node]
```

---

## Setup in 5 Steps

### Step 1: Import Workflow into n8n
1. In your n8n workspace, navigate to **Workflows** > **Add Workflow**.
2. Click **Import from File** in the top-right menu and select `weekly-dev-summary.json`.

### Step 2: Configure Your Credentials
Open the **Configure Workflow Variables** node and fill in:
- `github_owner`: GitHub organization or username (e.g. `MergeFi`)
- `github_repo`: Repository name (e.g. `frontend`)
- `github_token`: Your GitHub Personal Access Token (PAT)
- `anthropic_api_key`: Your Anthropic API Key (`sk-ant-...`)
- `webhook_url`: Discord Webhook or Slack Incoming Webhook URL
- `language`: `EN` (English) or `FR` (French)

### Step 3: Test Workflow Execution
Click **Test step** on the last node or run **Execute Workflow** to generate a live digest test.

### Step 4: Toggle Active
Flip the toggle at the top of the workflow canvas from **Inactive** to **Active**.

### Step 5: Receive Weekly Digests
Your team will now receive automated weekly summaries every Friday at 5:00 PM!

---

## Sample Generated Digest

> 📢 **Weekly Dev Digest: MergeFi/frontend (2026-09-20)**
>
> 🎯 **Key Highlights**
> The team completed a comprehensive frontend hardening and accessibility pass across 12 tracking issues, reaching 100% CI pass rate.
>
> 🚀 **Features & Enhancements**
> - Implemented multi-asset mock data routing for XLM and USDC tokens.
> - Added dynamic active navigation indicator and error boundaries.
>
> 🛠️ **Bug Fixes & Refactoring**
> - Intercepted wallet reconnect races on testnet network switches.
> - Pinned all 3rd-party GitHub Actions in CI workflows to full commit SHAs.
>
> 📈 **Next Week Outlook**
> Moving forward with mainnet contracts deployment and escrow fee distribution testing.
