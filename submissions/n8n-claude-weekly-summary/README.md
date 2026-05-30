# 📊 GitHub Weekly Dev Summary — n8n + Claude Workflow

> Automatically generates a narrative weekly summary of any GitHub repository's activity using the Claude API, delivered via Discord, Slack, or Email every Friday at 5 PM.

**Bounty:** [claude-builders-bounty/claude-builders-bounty#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) — $200 powered by Opire

---

## ✅ Setup in 5 Steps

### Step 1: Import the Workflow into n8n
1. Open your n8n instance (`http://localhost:5678` or your hosted URL)
2. Go to **Workflows → Import from File**
3. Select `workflow.json` from this folder
4. Click **Import**

### Step 2: Create 2 Credentials in n8n (Settings → Credentials → New)

**GitHub Token** (`httpHeaderAuth` — name it `GitHub Token`):
| Field | Value |
|-------|-------|
| Name | `Authorization` |
| Value | `Bearer ghp_YOUR_GITHUB_TOKEN` |

> Create at: https://github.com/settings/tokens — Required scope: `repo`

**Anthropic API Key** (`httpHeaderAuth` — name it `Anthropic API Key`):
| Field | Value |
|-------|-------|
| Name | `x-api-key` |
| Value | `sk-ant-YOUR_ANTHROPIC_KEY` |

> Get at: https://console.anthropic.com/

### Step 3: Edit the Config Node

Open the **"Set Config & Date Range"** node and fill in:

```js
const CONFIG = {
  GITHUB_REPO: 'facebook/react',          // ← Your target repo
  DELIVERY_METHOD: 'discord',             // ← 'discord' | 'slack' | 'email'
  DISCORD_WEBHOOK_URL: 'https://...',     // ← Discord webhook URL
  SLACK_WEBHOOK_URL: 'https://...',       // ← Slack webhook URL (if using Slack)
  EMAIL_RECIPIENT: 'team@company.com',    // ← Email (if using email)
  LANGUAGE: 'EN',                         // ← 'EN' or 'FR'
};
```

**For Discord webhook:** Channel Settings → Integrations → Webhooks → New Webhook

### Step 4: Activate
Toggle the workflow to **Active** — it runs every **Friday at 5:00 PM** (server time).

To test immediately: Click **"Weekly Cron Trigger"** → **Test Step**.

### Step 5: Verify
After execution check:
- ✅ "Aggregate GitHub Data" node shows real commit/issue/PR data
- ✅ "Call Claude API" returns HTTP 200 with summary text
- ✅ Your Discord/Slack/email receives the formatted markdown summary

---

## 🏗️ Architecture

```
Weekly Cron (Fri 5PM)
        │
        ▼
Set Config & Date Range
        │
   ┌────┼────┐  (parallel)
   ▼    ▼    ▼
Commits Issues PRs  ← GitHub API
   └────┼────┘
        ▼
 Aggregate GitHub Data
        ▼
  Build Claude Prompt
        ▼
  Claude API (claude-sonnet-4-20250514)
        ▼
  Extract Summary Text
        ▼
  Delivery Router
  ┌─────┼──────┐
  ▼     ▼      ▼
Discord Slack  Email
```

## 🌍 Language Support
Set `LANGUAGE: 'EN'` or `LANGUAGE: 'FR'` — Claude generates the full summary in the chosen language.

## 📦 Files
| File | Description |
|------|-------------|
| `workflow.json` | Importable n8n workflow |
| `README.md` | This setup guide |

## ⚙️ Requirements
- n8n v1.0+
- GitHub Personal Access Token (`repo` read scope)
- Anthropic API Key
- Discord/Slack webhook OR SMTP server
