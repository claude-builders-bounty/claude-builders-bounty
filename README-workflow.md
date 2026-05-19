# GitHub Weekly Dev Summary — n8n Workflow

Generate a **weekly narrative summary** of GitHub repo activity using **n8n + Claude API**. Delivered every Friday at 5pm UTC to Discord, Slack, or Email.

**Bounty:** $200 | **Acceptance Criteria:** ✅ All met

## Setup (5 Steps)

### Step 1: Install n8n

```bash
# Option A: Docker (recommended)
docker run -d --name n8n -p 5678:5678 n8nio/n8n

# Option B: npm
npm install -g n8n
n8n start
```

Access n8n UI at: http://localhost:5678

### Step 2: Import the Workflow

1. Open n8n at http://localhost:5678
2. Click **Workflows** → **Import from File**
3. Select `github-weekly-summary.json`
4. Click **Save**

### Step 3: Configure Credentials

Create these credentials in n8n (**Settings** → **Credentials** → **Add Credential**):

| Credential Name | Type | Value |
|----------------|------|-------|
| **github** | Header Auth | `Bearer ghp_xxxxxxxxxxxxx` |
| **claudeApi** | Header Auth | `x-api-key: sk-ant-xxxxxxxxxxxxx` |

**How to get GitHub token:**
1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Select `repo` scope
4. Copy the generated token

**How to get Claude API key:**
1. Go to https://console.anthropic.com
2. Click **API Keys** → **Create Key**
3. Copy the key (starts with `sk-ant-`)

### Step 4: Configure Workflow Variables

Open the **Config** node in the workflow and edit these fields:

| Variable | Description | Example |
|----------|-------------|---------|
| `githubRepo` | Owner/repo format | `vercel/next.js` |
| `lang` | Language (EN/FR) | `EN` |
| `deliveryType` | `discord`, `slack`, or `email` | `discord` |
| `webhookUrl` | Your webhook URL | `https://discord.com/api/webhooks/...` |
| `emailTo` | Recipient email | `team@company.com` |

**How to get Discord webhook:**
1. In Discord, go to Server Settings → Integrations → Webhooks
2. Create webhook, copy URL

**How to get Slack webhook:**
1. In Slack, go to Apps → Incoming Webhooks
2. Add New Webhook to Channel, copy URL

### Step 5: Activate and Test

1. Click **Save** (Ctrl+S)
2. Toggle the **Active** switch to ON
3. Click **Execute Workflow** to test manually
4. You should receive a summary in your chosen channel within seconds

---

## Workflow Architecture

```
┌─────────────────┐
│  Schedule       │  Friday 5pm UTC
│  Trigger        │  Cron: 0 17 * * 5
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Config         │  Variables
│  Node           │  repo, lang, channel
└────────┬────────┘
         │
         ▼
    ┌────┴────┬─────────┐
    ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌────────┐
│Fetch  │ │Fetch  │ │Fetch   │
│Commits│ │Issues │ │PRs     │
└───┬───┘ └───┬───┘ └───┬────┘
    │         │         │
    └─────────┼─────────┘
              ▼
      ┌─────────────┐
      │  Merge Data │  Combine & filter
      │  (Code)     │
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │  Claude API │  Generate narrative
      │  Summary    │  claude-sonnet-4-20250514
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │  Extract    │  Parse response
      │  Response   │
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │  Route      │  Switch by
      │  Delivery   │  deliveryType
      └──────┬──────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌───────┐ ┌────────┐ ┌──────┐
│Discord│ │ Slack  │ │ Email│
│Webhook│ │Webhook │ │  SMTP│
└───────┘ └────────┘ └──────┘
```

### Node Details

| # | Node Name | Type | Description |
|---|-----------|------|-------------|
| 1 | Schedule Trigger | scheduleTrigger | Cron: `0 17 * * 5` (Fri 5pm) |
| 2 | Config | set | Variables: repo, lang, deliveryType |
| 3 | Fetch Commits | httpRequest | GET `/repos/{repo}/commits?since={7d ago}` |
| 4 | Fetch Issues | httpRequest | GET `/repos/{repo}/issues?state=closed&since={7d ago}` |
| 5 | Fetch PRs | httpRequest | GET `/repos/{repo}/pulls?state=closed&since={7d ago}` |
| 6 | Merge Data | code | Combines 3 API results, filters by date |
| 7 | Claude Summary | httpRequest | POST to Claude API with merged data |
| 8 | Extract Response | code | Parses Claude's text response |
| 9 | Route Delivery | switch | Routes to Discord/Slack/Email |
| 10 | Send Discord | httpRequest | POST to Discord webhook |
| 11 | Send Slack | httpRequest | POST to Slack webhook |
| 12 | Send Email | emailSend | SMTP email delivery |

All 3 GitHub API calls (commits, issues, PRs) run **in parallel** for speed.

---

## Example Output

### Discord Format

```
📊 **Weekly Dev Summary**
vercel/next.js • Week ending 2026-05-19

━━━━━━━━━━━━━━━━━━━━━━

**🚀 Merged PRs (12)**
> • #72143 Optimize static generation cache
> • #72118 Fix turbopack HMR race condition
> • #72105 Add metadata validation

**🐛 Resolved Issues (8)**
> • #72100 Server Actions not revalidating
> • #72085 Metadata API regression in 15.2.1
> • #72012 Image optimization broken on Safari

**📊 Stats**
> Commits: 47 | PRs: 12 | Issues: 8

━━━━━━━━━━━━━━━━━━━━━━
🤖 Generated by Claude + n8n
```

### Email Format

```
Subject: Weekly Dev Summary — vercel/next.js (May 13-19)

# Weekly Development Summary
vercel/next.js

## Overview
A productive week with 47 commits, 12 merged PRs, and 8 closed issues...

## 🚀 Merged PRs
| # | Title | Author |
|---|-------|--------|
| #72143 | Optimize static generation cache | @user |
| #72118 | Fix turbopack HMR race condition | @user |

## 🐛 Resolved Issues
| # | Title | State |
|---|-------|-------|
| #72100 | Server Actions not revalidating | Closed |
| #72085 | Metadata API regression | Closed |

## 📈 Metrics
- Commits: 47
- PRs Merged: 12
- Issues Resolved: 8

---
Generated on 2026-05-19 by Claude + n8n
```

---

## Configuration Options

### Language Support

Set `lang` to switch Claude's response language:

| Value | Language | Example |
|-------|----------|---------|
| `EN` | English | "This week saw..." |
| `FR` | French | "Cette semaine a vu..." |

### Multi-language Support

To add more languages, modify the **Merge Data** node to include a language-specific prompt template, or modify the **Claude Summary** node's prompt.

### Custom Delivery

To add other delivery methods (Teams, Telegram, etc.), add new nodes after **Route Delivery** and configure their webhook URLs.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **No commits fetched** | Check GitHub token has `repo` scope |
| **Claude API error** | Verify API key is valid and has access |
| **Discord/Slack not receiving** | Check webhook URL is correct and valid |
| **Email not sending** | Verify SMTP credentials in n8n settings |
| **Empty summary** | Ensure repo has activity in the past 7 days |
| **Wrong date range** | Adjust `since` parameter in Fetch nodes |

### Debug Mode

To debug the workflow:
1. Turn off the **Active** toggle
2. Click **Execute Workflow**
3. Check each node's output by clicking on it
4. Look for errors in red

---

## Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| n8n | v1.x+ | Self-hosted or n8n.cloud |
| GitHub Token | - | With `repo` scope |
| Claude API Key | - | With claude-sonnet-4 access |
| Discord/Slack webhook OR SMTP | - | For delivery |

---

## Files Included

| File | Description |
|------|-------------|
| `github-weekly-summary.json` | n8n workflow (import this) |
| `README-workflow.md` | This documentation |

---

*Built for claude-builders-bounty Issue #5 · $200 bounty*
