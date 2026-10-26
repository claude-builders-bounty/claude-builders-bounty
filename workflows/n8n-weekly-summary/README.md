# Automated Weekly Dev Summary with n8n & Claude Code

An automated, production-ready [n8n](https://n8n.io) workflow that aggregates engineering activity from GitHub across the past 7 days (commits, merged pull requests, and closed issues) and uses the Anthropic Claude API (`claude-3-5-sonnet-20241022`) to compose an executive, narrative developer digest delivered directly to your team's Slack or Discord channel every Friday at 5:00 PM.

---

## Architecture & Data Flow

```text
  ┌─────────────────────────────────┐
  │   Weekly Trigger (Friday 5PM)   │
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │  Config Variables & 7-Day Window │
  └────────────────┬────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼         ▼         ▼
  ┌──────────┐┌──────────┐┌──────────┐
  │ Commits  ││ Closed   ││ Merged   │
  │ Endpoint ││ Issues   ││ PRs      │
  └────┬─────┘└────┬─────┘└────┬─────┘
       │           │           │
       └───────────┼───────────┘
                   ▼
  ┌─────────────────────────────────┐
  │   Aggregate & Format Prompt     │
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │      Call Claude Messages API   │
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │    Parse Output & Channel Switch │
  └────────┬─────────────────┬──────┘
           ▼                 ▼
  ┌─────────────────┐┌─────────────────┐
  │  Slack Webhook  ││ Discord Webhook │
  └─────────────────┘└─────────────────┘
```

---

## Setup in 5 Steps

### Step 1: Import Workflow into n8n
1. In your n8n workspace, navigate to **Workflows** > **Add Workflow**.
2. Click **Import from File** (or press `Ctrl+O` / `Cmd+O`) and select [`workflow.json`](workflow.json).

### Step 2: Configure Environment Variables
Set the following environment variables in your n8n instance (or configure them directly in the **Config Variables** node):

| Variable | Required | Description | Example |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | Anthropic API key for Claude | `sk-ant-api03-...` |
| `GITHUB_TOKEN` | Optional | GitHub PAT for higher rate limits (5,000 req/hr) | `ghp_...` |
| `GITHUB_REPO_OWNER` | **Yes** | Repository owner or organization | `BasedHardware` |
| `GITHUB_REPO_NAME` | **Yes** | Repository name | `omi` |
| `SUMMARY_LANGUAGE` | No | Language of generated report (`EN` or `FR`) | `EN` |
| `DELIVERY_CHANNEL` | No | Destination platform (`slack` or `discord`) | `slack` |
| `SLACK_WEBHOOK_URL` | If Slack | Incoming Webhook URL from Slack App | `https://hooks.slack.com/services/...` |
| `DISCORD_WEBHOOK_URL`| If Discord | Webhook URL from Discord channel settings | `https://discord.com/api/webhooks/...` |

### Step 3: Test Run
Click **Test Workflow** in the canvas to trigger an immediate run. Check the execution logs to verify GitHub data retrieval and Claude's response.

### Step 4: Verify Delivery
Check your designated Slack or Discord channel for the formatted weekly executive digest.

### Step 5: Activate
Toggle the **Active** switch in the top-right corner to enable the automated Friday 5:00 PM cron schedule.

---

## Sample Output

### English (`SUMMARY_LANGUAGE=EN`)
```markdown
*Weekly Dev Summary: BasedHardware/omi (2026-10-19 to 2026-10-26)*

### 🚀 Executive Narrative
This week, engineering delivered critical route authentication safeguards across plugin endpoints, addressed high-priority audio drop recovery on Ray-Ban Meta wearable integration, and improved data sync resilience. With 5 PRs merged and 12 under active review, system security and real-time capture stability saw significant leaps forward.

### 📦 Key Shipped Features & Enhancements
- **Ray-Ban Meta Audio Recovery (#20782)**: Added fallback reconnect handling and wedge monitor coverage when audio capture initialization fails.
- **Plugin Route Auth Defense (#14428, #14430, #14451, #14453, #15089)**: Enforced HMAC byte comparison and caller validation on Zapier, Hume AI, Twitter tools, and Whoop data routes.

### 🛡️ Resolved Issues & Fixes
- #21122: Handled unhandled backfill queue owner deferrals.
- #21749: Added 3-byte millivolts battery format support.
- #20779: Retried failed BLE codec reads to prevent PCM8 fallback.

### 🌟 Contributor Spotlight
Shout-out to @hardik4love-lang for landing core route auth hardening and wearable audio drop recovery!
```

---

## Automated Tests

Run the test suite to verify workflow syntax, connection graphs, and transformation logic:

```bash
python validate_workflow.py
```
